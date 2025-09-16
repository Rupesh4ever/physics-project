from vpython import *
#Web VPython 3.2
# Paste this into glowscript.org (choose "VPython" mode) and run.

scene = canvas(title="BB84 Quantum Key Distribution Simulation",
               width=1000, height=700, center=vector(0,0,0), background=color.white)

# Permanent labels (always visible)
label(pos=vector(-6,3.5,0), text="Person1 (Sender)", color=color.blue, box=False, height=20)
label(pos=vector(6,3.5,0), text="Person2 (Receiver)", color=color.green, box=False, height=20)
label(pos=vector(0,4.0,0), text="Quantum Channel", color=color.black, box=False, height=16)

# Eavesdropper object (shown only when toggle is checked)
eve_box = box(pos=vector(0,0.5,0), size=vector(0.9,0.9,0.9), color=color.orange, visible=False, opacity=0.4)
eve_label = label(pos=vector(0,1.2,0), text="Eavesdropper", color=color.red, box=False, height=12, visible=False)

# Narration panel (html wtext)
narration = wtext(text="<b>Narration:</b><br>")

# Parameters (you can adjust these)
N = 10                 # number of photons to send
SAMPLE_FRACTION = 0.3  # fraction of sifted key revealed to estimate QBER
DETECTION_THRESHOLD = 0.15  # QBER threshold to declare eavesdropping

# temporary objects (cleared each run)
temp_objects = []

# Helper: toggle handler (checkbox requires bind)
def toggle_eve(cb):
    eve_box.visible = cb.checked
    eve_label.visible = cb.checked

eve_toggle = checkbox(bind=toggle_eve, text=" Enable Eavesdropper", checked=False)
wtext(text="   ")

# Helper functions for randomness and colors (GlowScript uses random())
def randbit():
    return 0 if random() < 0.5 else 1

def randbasis():
    return '+' if random() < 0.5 else 'x'

def photon_color(basis, bit):
    if basis == '+':
        return color.blue if bit == 0 else color.green
    else:
        return color.red if bit == 0 else color.orange

# Clear objects from previous run
def clear_temp():
    global temp_objects
    for o in temp_objects:
        try:
            o.visible = False
        except:
            pass
    temp_objects = []

# The main simulation function
def run_simulation():
    global temp_objects
    clear_temp()
    narration.text = "<b>Narration:</b><br>"

    # --- Step 0: prepare original Person1 bits & bases (preserve originals) ---
    p1_bits_initial = []
    p1_bases_initial = []
    for i in range(N):
        p1_bits_initial.append(randbit())
        p1_bases_initial.append(randbasis())

    # Working copies (may be changed by Eve)
    p1_bits = [p1_bits_initial[i] for i in range(N)]
    p1_bases = [p1_bases_initial[i] for i in range(N)]

    # Person2 bases (chosen independently)
    p2_bases = []
    for i in range(N):
        p2_bases.append(randbasis())

    p2_bits = []

    # track indexes Eve touched
    eve_intercepts = []

    # Animate each photon: Person1 -> Eve (midpoint) -> Person2
    for i in range(N):
        # show what Person1 sent (use initial arrays for this)
        narration.text = narration.text + "Photon " + str(i+1) + ": Person1 sends bit " + str(p1_bits_initial[i]) + " in basis " + p1_bases_initial[i] + ".<br>"

        # create photon at Person1 location
        ph = sphere(pos=vector(-6,0,0), radius=0.24, color=photon_color(p1_bases[i], p1_bits[i]), make_trail=False)
        temp_objects.append(ph)

        # animate travel in 80 steps (0..79)
        for step in range(80):
            rate(60)
            ph.pos.x = -6 + step * (12.0/79.0)   # from -6 to +6 across 80 steps

            # when crossing midpoint (Eve's position)
            if step == 39:
                if eve_toggle.checked:
                    # Eve measures & resends in random basis
                    eve_basis = randbasis()
                    if eve_basis == p1_bases[i]:
                        eve_bit = p1_bits[i]
                    else:
                        eve_bit = randbit()
                    # Eve replaces the state that continues to Person2
                    p1_bits[i] = eve_bit
                    p1_bases[i] = eve_basis

                    # mark interception
                    eve_intercepts.append(i)

                    # change photon color to show the new (post-Eve) state
                    ph.color = photon_color(eve_basis, eve_bit)

                    # show a brief flash & small label at Eve to visualize interception
                    flash = box(pos=vector(0,0.8,0), size=vector(2.4,0.6,0.01), color=color.yellow, opacity=0.5)
                    temp_objects.append(flash)
                    e_lbl = label(pos=vector(0,1.3,0), text="Eve intercepted", color=color.red, box=False, height=10)
                    temp_objects.append(e_lbl)

                    narration.text = narration.text + "Photon " + str(i+1) + ": Eavesdropper intercepted (basis=" + eve_basis + "), resent bit " + str(eve_bit) + ".<br>"
                else:
                    narration.text = narration.text + "Photon " + str(i+1) + ": Passed channel without interception.<br>"

            # when arriving at receiver
            if step == 79:
                if p2_bases[i] == p1_bases[i]:
                    # correct measurement
                    measured = p1_bits[i]
                    p2_bits.append(measured)
                    narration.text = narration.text + "Photon " + str(i+1) + ": Person2 measured " + str(measured) + " (correct, bases matched).<br>"
                else:
                    # random result
                    measured = randbit()
                    p2_bits.append(measured)
                    narration.text = narration.text + "Photon " + str(i+1) + ": Person2 measured " + str(measured) + " (random, bases mismatched).<br>"

        # hide photon after it finished moving
        ph.visible = False

    # --- Sifting: keep only positions where bases matched ---
    sifted_p1 = []
    sifted_p2 = []
    match_positions = []
    for i in range(N):
        if p1_bases[i] == p2_bases[i]:
            sifted_p1.append(p1_bits[i])
            sifted_p2.append(p2_bits[i])
            match_positions.append(i)

    if len(sifted_p1) == 0:
        narration.text = narration.text + "<br><b>No sifted bits (no matching bases).</b><br>"
        return

    # --- Sampling for QBER estimate ---
    sample_size = int(len(sifted_p1) * SAMPLE_FRACTION)
    if sample_size < 1:
        sample_size = 1
    # choose unique random sample indices
    sample_indices = []
    L = len(sifted_p1)
    while len(sample_indices) < sample_size:
        k = int(random() * L)
        if not (k in sample_indices):
            sample_indices.append(k)

    sample_errors = 0
    for idx in sample_indices:
        if sifted_p1[idx] != sifted_p2[idx]:
            sample_errors += 1
    qber = sample_errors / float(sample_size)
    detected = (qber > DETECTION_THRESHOLD)

    # Final key: remove the sample indices (those were revealed for error check)
    final_key_bits = []
    for idx in range(len(sifted_p1)):
        if not (idx in sample_indices):
            final_key_bits.append(sifted_p1[idx])

    # --- Visual table / log below the channel ---
    y0 = 1.2
    spacing = 0.55
    for i in range(N):
        # left: Person1 original bit & basis
        lbl_bit = label(pos=vector(-4, y0 - i*spacing, 0), text=str(p1_bits_initial[i]), box=False, height=12, color=color.blue)
        lbl_basis = label(pos=vector(-5, y0 - i*spacing, 0), text=(p1_bases_initial[i]), box=False, height=12, color=color.gray(0.5))
        temp_objects.append(lbl_bit)
        temp_objects.append(lbl_basis)

        # right: Person2 measured bit & basis
        lbl_bit2 = label(pos=vector(4, y0 - i*spacing, 0), text=str(p2_bits[i]), box=False, height=12, color=color.green)
        lbl_basis2 = label(pos=vector(5, y0 - i*spacing, 0), text=(p2_bases[i]), box=False, height=12, color=color.gray(0.5))
        temp_objects.append(lbl_bit2)
        temp_objects.append(lbl_basis2)

        # mark if Eve intercepted this photon
        if i in eve_intercepts:
            mark = box(pos=vector(0, y0 - i*spacing, 0), size=vector(12,0.45,0.01), color=color.orange, opacity=0.25)
            temp_objects.append(mark)

        # highlight sifted (matching) rows
        if i in match_positions:
            hl = box(pos=vector(0, y0 - i*spacing, -0.01), size=vector(12,0.3,0.01), color=color.cyan, opacity=0.18)
            temp_objects.append(hl)

    # --- Summary appended to narration ---
    narration.text = narration.text + "<br><b>Summary</b><br>"
    narration.text = narration.text + "Sifted bits kept: " + str(len(sifted_p1)) + "<br>"
    narration.text = narration.text + "Sample size (revealed): " + str(sample_size) + "<br>"
    narration.text = narration.text + "Sample errors: " + str(sample_errors) + "<br>"
    narration.text = narration.text + "Estimated QBER: " + str(round(qber,3)) + "<br>"
    narration.text = narration.text + "Eavesdropper detected (threshold " + str(DETECTION_THRESHOLD) + ")? " + ("YES" if detected else "NO") + "<br>"
    narration.text = narration.text + "Eve physically touched " + str(len(eve_intercepts)) + " photon(s).<br>"
    narration.text = narration.text + "Final key (after revealing sample): " + "".join([str(x) for x in final_key_bits]) + "<br>"

# Button handler and button (no lambda)
def on_run_clicked(b):
    run_simulation()

button(text="Run BB84", bind=on_run_clicked)

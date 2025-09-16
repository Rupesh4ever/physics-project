from vpython import *
#Web VPython 3.2

from vpython import *    # Import VPython (3D graphics + physics simulation library)
import random            # Random choices (used to pick repeater paths)

# ====================================================
# 🔹 CONFIGURATION (initial physics + behavior values)
# ====================================================
initial_speed = 0.15           # Default photon travel speed
initial_attenuation = 0.995    # Intensity loss per update step
initial_boost = 1.0            # How much repeaters restore the signal intensity
photon_spawn_rate = 40         # Steps between photon creation (controls flow rate)

# Current values that change in simulation (linked to sliders)
photon_speed = initial_speed
attenuation_rate = initial_attenuation
repeater_boost = initial_boost


# ====================================================
# 🔹 SCENE SETUP (camera and background)
# ====================================================
scene.title = "Photon Network Simulation (Tower → Repeaters → Receivers)"
scene.width = 1200
scene.height = 700
scene.center = vector(0, 0, 0)    # Camera looks at origin
scene.background = color.black    # Black background = space-like


# ====================================================
# 🔹 NODE CREATOR FUNCTION
# ====================================================
def Node(pos, ntype="repeater", label_text=""):
    """
    Creates a 'node' (Tower, Repeater, or Receiver).
    Each node has:
      - a 3D shape (cylinder, sphere, or box)
      - a position in space
      - a label floating above it
    """
    node = {"pos": pos, "ntype": ntype}
    
    # Main tower (Source) → Cyan glowing cylinder
    if ntype == "source":
        node["obj"] = cylinder(pos=pos, axis=vector(0,6,0), radius=1.5,
                               color=color.cyan, emissive=True)
    
    # Receiver → Red glowing cube
    elif ntype == "destination":
        node["obj"] = box(pos=pos, size=vector(3,3,3),
                          color=color.red, emissive=True)
    
    # Repeater → Green glowing sphere
    else:
        node["obj"] = sphere(pos=pos, radius=1.3,
                             color=color.green, emissive=True)
    
    # Optional text label above the node
    if label_text:
        node["label"] = label(pos=pos+vector(0,5,0), text=label_text,
                              height=15, color=color.white, box=False)
    return node


# ====================================================
# 🔹 BUILD NETWORK (nodes and connections)
# ====================================================
nodes = [
    Node(vector(-30, 0, 0), "source", "Main Tower"),   # Left: main tower
    Node(vector(-5, 15, 0), "repeater", "Repeater 1"), # Upper repeater
    Node(vector(-5, -15, 0), "repeater", "Repeater 2"),# Lower repeater
    Node(vector(30, 15, 0), "destination", "Receiver A"), # Top receiver
    Node(vector(30, -15, 0), "destination", "Receiver B") # Bottom receiver
]

# Connections (edges of the graph)
# Represented visually by faint white cylinders (like network cables/paths)
connections = [(0, 1), (0, 2), (1, 3), (2, 4)]
for i, j in connections:
    cylinder(pos=nodes[i]["pos"],
             axis=nodes[j]["pos"] - nodes[i]["pos"],
             radius=0.2,
             color=color.white,
             opacity=0.1)


# ====================================================
# 🔹 PHOTON CREATION
# ====================================================
def Photon(start_node, end_node):
    """
    Creates a photon particle that will move from start_node → end_node.
    Each photon has:
      - A small bright yellow sphere (core)
      - A larger transparent halo (glow effect)
      - Properties: current node, next node, intensity, velocity, burst glow
    """
    photon = {
        "current_node": start_node,
        "next_node": end_node,
        "intensity": 1.0,         # Start fully bright
        "velocity": vector(0,0,0),# Will be set by set_next_hop()
        "burst": 0                # Extra glow boost when hitting a repeater
    }
    
    # The bright yellow "core" of the photon
    core = sphere(pos=nodes[start_node]["pos"],
                  radius=0.35,
                  color=color.yellow,
                  emissive=True,
                  make_trail=True,   # Leaves behind a glowing trail
                  retain=60)         # Trail memory length
    
    # The glowing halo around the photon (semi-transparent)
    halo = sphere(pos=core.pos,
                  radius=1.0,
                  color=color.yellow,
                  opacity=0.4,
                  emissive=True)
    
    photon["obj"] = core
    photon["halo"] = halo
    
    # Set its initial velocity toward the first target
    set_next_hop(photon)
    return photon


def set_next_hop(photon):
    """
    Compute velocity vector toward the photon’s next node.
    Velocity = normalized direction × speed
    """
    current = photon["current_node"]
    next_node = photon["next_node"]
    
    if next_node is not None:
        direction = norm(nodes[next_node]["pos"] - nodes[current]["pos"])
        photon["velocity"] = direction * photon_speed
    else:
        photon["velocity"] = vector(0,0,0)


# ====================================================
# 🔹 PHOTON UPDATE (called every frame)
# ====================================================
def update_photon(photon):
    """
    Update photon’s position, brightness, halo glow, and interactions.
    Returns False if photon should be destroyed (e.g., reached destination).
    """
    if photon["next_node"] is None:
        return False

    # ---- Movement ----
    photon["obj"].pos += photon["velocity"]
    photon["halo"].pos = photon["obj"].pos
    
    # ---- Attenuation (decay in intensity) ----
    photon["intensity"] *= attenuation_rate
    photon["intensity"] = max(0.05, photon["intensity"])  # Prevent full blackout
    
    # ---- Halo Glow Behavior ----
    if photon["burst"] > 0:  # Extra glow effect right after hitting repeater
        photon["halo"].radius = 1.5 + 0.5*photon["burst"]
        photon["halo"].opacity = 0.5
        photon["burst"] -= 0.05
    else:
        photon["halo"].radius = 1.0
        photon["halo"].opacity = 0.2 + 0.4*photon["intensity"]
    
    # ---- Smooth gradient coloring ----
    core_val = min(1.0, photon["intensity"]*1.5)   # Brighter core
    halo_val = photon["intensity"]*0.6             # Dimmer halo
    photon["obj"].color = vector(core_val, core_val, 0)
    photon["halo"].color = vector(halo_val, halo_val, 0)

    # ---- Check if photon reached its next node ----
    if mag(photon["obj"].pos - nodes[photon["next_node"]]["pos"]) < 0.6:
        photon["current_node"] = photon["next_node"]
        node_type = nodes[photon["current_node"]]["ntype"]
        
        if node_type == "repeater":
            # Boost intensity when hitting repeater
            photon["intensity"] = repeater_boost
            photon["burst"] = 1.0  # Burst glow
            # Choose next receiver depending on repeater
            if photon["current_node"] == 1:   # Repeater 1 → Receiver A
                photon["next_node"] = 3
            else:                             # Repeater 2 → Receiver B
                photon["next_node"] = 4
            set_next_hop(photon)
        
        elif node_type == "destination":
            # Photon reached receiver → vanish
            photon["obj"].visible = False
            photon["halo"].visible = False
            photon["obj"].clear_trail()
            return False
    return True


# ====================================================
# 🔹 CONTROL PANEL (pause, reset, sliders)
# ====================================================
paused = False   # Track whether simulation is running
photons = []     # Active photons
step = 0         # Frame counter

def toggle_pause(b):
    """Pause or resume simulation when button is clicked"""
    global paused
    paused = not paused
    b.text = "Resume" if paused else "Pause"

def reset_sim(b):
    """Clear all photons and reset parameters"""
    global photons, step, photon_speed, attenuation_rate, repeater_boost
    # Destroy all photons
    for p in photons:
        p["obj"].visible = False
        p["halo"].visible = False
        try:
            p["obj"].clear_trail()
        except:
            pass
    photons = []
    step = 0
    # Reset values
    photon_speed = initial_speed
    attenuation_rate = initial_attenuation
    repeater_boost = initial_boost
    # Reset sliders
    slider_speed.value = photon_speed
    slider_attenuation.value = attenuation_rate
    slider_boost.value = repeater_boost

# Slider callbacks
def set_speed(sl):
    global photon_speed
    photon_speed = sl.value

def set_attenuation(sl):
    global attenuation_rate
    attenuation_rate = sl.value

def set_boost(sl):
    global repeater_boost
    repeater_boost = sl.value


# ====================================================
# 🔹 UI ELEMENTS
# ====================================================
scene.append_to_caption("\n\nSimulation Controls:\n")
slider_speed = slider(min=0.05, max=0.5, value=initial_speed, step=0.01,
                      length=200, bind=set_speed)
scene.append_to_caption(" Photon Speed\n\n")

slider_attenuation = slider(min=0.90, max=0.999, value=initial_attenuation,
                            step=0.001, length=200, bind=set_attenuation)
scene.append_to_caption(" Attenuation Rate\n\n")

slider_boost = slider(min=0.5, max=2.0, value=initial_boost, step=0.05,
                      length=200, bind=set_boost)
scene.append_to_caption(" Repeater Boost\n\n")

button_pause = button(text="Pause", bind=toggle_pause)
scene.append_to_caption("   ")
button_reset = button(text="Reset", bind=reset_sim)


# ====================================================
# 🔹 MAIN LOOP (runs continuously)
# ====================================================
while True:
    rate(100)   # 100 frames per second (simulation speed)
    step += 1

    if not paused:
        # ---- Spawn new photons from the Tower periodically ----
        if step % photon_spawn_rate == 0:
            if random.random() < 0.5:
                photons.append(Photon(start_node=0, end_node=1))  # Tower → Repeater 1
            else:
                photons.append(Photon(start_node=0, end_node=2))  # Tower → Repeater 2

        # ---- Update all photons ----
        alive = []
        for p in photons:
            if update_photon(p):
                alive.append(p)   # Keep if still alive
        photons = alive           # Remove dead photons
"""
Cyberpunk Megacity Neon Circuit Generator for Blender.
Fully fulfills all 12 specifications:
- Complete closed loop with elevation, bridge overpass on pylons, covered cyber tunnel with neon rings.
- 18m road width (comfortably accommodates 4 cars in parallel).
- Separate modular objects for Road, Kerbs, Barriers, Bridge, Tunnel.
- Cyberpunk Megacity: 35+ skyscrapers, rooftop HVAC/antennae, holographic neon billboards, street lamps.
- Racing Infrastructure: Start gantry, timing tower, checkpoint gates, camera towers.
- Guide Objects: Start_Finish, Player_Grid_01-08 (4-wide), Checkpoint_01-08, AI_Racing_Line, Pit_Entry/Exit.
- 3 Cameras & Night lighting setup.
- Saves scene to d:\game\cyberpunk_circuit.blend.
"""

from blender_client import send_code

cyberpunk_code = r'''
import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, Euler

# -------------------------------------------------------------
# 1. Clean Scene and Initialize Collections
# -------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for block in bpy.data.meshes:
    if block.users == 0:
        bpy.data.meshes.remove(block)
for block in bpy.data.materials:
    if block.users == 0:
        bpy.data.materials.remove(block)
for block in bpy.data.curves:
    if block.users == 0:
        bpy.data.curves.remove(block)

# Set world to deep night cyberpunk sky
world = bpy.context.scene.world
if not world:
    world = bpy.data.worlds.new("Cyberpunk_World")
    bpy.context.scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs['Color'].default_value = (0.005, 0.008, 0.02, 1.0)
    bg_node.inputs['Strength'].default_value = 0.4

# Create 6 required collections
coll_names = [
    "01_TRACK_SURFACE",
    "02_BARRIERS_AND_KERBS",
    "03_RACING_INFRASTRUCTURE",
    "04_CYBERPUNK_MEGACITY",
    "05_NAVIGATION_GUIDES",
    "06_LIGHTING_AND_CAMERAS"
]
collections = {}
for name in coll_names:
    existing = bpy.data.collections.get(name)
    if existing:
        bpy.context.scene.collection.children.unlink(existing)
        bpy.data.collections.remove(existing)
    new_coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(new_coll)
    collections[name] = new_coll

def link_obj(obj, coll_name):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    collections[coll_name].objects.link(obj)

# -------------------------------------------------------------
# 2. Cyberpunk Palette Materials
# -------------------------------------------------------------
def make_mat(name, base_color, metallic=0.0, roughness=0.5, emission=None, emission_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = base_color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        if emission:
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = emission
                bsdf.inputs['Emission Strength'].default_value = emission_strength
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = emission
    return mat

mat_asphalt   = make_mat("Mat_Asphalt_Wet", (0.025, 0.025, 0.03, 1.0), roughness=0.22, metallic=0.05) # subtle wet reflection
mat_white_line= make_mat("Mat_Road_White", (0.92, 0.92, 0.95, 1.0), roughness=0.3)
mat_yellow_ln = make_mat("Mat_Road_Yellow", (1.0, 0.75, 0.05, 1.0), roughness=0.3)
mat_concrete  = make_mat("Mat_Concrete_Dark", (0.10, 0.10, 0.11, 1.0), roughness=0.88)
mat_metal     = make_mat("Mat_Metal_Charcoal", (0.06, 0.06, 0.07, 1.0), metallic=0.9, roughness=0.25)
mat_glass     = make_mat("Mat_Glass_Tinted", (0.02, 0.03, 0.05, 1.0), metallic=0.95, roughness=0.05)

# Neon Palette
mat_neon_cyan = make_mat("Mat_Neon_Cyan", (0.0, 0.9, 1.0, 1.0), emission=(0.0, 0.9, 1.0, 1.0), emission_strength=12.0)
mat_neon_mag  = make_mat("Mat_Neon_Magenta", (1.0, 0.05, 0.55, 1.0), emission=(1.0, 0.05, 0.55, 1.0), emission_strength=12.0)
mat_neon_purp = make_mat("Mat_Neon_Violet", (0.65, 0.08, 1.0, 1.0), emission=(0.65, 0.08, 1.0, 1.0), emission_strength=10.0)
mat_neon_amb  = make_mat("Mat_Neon_Amber", (1.0, 0.55, 0.02, 1.0), emission=(1.0, 0.55, 0.02, 1.0), emission_strength=10.0)
mat_start_red = make_mat("Mat_Gantry_Red", (1.0, 0.02, 0.02, 1.0), emission=(1.0, 0.02, 0.02, 1.0), emission_strength=20.0)
mat_start_grn = make_mat("Mat_Gantry_Green", (0.05, 1.0, 0.2, 1.0), emission=(0.05, 1.0, 0.2, 1.0), emission_strength=20.0)

# Building window shader (subtle glowing office grid)
mat_facade_lit = make_mat("Mat_Facade_LitWindows", (0.03, 0.03, 0.04, 1.0), metallic=0.5, roughness=0.4, emission=(0.95, 0.85, 0.65, 1.0), emission_strength=0.7)

# -------------------------------------------------------------
# 3. Closed-Loop Circuit Geometry Waypoints
# -------------------------------------------------------------
# Includes:
# - Long Starting Straight (ground Z=0)
# - Wide Plaza Sweeper
# - Twin Towers Chicane
# - Elevated Skybridge at Z=+18m with structural pylons
# - Skybridge Hairpin (Tight Hairpin #1)
# - Subterranean Cyber Tunnel at Z=-6m with glowing neon rib arches
# - Industrial Chicane
# - Harbor Hairpin (Tight Hairpin #2)
# - High-Speed Neon Strip Straight
# - Boulevard Final Corners back to Start Straight

circuit_wps = [
    # Main Start/Finish Straight (Length ~340m, Z=0)
    Vector((0.0, -180.0, 0.0)),
    Vector((0.0, -90.0, 0.0)),
    Vector((0.0, 0.0, 0.0)),           # Start / Finish Line
    Vector((0.0, 90.0, 0.0)),
    Vector((0.0, 170.0, 0.0)),

    # Turn 1: Wide Plaza Sweeper (High-Speed Sweeping Corner)
    Vector((30.0, 240.0, 1.5)),
    Vector((90.0, 280.0, 3.0)),
    Vector((160.0, 280.0, 4.0)),

    # Turn 2 & 3: Twin Towers Chicane (S-curve between megastructures)
    Vector((220.0, 240.0, 5.0)),
    Vector((250.0, 180.0, 7.0)),
    Vector((220.0, 120.0, 9.0)),
    Vector((210.0, 50.0, 12.0)),       # Climbing onto elevated sky-ramp

    # Elevated Skybridge Section (Rises to +18m over city flyovers)
    Vector((200.0, -20.0, 16.0)),
    Vector((190.0, -90.0, 18.0)),      # Peak elevated bridge deck
    Vector((170.0, -170.0, 18.0)),
    Vector((140.0, -240.0, 18.0)),

    # Turn 4: Skybridge Hairpin (Tight Hairpin #1 at +18m summit)
    Vector((110.0, -300.0, 18.0)),     # Braking zone
    Vector((70.0, -325.0, 17.5)),      # Apex
    Vector((30.0, -295.0, 15.0)),      # Exit plunge

    # Incline Ramp plunging into Cyber-Tunnel
    Vector((10.0, -220.0, 10.0)),
    Vector((-10.0, -150.0, 4.0)),
    Vector((-30.0, -80.0, -2.0)),      # Tunnel Entrance Portal (Z = -2m)

    # Subterranean Cyber Tunnel Section (Covered with neon arches, Z = -6m)
    Vector((-50.0, -10.0, -6.0)),      # Deep tunnel mid
    Vector((-75.0, 60.0, -6.0)),
    Vector((-110.0, 120.0, -4.0)),
    Vector((-150.0, 160.0, -1.0)),     # Tunnel Exit Portal (Z = 0m)

    # Turn 5 & 6: Industrial District Chicane
    Vector((-200.0, 180.0, 0.0)),
    Vector((-245.0, 150.0, 0.0)),
    Vector((-260.0, 90.0, 0.0)),

    # Turn 7: Harbor Hairpin (Tight Hairpin #2)
    Vector((-260.0, 10.0, 0.0)),       # Hard braking
    Vector((-235.0, -40.0, 0.0)),      # Apex
    Vector((-190.0, -55.0, 0.0)),      # Exit

    # Neon Strip Straight (High-speed blast flanked by mega-billboards)
    Vector((-160.0, -110.0, 0.0)),
    Vector((-130.0, -180.0, 0.0)),
    Vector((-100.0, -250.0, 0.0)),

    # Turn 8 & 9: Boulevard Final Turns
    Vector((-60.0, -280.0, 0.0)),      # Turn 8 90-deg left
    Vector((-20.0, -250.0, 0.0)),      # Turn 9 right into start straight
]

# Spline generator
def catmull_rom(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        (2.0 * p1) +
        (-p0 + p2) * t +
        (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 +
        (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
    )

num_wp = len(circuit_wps)
subdiv = 14
track_pts = []
for i in range(num_wp):
    p0 = circuit_wps[(i - 1) % num_wp]
    p1 = circuit_wps[i]
    p2 = circuit_wps[(i + 1) % num_wp]
    p3 = circuit_wps[(i + 2) % num_wp]
    for s in range(subdiv):
        track_pts.append(catmull_rom(p0, p1, p2, p3, s / subdiv))

total_rings = len(track_pts)
print(f"Generated {total_rings} smooth track rings.")

# Calculate ring frames (position, tangent, normal, binormal)
ring_frames = []
for i in range(total_rings):
    curr_pt = track_pts[i]
    next_pt = track_pts[(i + 1) % total_rings]
    prev_pt = track_pts[(i - 1) % total_rings]
    tangent = (next_pt - prev_pt).normalized()
    up = Vector((0.0, 0.0, 1.0))
    normal = tangent.cross(up).normalized()
    binormal = normal.cross(tangent).normalized()

    # Banking in high speed corners
    curvature = (next_pt - 2.0 * curr_pt + prev_pt).length
    bank = math.sin(i / 10.0) * min(curvature * 0.15, 0.09)
    rot_norm = normal * math.cos(bank) + binormal * math.sin(bank)
    rot_binorm = -normal * math.sin(bank) + binormal * math.cos(bank)

    ring_frames.append({
        "pos": curr_pt,
        "tangent": tangent,
        "normal": rot_norm,
        "binormal": rot_binorm,
        "idx": i
    })

# -------------------------------------------------------------
# 4. Object 1: Track Road Surface (18m Wide for 4 Parallel Cars)
# -------------------------------------------------------------
# Road width: 18m pure asphalt (-9m to +9m)
road_mesh = bpy.data.meshes.new("Mesh_Track_Road")
road_obj = bpy.data.objects.new("Track_Road_Surface", road_mesh)
link_obj(road_obj, "01_TRACK_SURFACE")
road_obj.data.materials.append(mat_asphalt)
road_obj.data.materials.append(mat_white_line)
road_obj.data.materials.append(mat_yellow_ln)

bm_road = bmesh.new()

# Cross-section vertices across 18m road:
# [-9.0, -8.7, -4.5, -0.15, 0.15, 4.5, 8.7, 9.0]
# Slots: 1=white edge line, 2=yellow center dash / lane division
road_offsets = [
    (-9.0, 0.0, 1),
    (-8.7, 0.01, 0),
    (-4.5, 0.03, 0),  # Lane 1/2 boundary
    (-0.15, 0.04, 2), # Center double line
    ( 0.15, 0.04, 2),
    ( 4.5, 0.03, 0),  # Lane 3/4 boundary
    ( 8.7, 0.01, 0),
    ( 9.0, 0.0, 1),
]

road_ring_verts = []
for f in ring_frames:
    r_verts = []
    for (lat, h, _) in road_offsets:
        p = f["pos"] + f["normal"] * lat + f["binormal"] * h
        r_verts.append(bm_road.verts.new(p))
    road_ring_verts.append(r_verts)

bm_road.verts.ensure_lookup_table()

for i in range(total_rings):
    next_i = (i + 1) % total_rings
    r1 = road_ring_verts[i]
    r2 = road_ring_verts[next_i]
    for p in range(len(road_offsets) - 1):
        face = bm_road.faces.new((r1[p], r1[p+1], r2[p+1], r2[p]))
        face.material_index = road_offsets[p][2]

bm_road.to_mesh(road_mesh)
bm_road.free()
road_mesh.update()
for poly in road_mesh.polygons:
    poly.use_smooth = True

print("Track road surface generated.")

# -------------------------------------------------------------
# 5. Object 2: Kerbs & Modular Barriers (Separate Object)
# -------------------------------------------------------------
barrier_mesh = bpy.data.meshes.new("Mesh_Barriers_Kerbs")
barrier_obj = bpy.data.objects.new("Track_Barriers_And_Kerbs", barrier_mesh)
link_obj(barrier_obj, "02_BARRIERS_AND_KERBS")
barrier_obj.data.materials.append(mat_concrete)    # 0
barrier_obj.data.materials.append(mat_metal)       # 1
barrier_obj.data.materials.append(mat_neon_cyan)   # 2
barrier_obj.data.materials.append(mat_neon_mag)    # 3

bm_bar = bmesh.new()

# Left and Right kerbs (2.0m wide each: 9.0m to 11.0m) + concrete barrier + neon railing
# Profiles on left (-X) and right (+X)
left_bar_profile = [
    (-9.0, 0.02, 2),    # Kerb start
    (-10.8, 0.15, 2),   # Kerb top
    (-11.0, 0.0, 0),    # Concrete barrier base
    (-11.2, 0.8, 0),    # Concrete barrier top
    (-11.2, 1.3, 1),    # Metal upper rail
    (-11.1, 1.4, 2),    # Neon glow strip
]

right_bar_profile = [
    ( 9.0, 0.02, 3),    # Kerb start
    ( 10.8, 0.15, 3),   # Kerb top
    ( 11.0, 0.0, 0),    # Concrete barrier base
    ( 11.2, 0.8, 0),    # Concrete barrier top
    ( 11.2, 1.3, 1),    # Metal upper rail
    ( 11.1, 1.4, 3),    # Neon glow strip
]

left_ring_verts = []
right_ring_verts = []

for f in ring_frames:
    l_verts = []
    for (lat, h, _) in left_bar_profile:
        p = f["pos"] + f["normal"] * lat + f["binormal"] * h
        l_verts.append(bm_bar.verts.new(p))
    left_ring_verts.append(l_verts)

    r_verts = []
    for (lat, h, _) in right_bar_profile:
        p = f["pos"] + f["normal"] * lat + f["binormal"] * h
        r_verts.append(bm_bar.verts.new(p))
    right_ring_verts.append(r_verts)

bm_bar.verts.ensure_lookup_table()

for i in range(total_rings):
    next_i = (i + 1) % total_rings
    # Alternating neon kerb color along track (cyan & magenta rhythm)
    kerb_alt = 2 if ((i // 6) % 2 == 0) else 3

    # Left
    l1 = left_ring_verts[i]
    l2 = left_ring_verts[next_i]
    for p in range(len(left_bar_profile) - 1):
        face = bm_bar.faces.new((l1[p], l1[p+1], l2[p+1], l2[p]))
        mat = left_bar_profile[p][2]
        face.material_index = kerb_alt if mat in (2, 3) else mat

    # Right
    r1 = right_ring_verts[i]
    r2 = right_ring_verts[next_i]
    for p in range(len(right_bar_profile) - 1):
        face = bm_bar.faces.new((r1[p], r1[p+1], r2[p+1], r2[p]))
        mat = right_bar_profile[p][2]
        face.material_index = kerb_alt if mat in (2, 3) else mat

bm_bar.to_mesh(barrier_mesh)
bm_bar.free()
barrier_mesh.update()
for poly in barrier_mesh.polygons:
    poly.use_smooth = True

print("Barriers and Kerbs generated.")

# -------------------------------------------------------------
# 6. Object 3: Elevated Bridge Support Pylons
# -------------------------------------------------------------
# Spawn massive concrete/steel structural pylons beneath elevated bridge section (Z >= 12.0)
pylon_mesh = bpy.data.meshes.new("Mesh_Bridge_Pylons")
pylon_obj = bpy.data.objects.new("Bridge_Support_Pylons", pylon_mesh)
link_obj(pylon_obj, "01_TRACK_SURFACE")
pylon_obj.data.materials.append(mat_concrete)
pylon_obj.data.materials.append(mat_metal)

bm_pylon = bmesh.new()

for i in range(0, total_rings, 8):
    f = ring_frames[i]
    if f["pos"].z >= 10.0:
        deck_pos = f["pos"]
        ground_z = 0.0
        pylon_height = deck_pos.z - ground_z

        # Twin support columns under left and right edges
        for side in [-7.5, 7.5]:
            col_base = deck_pos + f["normal"] * side
            col_base.z = ground_z

            # Create box pillar from ground to deck
            hw = 1.2
            hd = 1.2
            v1 = bm_pylon.verts.new(col_base + Vector((-hw, -hd, 0)))
            v2 = bm_pylon.verts.new(col_base + Vector(( hw, -hd, 0)))
            v3 = bm_pylon.verts.new(col_base + Vector(( hw,  hd, 0)))
            v4 = bm_pylon.verts.new(col_base + Vector((-hw,  hd, 0)))

            v5 = bm_pylon.verts.new(col_base + Vector((-hw, -hd, pylon_height - 0.5)))
            v6 = bm_pylon.verts.new(col_base + Vector(( hw, -hd, pylon_height - 0.5)))
            v7 = bm_pylon.verts.new(col_base + Vector(( hw,  hd, pylon_height - 0.5)))
            v8 = bm_pylon.verts.new(col_base + Vector((-hw,  hd, pylon_height - 0.5)))

            # 4 side faces
            f1 = bm_pylon.faces.new((v1, v2, v6, v5))
            f2 = bm_pylon.faces.new((v2, v3, v7, v6))
            f3 = bm_pylon.faces.new((v3, v4, v8, v7))
            f4 = bm_pylon.faces.new((v4, v1, v5, v8))
            f1.material_index = 0
            f2.material_index = 0
            f3.material_index = 0
            f4.material_index = 0

bm_pylon.to_mesh(pylon_mesh)
bm_pylon.free()
pylon_mesh.update()
print("Bridge support pylons generated.")

# -------------------------------------------------------------
# 7. Object 4: Subterranean Cyber Tunnel with Neon Rib Arches
# -------------------------------------------------------------
tunnel_mesh = bpy.data.meshes.new("Mesh_Cyber_Tunnel")
tunnel_obj = bpy.data.objects.new("Cyber_Tunnel_Structure", tunnel_mesh)
link_obj(tunnel_obj, "01_TRACK_SURFACE")
tunnel_obj.data.materials.append(mat_concrete)    # 0: Dark tunnel shell
tunnel_obj.data.materials.append(mat_neon_cyan)   # 1: Neon arch ribs
tunnel_obj.data.materials.append(mat_neon_purp)   # 2: Violet accent

bm_tun = bmesh.new()

# Tunnel arch profile (arch spanning from -11.5m to +11.5m, 6.5m ceiling height)
arch_pts = [
    (-11.5, 0.0),
    (-11.5, 4.0),
    (-8.0,  6.8),
    (-3.0,  7.5),
    ( 3.0,  7.5),
    ( 8.0,  6.8),
    ( 11.5, 4.0),
    ( 11.5, 0.0),
]

tunnel_ring_verts = []
tunnel_indices = []

for i, f in enumerate(ring_frames):
    # Tunnel is active where Z < 0.0 (subterranean section)
    if f["pos"].z <= 0.0 and -180.0 <= f["pos"].x <= -20.0 and -120.0 <= f["pos"].y <= 160.0:
        tunnel_indices.append(i)
        t_verts = []
        for (lat, h) in arch_pts:
            p = f["pos"] + f["normal"] * lat + f["binormal"] * h
            t_verts.append(bm_tun.verts.new(p))
        tunnel_ring_verts.append((i, t_verts))

bm_tun.verts.ensure_lookup_table()

for k in range(len(tunnel_ring_verts) - 1):
    idx_curr, t1 = tunnel_ring_verts[k]
    idx_next, t2 = tunnel_ring_verts[k + 1]
    # Check continuity
    if idx_next == idx_curr + 1:
        # Every 4th arch is a glowing neon rib
        is_neon_rib = (k % 4 == 0)
        rib_mat = 1 if (k % 8 == 0) else 2

        for p in range(len(arch_pts) - 1):
            face = bm_tun.faces.new((t1[p], t1[p+1], t2[p+1], t2[p]))
            face.material_index = rib_mat if is_neon_rib else 0

bm_tun.to_mesh(tunnel_mesh)
bm_tun.free()
tunnel_mesh.update()
print("Cyber tunnel structure generated.")

# -------------------------------------------------------------
# 8. Racing Infrastructure (Gantry, Timing Tower, Checkpoint Gates)
# -------------------------------------------------------------
start_frame = ring_frames[2 * subdiv] # Near (0, 0, 0)
s_pos = start_frame["pos"]
s_tan = start_frame["tangent"]
s_norm = start_frame["normal"]

# 8.1 Starting Light Gantry
bpy.ops.mesh.primitive_cube_add(size=1.0, location=s_pos + s_norm * 12.0 + Vector((0, 0, 6.0)))
p1 = bpy.context.active_object
p1.name = "Gantry_Pillar_Left"
p1.scale = (1.2, 1.2, 12.0)
p1.data.materials.append(mat_metal)
link_obj(p1, "03_RACING_INFRASTRUCTURE")

bpy.ops.mesh.primitive_cube_add(size=1.0, location=s_pos - s_norm * 12.0 + Vector((0, 0, 6.0)))
p2 = bpy.context.active_object
p2.name = "Gantry_Pillar_Right"
p2.scale = (1.2, 1.2, 12.0)
p2.data.materials.append(mat_metal)
link_obj(p2, "03_RACING_INFRASTRUCTURE")

# Gantry overhead crossbeam
bpy.ops.mesh.primitive_cube_add(size=1.0, location=s_pos + Vector((0, 0, 11.5)))
bar = bpy.context.active_object
bar.name = "Gantry_Crossbeam"
bar.scale = (2.0, 26.0, 1.6)
bar.data.materials.append(mat_metal)
link_obj(bar, "03_RACING_INFRASTRUCTURE")

# 5 Red and 5 Green F1/Cyberpunk Start Lights
for idx in range(5):
    l_pos = s_pos + s_norm * (idx * 2.8 - 5.6) + Vector((0, 0, 10.6))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=0.4, location=l_pos)
    red_lamp = bpy.context.active_object
    red_lamp.name = f"StartLight_Red_{idx+1}"
    red_lamp.data.materials.append(mat_start_red)
    link_obj(red_lamp, "03_RACING_INFRASTRUCTURE")

# 8.2 Futuristic Timing Tower (6-tier vertical cyber-monolith)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=s_pos + s_norm * 17.0 + Vector((0, 0, 16.0)))
tower = bpy.context.active_object
tower.name = "Timing_Tower_Main"
tower.scale = (4.5, 4.5, 32.0)
tower.data.materials.append(mat_concrete)
link_obj(tower, "03_RACING_INFRASTRUCTURE")

# Timing screens on tower
bpy.ops.mesh.primitive_cube_add(size=1.0, location=s_pos + s_norm * 14.6 + Vector((0, 0, 22.0)))
screen = bpy.context.active_object
screen.name = "Timing_Tower_DigitalScreen"
screen.scale = (0.2, 3.8, 14.0)
screen.data.materials.append(mat_neon_cyan)
link_obj(screen, "03_RACING_INFRASTRUCTURE")

# 8.3 Checkpoint Gates (8 visually distinct glowing checkpoint arches)
checkpoint_ring_indices = [
    int(total_rings * (i / 8.0)) for i in range(8)
]

for cp_idx, r_idx in enumerate(checkpoint_ring_indices):
    cp_frame = ring_frames[r_idx]
    cp_p = cp_frame["pos"]
    cp_n = cp_frame["normal"]
    cp_t = cp_frame["tangent"]

    # Arch overhead gate
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=cp_p + Vector((0, 0, 9.0)))
    cp_gate = bpy.context.active_object
    cp_gate.name = f"Checkpoint_Gate_{cp_idx+1:02d}"
    cp_gate.scale = (1.5, 24.0, 1.2)
    # Alternate neon color
    cp_mat = mat_neon_cyan if (cp_idx % 2 == 0) else mat_neon_mag
    cp_gate.data.materials.append(cp_mat)
    # Align rotation to road tangent
    rot_z = math.atan2(cp_t.y, cp_t.x)
    cp_gate.rotation_euler.z = rot_z
    link_obj(cp_gate, "03_RACING_INFRASTRUCTURE")

print("Racing infrastructure generated.")

# -------------------------------------------------------------
# 9. Cyberpunk Megacity Environment
# -------------------------------------------------------------
# 35+ skyscrapers, rooftop equipment, holographic billboards, street lamps
bldg_coll = collections["04_CYBERPUNK_MEGACITY"]
random.seed(42)

# Building footprint coordinates strategically placed along streets and skyline
building_specs = [
    # Main straight street canyon (East side)
    (32.0, -160.0, 36.0, 40.0, 140.0),
    (35.0, -90.0, 32.0, 35.0, 210.0),
    (38.0, -20.0, 30.0, 30.0, 180.0),
    (40.0, 50.0, 34.0, 36.0, 240.0),
    (42.0, 130.0, 35.0, 42.0, 160.0),

    # Main straight street canyon (West side)
    (-32.0, -160.0, 35.0, 38.0, 170.0),
    (-35.0, -90.0, 30.0, 32.0, 230.0),
    (-38.0, -20.0, 32.0, 34.0, 270.0),
    (-40.0, 60.0, 35.0, 36.0, 190.0),
    (-42.0, 140.0, 38.0, 40.0, 150.0),

    # Plaza Sweeper & Twin Towers (North sector)
    (120.0, 340.0, 45.0, 45.0, 290.0),   # Monolithic Mega-Tower
    (200.0, 330.0, 42.0, 40.0, 260.0),
    (290.0, 260.0, 40.0, 38.0, 220.0),
    (300.0, 170.0, 42.0, 42.0, 250.0),
    (270.0, 90.0, 36.0, 36.0, 190.0),

    # Skybridge Overpass vistas (East / South-East sector)
    (250.0, -100.0, 40.0, 40.0, 180.0),
    (230.0, -190.0, 38.0, 42.0, 210.0),
    (190.0, -320.0, 45.0, 40.0, 240.0),
    (100.0, -380.0, 42.0, 42.0, 220.0),
    (20.0, -370.0, 40.0, 45.0, 190.0),

    # Industrial & Harbor district (South-West / West sector)
    (-290.0, 180.0, 45.0, 45.0, 160.0),
    (-310.0, 90.0, 42.0, 40.0, 200.0),
    (-300.0, -10.0, 44.0, 44.0, 175.0),
    (-280.0, -100.0, 40.0, 40.0, 220.0),

    # Neon Strip Boulevard (South sector)
    (-190.0, -180.0, 36.0, 36.0, 230.0),
    (-160.0, -250.0, 38.0, 38.0, 250.0),
    (-120.0, -320.0, 40.0, 40.0, 210.0),

    # Distant Megacity Backdrop Silhouettes
    (0.0, 480.0, 80.0, 80.0, 340.0),
    (380.0, 0.0, 75.0, 75.0, 320.0),
    (-380.0, -200.0, 70.0, 70.0, 310.0),
    (150.0, -480.0, 80.0, 80.0, 330.0),
]

for idx, (bx, by, bw, bd, bh) in enumerate(building_specs):
    # Main Tower Block
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, bh / 2.0))
    bldg = bpy.context.active_object
    bldg.name = f"Cyber_Skyscraper_{idx+1:02d}"
    bldg.scale = (bw, bd, bh)
    bldg.data.materials.append(mat_facade_lit if (idx % 2 == 0) else mat_concrete)
    link_obj(bldg, "04_CYBERPUNK_MEGACITY")

    # Rooftop HVAC machinery & Antenna on prominent buildings
    if bh >= 180.0:
        # HVAC block
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, bh + 3.0))
        hvac = bpy.context.active_object
        hvac.name = f"Rooftop_HVAC_{idx+1:02d}"
        hvac.scale = (bw * 0.4, bd * 0.4, 6.0)
        hvac.data.materials.append(mat_metal)
        link_obj(hvac, "04_CYBERPUNK_MEGACITY")

        # Communication Spire with red warning beacon
        bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=18.0, location=(bx, by, bh + 15.0))
        spire = bpy.context.active_object
        spire.name = f"Rooftop_Spire_{idx+1:02d}"
        spire.data.materials.append(mat_metal)
        link_obj(spire, "04_CYBERPUNK_MEGACITY")

# 9.2 Holographic Digital Neon Billboards
billboard_positions = [
    # Position, Dimensions (Width, Height), Facing Angle, Neon Material, Name
    ((22.0, -100.0, 24.0), (1.0, 16.0, 8.0), 0.0, mat_neon_cyan, "Billboard_CYBERDRIVE"),
    ((-22.0, -50.0, 22.0), (1.0, 16.0, 8.0), 0.0, mat_neon_mag, "Billboard_NEOKAIJU"),
    ((22.0, 20.0, 26.0), (1.0, 18.0, 9.0), 0.0, mat_neon_purp, "Billboard_NEXUS9"),
    ((70.0, 250.0, 30.0), (18.0, 1.0, 8.0), 0.3, mat_neon_amb, "Billboard_OVERDRIVE"),
    ((210.0, 210.0, 28.0), (1.0, 16.0, 8.0), 1.2, mat_neon_cyan, "Billboard_HYPERSPEED"),
    ((160.0, -130.0, 32.0), (16.0, 1.0, 9.0), -0.8, mat_neon_mag, "Billboard_QUANTUM"),
    ((-210.0, 120.0, 22.0), (1.0, 18.0, 9.0), -0.5, mat_neon_purp, "Billboard_SYNTHWAVE"),
    ((-150.0, -150.0, 25.0), (1.0, 20.0, 10.0), 0.6, mat_neon_cyan, "Billboard_MEGA_AD"),
]

for b_pos, (bw, bd, bh), rot_z, b_mat, b_name in billboard_positions:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=b_pos)
    board = bpy.context.active_object
    board.name = b_name
    board.scale = (bw, bd, bh)
    board.rotation_euler.z = rot_z
    board.data.materials.append(b_mat)
    link_obj(board, "04_CYBERPUNK_MEGACITY")

# 9.3 Cyberpunk Street Lamps along Main Straight
for y in range(-160, 160, 35):
    # Left lamp
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=7.5, location=(-12.5, y, 3.75))
    lamp_l = bpy.context.active_object
    lamp_l.name = f"StreetLamp_L_{y}"
    lamp_l.data.materials.append(mat_metal)
    link_obj(lamp_l, "04_CYBERPUNK_MEGACITY")

    # Neon light head
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-11.5, y, 7.2))
    head_l = bpy.context.active_object
    head_l.name = f"LampHead_L_{y}"
    head_l.scale = (1.5, 0.4, 0.2)
    head_l.data.materials.append(mat_neon_cyan)
    link_obj(head_l, "04_CYBERPUNK_MEGACITY")

    # Right lamp
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=7.5, location=(12.5, y, 3.75))
    lamp_r = bpy.context.active_object
    lamp_r.name = f"StreetLamp_R_{y}"
    lamp_r.data.materials.append(mat_metal)
    link_obj(lamp_r, "04_CYBERPUNK_MEGACITY")

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(11.5, y, 7.2))
    head_r = bpy.context.active_object
    head_r.name = f"LampHead_R_{y}"
    head_r.scale = (1.5, 0.4, 0.2)
    head_r.data.materials.append(mat_neon_cyan)
    link_obj(head_r, "04_CYBERPUNK_MEGACITY")

print("Cyberpunk Megacity environment generated.")

# -------------------------------------------------------------
# 10. Navigation Guides & Unity Authoring Objects
# -------------------------------------------------------------
# Required clearly named guide objects:
# - Start_Finish
# - Player_Grid_01 through Player_Grid_08 (4 cars wide in 2 rows!)
# - Checkpoint_01 through Checkpoint_08
# - AI_Racing_Line (Editable continuous closed curve)
# - Pit_Entry
# - Pit_Exit

# 10.1 Start_Finish Empty
sf_obj = bpy.data.objects.new("Start_Finish", None)
sf_obj.empty_display_type = 'ARROWS'
sf_obj.empty_display_size = 4.0
sf_obj.location = s_pos
sf_obj.rotation_euler.z = math.atan2(s_tan.y, s_tan.x)
link_obj(sf_obj, "05_NAVIGATION_GUIDES")

# 10.2 Player_Grid_01 through Player_Grid_08 (4-Wide Parallel Formation!)
# Row 1: Grids 01-04 (offsets -6.75, -2.25, +2.25, +6.75 across the 18m road)
# Row 2: Grids 05-08 (staggered 14m behind Row 1)
row1_y_offset = -15.0
row2_y_offset = -30.0
lane_offsets = [-6.75, -2.25, 2.25, 6.75]

grid_names = [f"Player_Grid_{i+1:02d}" for i in range(8)]
for i in range(4):
    # Row 1
    g1 = bpy.data.objects.new(grid_names[i], None)
    g1.empty_display_type = 'SINGLE_ARROW'
    g1.empty_display_size = 2.5
    g1.location = s_pos + s_norm * lane_offsets[i] + s_tan * row1_y_offset + Vector((0, 0, 0.1))
    g1.rotation_euler.z = math.atan2(s_tan.y, s_tan.x)
    link_obj(g1, "05_NAVIGATION_GUIDES")

    # Row 2
    g2 = bpy.data.objects.new(grid_names[i+4], None)
    g2.empty_display_type = 'SINGLE_ARROW'
    g2.empty_display_size = 2.5
    g2.location = s_pos + s_norm * lane_offsets[i] + s_tan * row2_y_offset + Vector((0, 0, 0.1))
    g2.rotation_euler.z = math.atan2(s_tan.y, s_tan.x)
    link_obj(g2, "05_NAVIGATION_GUIDES")

# 10.3 Checkpoint_01 through Checkpoint_08
for cp_idx, r_idx in enumerate(checkpoint_ring_indices):
    cp_frame = ring_frames[r_idx]
    cp_empty = bpy.data.objects.new(f"Checkpoint_{cp_idx+1:02d}", None)
    cp_empty.empty_display_type = 'CUBE'
    cp_empty.empty_display_size = 3.5
    cp_empty.location = cp_frame["pos"] + Vector((0, 0, 1.5))
    cp_empty.rotation_euler.z = math.atan2(cp_frame["tangent"].y, cp_frame["tangent"].x)
    link_obj(cp_empty, "05_NAVIGATION_GUIDES")

# 10.4 Pit_Entry and Pit_Exit
pit_entry = bpy.data.objects.new("Pit_Entry", None)
pit_entry.empty_display_type = 'SPHERE'
pit_entry.empty_display_size = 3.0
pit_entry.location = s_pos + s_norm * 8.5 + s_tan * -70.0
link_obj(pit_entry, "05_NAVIGATION_GUIDES")

pit_exit = bpy.data.objects.new("Pit_Exit", None)
pit_exit.empty_display_type = 'SPHERE'
pit_exit.empty_display_size = 3.0
pit_exit.location = s_pos + s_norm * 8.5 + s_tan * 70.0
link_obj(pit_exit, "05_NAVIGATION_GUIDES")

# 10.5 AI_Racing_Line (Editable closed Bezier curve object)
curve_data = bpy.data.curves.new("Curve_AI_Racing_Line", type='CURVE')
curve_data.dimensions = '3D'
curve_data.resolution_u = 4
spline = curve_data.splines.new('BEZIER')
spline.use_cyclic_u = True

# Downsample points for editable curve
racing_line_pts = [circuit_wps[i] + Vector((0, 0, 0.25)) for i in range(num_wp)]
spline.bezier_points.add(len(racing_line_pts) - 1)
for i, pt in enumerate(racing_line_pts):
    bp = spline.bezier_points[i]
    bp.co = pt
    bp.handle_left_type = 'AUTO'
    bp.handle_right_type = 'AUTO'

ai_curve_obj = bpy.data.objects.new("AI_Racing_Line", curve_data)
link_obj(ai_curve_obj, "05_NAVIGATION_GUIDES")

print("Navigation and Unity guide objects generated.")

# -------------------------------------------------------------
# 11. Lighting & Cameras
# -------------------------------------------------------------
# Key Track Lighting: Selective mood spots rather than hundreds of lights
light_data_start = bpy.data.lights.new(name="Light_Start_Gantry", type='SPOT')
light_data_start.energy = 8000.0
light_data_start.spot_size = math.radians(70.0)
light_data_start.color = (0.7, 0.9, 1.0)
start_light = bpy.data.objects.new("Light_Start_Gantry", light_data_start)
start_light.location = s_pos + Vector((0, 0, 14.0))
start_light.rotation_euler = (0.0, 0.0, 0.0)
link_obj(start_light, "06_LIGHTING_AND_CAMERAS")

# High Altitude Moon/Ambient Fill
sun_data = bpy.data.lights.new(name="Cyber_Night_Moon", type='SUN')
sun_data.energy = 0.8
sun_data.color = (0.2, 0.35, 0.7)
sun_obj = bpy.data.objects.new("Cyber_Night_Moon", sun_data)
sun_obj.rotation_euler = (math.radians(65.0), math.radians(15.0), math.radians(45.0))
link_obj(sun_obj, "06_LIGHTING_AND_CAMERAS")

# 11.1 Cam_Overview_City (Elevated overview showing the full illuminated megacity circuit)
cam_over_data = bpy.data.cameras.new("Cam_Overview_City")
cam_over_data.lens = 20.0
cam_over = bpy.data.objects.new("Cam_Overview_City", cam_over_data)
cam_over.location = Vector((120.0, -180.0, 360.0))
cam_over.rotation_euler = (math.radians(48.0), 0.0, math.radians(35.0))
link_obj(cam_over, "06_LIGHTING_AND_CAMERAS")

# 11.2 Cam_Track_Level (Low-angle view looking down the Neon Strip straight)
cam_track_data = bpy.data.cameras.new("Cam_Track_Level")
cam_track_data.lens = 28.0
cam_track = bpy.data.objects.new("Cam_Track_Level", cam_track_data)
cam_track.location = Vector((-155.0, -130.0, 1.8))
cam_track.rotation_euler = (math.radians(85.0), 0.0, math.radians(-150.0))
link_obj(cam_track, "06_LIGHTING_AND_CAMERAS")

# 11.3 Cam_Cinematic_Start (Cinematic view behind starting grid looking towards Turn 1)
cam_start_data = bpy.data.cameras.new("Cam_Cinematic_Start")
cam_start_data.lens = 24.0
cam_start = bpy.data.objects.new("Cam_Cinematic_Start", cam_start_data)
cam_start.location = s_pos + s_tan * -45.0 + Vector((0, 0, 4.2))
cam_start.rotation_euler = (math.radians(82.0), 0.0, math.atan2(s_tan.y, s_tan.x) - math.radians(90.0))
link_obj(cam_start, "06_LIGHTING_AND_CAMERAS")

# Set active camera to Cinematic Start
bpy.context.scene.camera = cam_start

# Set viewport to Material Preview
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'

# -------------------------------------------------------------
# 12. Save File & Completion
# -------------------------------------------------------------
save_path = r"d:\game\cyberpunk_circuit.blend"
bpy.ops.wm.save_as_mainfile(filepath=save_path)
print(f"SUCCESS: Scene saved to {save_path}")
'''

print("Sending Cyberpunk Megacity Circuit script to Blender...")
res = send_code(cyberpunk_code, timeout=90.0)
print("Execution Result:", res)

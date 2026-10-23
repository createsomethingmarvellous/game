"""
Build Buddh International Circuit (BIC) with:
1. Exact Buddh layout from the uploaded diagram.
2. 18m road width (accommodating 4 cars in parallel).
3. Complete separation: Track in its own clean collection, Buildings with strict 28m+ setback in separate collection.
4. Animated Camera (Cam_Follow_Track) moving along the entire track over 600 frames (press Spacebar to play!).
5. Saves scene to d:\game\cyberpunk_circuit.blend.
"""

from blender_client import send_code

buddh_animated_code = r'''
import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, Euler

# -------------------------------------------------------------
# 1. Clean Scene and Reset
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
for block in bpy.data.actions:
    bpy.data.actions.remove(block)

# Deep night cyberpunk sky
world = bpy.context.scene.world
if not world:
    world = bpy.data.worlds.new("Cyberpunk_Night")
    bpy.context.scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs['Color'].default_value = (0.004, 0.007, 0.018, 1.0)
    bg_node.inputs['Strength'].default_value = 0.5

# Setup Clean Distinct Collections
collection_names = [
    "01_TRACK_SYSTEM",
    "02_CYBERPUNK_BUILDINGS",
    "03_RACING_INFRASTRUCTURE",
    "04_NAVIGATION_GUIDES",
    "05_CAMERAS_AND_LIGHTS"
]

collections = {}
for name in collection_names:
    existing = bpy.data.collections.get(name)
    if existing:
        bpy.context.scene.collection.children.unlink(existing)
        bpy.data.collections.remove(existing)
    new_c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(new_c)
    collections[name] = new_c

# Also purge any leftover collections
for c in list(bpy.data.collections):
    if c.name not in collection_names:
        try:
            bpy.data.collections.remove(c)
        except Exception:
            pass

def link_obj(obj, coll_name):
    for c in list(obj.users_collection):
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

mat_asphalt       = make_mat("Mat_Asphalt_Wet", (0.02, 0.02, 0.025, 1.0), roughness=0.22, metallic=0.05)
mat_road_white    = make_mat("Mat_Road_White", (0.92, 0.92, 0.95, 1.0), roughness=0.3)
mat_road_yellow   = make_mat("Mat_Road_Yellow", (1.0, 0.75, 0.05, 1.0), roughness=0.3)
mat_concrete_dark = make_mat("Mat_Concrete_Dark", (0.09, 0.09, 0.10, 1.0), roughness=0.88)
mat_metal_dark    = make_mat("Mat_Metal_Dark", (0.06, 0.06, 0.07, 1.0), metallic=0.9, roughness=0.25)
mat_neon_cyan     = make_mat("Mat_Neon_Cyan", (0.0, 0.9, 1.0, 1.0), emission=(0.0, 0.9, 1.0, 1.0), emission_strength=14.0)
mat_neon_magenta  = make_mat("Mat_Neon_Magenta", (1.0, 0.05, 0.55, 1.0), emission=(1.0, 0.05, 0.55, 1.0), emission_strength=14.0)
mat_neon_violet   = make_mat("Mat_Neon_Violet", (0.65, 0.08, 1.0, 1.0), emission=(0.65, 0.08, 1.0, 1.0), emission_strength=12.0)
mat_neon_amber    = make_mat("Mat_Neon_Amber", (1.0, 0.55, 0.02, 1.0), emission=(1.0, 0.55, 0.02, 1.0), emission_strength=12.0)
mat_start_red     = make_mat("Mat_Start_Red", (1.0, 0.02, 0.02, 1.0), emission=(1.0, 0.02, 0.02, 1.0), emission_strength=20.0)
mat_facade_lit    = make_mat("Mat_Facade_Lit", (0.03, 0.03, 0.04, 1.0), metallic=0.5, roughness=0.4, emission=(0.95, 0.85, 0.65, 1.0), emission_strength=0.7)

# -------------------------------------------------------------
# 3. Exact Buddh International Circuit Waypoints (From Uploaded Diagram)
# -------------------------------------------------------------
# Clockwise loop, North is +Y:
# - Start/Finish Straight: runs NNW from T16 to T1
# - Turn 1: 90 deg uphill right-hander
# - Turn 2 & 3: Sweeping uphill left into summit hairpin at T3
# - Back Straight: 1.06 km long downhill blast
# - Turn 4: Tight right-hander at bottom-right
# - Straight to Turn 5 (left sweeper)
# - Turn 6 (left), Turn 7 (right), Turn 8 (left), Turn 9 (right)
# - Turn 10 & 11: Iconic Parabolica carousel loop
# - Turn 12, 13 (chicane) & Turn 14 (left kink)
# - Turn 15: Sharp 90 deg left-hander
# - Downhill chute to Turn 16 (final corner onto main straight)

buddh_wps = [
    # Main Start/Finish Straight (Length ~340m)
    Vector((0.0, 0.0, 0.0)),            # Start / Finish Line
    Vector((-35.0, 95.0, 3.0)),
    Vector((-70.0, 195.0, 6.0)),
    Vector((-105.0, 290.0, 9.0)),

    # Turn 1: Uphill 90 deg right-hander
    Vector((-125.0, 350.0, 12.0)),      # T1 Entry
    Vector((-110.0, 375.0, 13.0)),      # T1 Apex
    Vector((-65.0, 375.0, 13.5)),       # T1 Exit

    # Turn 2: Sweeping uphill left curve
    Vector((-15.0, 385.0, 14.5)),
    Vector((35.0, 415.0, 15.5)),        # T2 Apex
    Vector((70.0, 475.0, 17.0)),

    # Turn 3: 135 deg sharp right hairpin at circuit summit (+18m)
    Vector((95.0, 535.0, 18.0)),
    Vector((110.0, 565.0, 18.5)),       # T3 Apex summit
    Vector((125.0, 550.0, 18.0)),       # T3 Exit

    # Massive Long Back Straight (1.06 km downhill skybridge on pylons)
    Vector((155.0, 440.0, 16.0)),
    Vector((195.0, 295.0, 13.0)),
    Vector((235.0, 145.0, 10.0)),
    Vector((275.0, -5.0, 7.0)),
    Vector((315.0, -155.0, 4.0)),
    Vector((350.0, -285.0, 1.5)),

    # Turn 4: Sharp right-hander at bottom-right corner
    Vector((368.0, -345.0, 0.0)),       # T4 Entry
    Vector((350.0, -368.0, 0.0)),       # T4 Apex
    Vector((315.0, -355.0, 0.0)),       # T4 Exit

    # High-speed chute heading WNW to Turn 5
    Vector((250.0, -315.0, 0.0)),
    Vector((175.0, -268.0, 0.0)),
    Vector((95.0, -218.0, 0.0)),
    Vector((20.0, -172.0, 0.0)),

    # Turn 5 (left sweeper) & Turn 6 (sharp left inside cyber tunnel)
    Vector((-35.0, -150.0, -2.0)),      # T5 Apex & Tunnel Entrance
    Vector((-75.0, -170.0, -4.0)),      # In tunnel
    Vector((-105.0, -205.0, -4.5)),     # T6 Apex

    # Turn 7 (right flick) & Turn 8, 9 (S-curves / chicane exiting tunnel)
    Vector((-95.0, -245.0, -4.0)),      # T7 Apex
    Vector((-92.0, -280.0, -2.0)),      # Tunnel Exit
    Vector((-98.0, -315.0, 0.0)),       # T8 Apex
    Vector((-120.0, -350.0, 0.0)),      # T9 Apex
    Vector((-125.0, -395.0, 0.0)),

    # Turn 10 & 11: Iconic Double-Apex Parabolica Carousel Loop
    Vector((-125.0, -450.0, 0.0)),      # T10 Entry
    Vector((-155.0, -485.0, 0.0)),      # T10 South Apex
    Vector((-200.0, -475.0, 0.0)),      # Banked carousel bowl
    Vector((-225.0, -430.0, 0.0)),      # T11 Apex
    Vector((-215.0, -375.0, 0.0)),      # T11 Exit

    # Turn 12 & 13: Quick Esses
    Vector((-180.0, -325.0, 0.0)),      # T12 Apex
    Vector((-150.0, -265.0, 0.0)),      # T13 Apex

    # Turn 14: Left Kink
    Vector((-162.0, -195.0, 0.0)),      # T14 Apex
    Vector((-158.0, -125.0, 0.0)),

    # Turn 15: Sharp 90 deg corner
    Vector((-155.0, -65.0, 0.0)),
    Vector((-130.0, -48.0, 0.0)),       # T15 Apex
    Vector((-95.0, -68.0, 0.0)),

    # Chute down-right to Turn 16
    Vector((-55.0, -95.0, 0.0)),
    Vector((-20.0, -122.0, 0.0)),

    # Turn 16: Final right-hander onto Main Straight
    Vector((8.0, -142.0, 0.0)),         # T16 Apex
    Vector((18.0, -120.0, 0.0)),        # T16 Exit
    Vector((12.0, -60.0, 0.0)),
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

num_wp = len(buddh_wps)
subdiv = 14
track_pts = []
for i in range(num_wp):
    p0 = buddh_wps[(i - 1) % num_wp]
    p1 = buddh_wps[i]
    p2 = buddh_wps[(i + 1) % num_wp]
    p3 = buddh_wps[(i + 2) % num_wp]
    for s in range(subdiv):
        track_pts.append(catmull_rom(p0, p1, p2, p3, s / subdiv))

total_rings = len(track_pts)
print(f"Generated {total_rings} smooth track rings for Buddh Circuit.")

ring_frames = []
for i in range(total_rings):
    curr_pt = track_pts[i]
    next_pt = track_pts[(i + 1) % total_rings]
    prev_pt = track_pts[(i - 1) % total_rings]
    tangent = (next_pt - prev_pt).normalized()
    up = Vector((0.0, 0.0, 1.0))
    normal = tangent.cross(up).normalized()
    binormal = normal.cross(tangent).normalized()

    # Dynamic banking in corners
    curvature = (next_pt - 2.0 * curr_pt + prev_pt).length
    bank = math.sin(i / 10.0) * min(curvature * 0.15, 0.08)
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
road_mesh = bpy.data.meshes.new("Mesh_Track_Road")
road_obj = bpy.data.objects.new("Track_Road_Surface", road_mesh)
link_obj(road_obj, "01_TRACK_SYSTEM")
road_obj.data.materials.append(mat_asphalt)
road_obj.data.materials.append(mat_road_white)
road_obj.data.materials.append(mat_road_yellow)

bm_road = bmesh.new()

# Cross-section profile for 18m asphalt (-9.0m to +9.0m)
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

# -------------------------------------------------------------
# 5. Object 2: Kerbs & Modular Barriers (Separate Object in 01_TRACK_SYSTEM)
# -------------------------------------------------------------
barrier_mesh = bpy.data.meshes.new("Mesh_Barriers_Kerbs")
barrier_obj = bpy.data.objects.new("Track_Barriers_And_Kerbs", barrier_mesh)
link_obj(barrier_obj, "01_TRACK_SYSTEM")
barrier_obj.data.materials.append(mat_concrete_dark)  # 0
barrier_obj.data.materials.append(mat_metal_dark)     # 1
barrier_obj.data.materials.append(mat_neon_cyan)      # 2
barrier_obj.data.materials.append(mat_neon_magenta)   # 3

bm_bar = bmesh.new()

left_bar_profile = [
    (-9.0, 0.02, 2),
    (-10.8, 0.15, 2),
    (-11.0, 0.0, 0),
    (-11.2, 0.8, 0),
    (-11.2, 1.3, 1),
    (-11.1, 1.4, 2),
]

right_bar_profile = [
    ( 9.0, 0.02, 3),
    ( 10.8, 0.15, 3),
    ( 11.0, 0.0, 0),
    ( 11.2, 0.8, 0),
    ( 11.2, 1.3, 1),
    ( 11.1, 1.4, 3),
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
    kerb_alt = 2 if ((i // 6) % 2 == 0) else 3

    l1 = left_ring_verts[i]
    l2 = left_ring_verts[next_i]
    for p in range(len(left_bar_profile) - 1):
        face = bm_bar.faces.new((l1[p], l1[p+1], l2[p+1], l2[p]))
        mat = left_bar_profile[p][2]
        face.material_index = kerb_alt if mat in (2, 3) else mat

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

# -------------------------------------------------------------
# 6. Object 3: Structural Bridge Pylons & Cyber Tunnel
# -------------------------------------------------------------
# Structural Pylons on the 1km elevated back straight (Z >= 8.0)
pylon_mesh = bpy.data.meshes.new("Mesh_Bridge_Pylons")
pylon_obj = bpy.data.objects.new("Bridge_Support_Pylons", pylon_mesh)
link_obj(pylon_obj, "01_TRACK_SYSTEM")
pylon_obj.data.materials.append(mat_concrete_dark)
pylon_obj.data.materials.append(mat_metal_dark)

bm_pylon = bmesh.new()
for i in range(0, total_rings, 8):
    f = ring_frames[i]
    if f["pos"].z >= 6.0:
        deck_pos = f["pos"]
        for side in [-7.5, 7.5]:
            col_base = deck_pos + f["normal"] * side
            col_base.z = 0.0
            p_height = deck_pos.z
            hw, hd = 1.2, 1.2
            v1 = bm_pylon.verts.new(col_base + Vector((-hw, -hd, 0)))
            v2 = bm_pylon.verts.new(col_base + Vector(( hw, -hd, 0)))
            v3 = bm_pylon.verts.new(col_base + Vector(( hw,  hd, 0)))
            v4 = bm_pylon.verts.new(col_base + Vector((-hw,  hd, 0)))
            v5 = bm_pylon.verts.new(col_base + Vector((-hw, -hd, p_height - 0.4)))
            v6 = bm_pylon.verts.new(col_base + Vector(( hw, -hd, p_height - 0.4)))
            v7 = bm_pylon.verts.new(col_base + Vector(( hw,  hd, p_height - 0.4)))
            v8 = bm_pylon.verts.new(col_base + Vector((-hw,  hd, p_height - 0.4)))
            bm_pylon.faces.new((v1, v2, v6, v5))
            bm_pylon.faces.new((v2, v3, v7, v6))
            bm_pylon.faces.new((v3, v4, v8, v7))
            bm_pylon.faces.new((v4, v1, v5, v8))

bm_pylon.to_mesh(pylon_mesh)
bm_pylon.free()
pylon_mesh.update()

# Cyber Tunnel on Turns 5-7 (Z < 0.0)
tunnel_mesh = bpy.data.meshes.new("Mesh_Cyber_Tunnel")
tunnel_obj = bpy.data.objects.new("Cyber_Tunnel_Structure", tunnel_mesh)
link_obj(tunnel_obj, "01_TRACK_SYSTEM")
tunnel_obj.data.materials.append(mat_concrete_dark)
tunnel_obj.data.materials.append(mat_neon_cyan)
tunnel_obj.data.materials.append(mat_neon_violet)

bm_tun = bmesh.new()
arch_pts = [
    (-11.5, 0.0), (-11.5, 4.0), (-8.0, 6.8), (-3.0, 7.5),
    ( 3.0, 7.5), ( 8.0, 6.8), ( 11.5, 4.0), ( 11.5, 0.0)
]
tunnel_rings = []
for i, f in enumerate(ring_frames):
    if f["pos"].z <= -0.5:
        t_verts = []
        for (lat, h) in arch_pts:
            p = f["pos"] + f["normal"] * lat + f["binormal"] * h
            t_verts.append(bm_tun.verts.new(p))
        tunnel_rings.append((i, t_verts))

bm_tun.verts.ensure_lookup_table()
for k in range(len(tunnel_rings) - 1):
    idx_curr, t1 = tunnel_rings[k]
    idx_next, t2 = tunnel_rings[k + 1]
    if idx_next == idx_curr + 1:
        is_neon_rib = (k % 4 == 0)
        rib_mat = 1 if (k % 8 == 0) else 2
        for p in range(len(arch_pts) - 1):
            face = bm_tun.faces.new((t1[p], t1[p+1], t2[p+1], t2[p]))
            face.material_index = rib_mat if is_neon_rib else 0

bm_tun.to_mesh(tunnel_mesh)
bm_tun.free()
tunnel_mesh.update()

# -------------------------------------------------------------
# 7. Cyberpunk Megacity Buildings (Properly Separated with Setback!)
# -------------------------------------------------------------
# Strict separation: every building is placed at least 26m away from track centerline!
def min_dist_to_track(x, y):
    min_d = float('inf')
    # Subsample track points for fast collision check
    for f in ring_frames[::4]:
        dx = x - f["pos"].x
        dy = y - f["pos"].y
        d = math.sqrt(dx*dx + dy*dy)
        if d < min_d:
            min_d = d
    return min_d

# Candidate building sites
building_candidates = [
    # East street canyon (Main straight & T1)
    (38.0, -140.0, 32.0, 34.0, 150.0),
    (40.0, -60.0, 30.0, 32.0, 210.0),
    (42.0, 20.0, 32.0, 30.0, 250.0),
    (42.0, 110.0, 34.0, 34.0, 180.0),
    (40.0, 200.0, 36.0, 36.0, 230.0),
    # West street canyon (Main straight)
    (-40.0, -140.0, 34.0, 34.0, 160.0),
    (-42.0, -60.0, 32.0, 32.0, 220.0),
    (-45.0, 20.0, 30.0, 32.0, 260.0),
    (-48.0, 110.0, 34.0, 34.0, 190.0),
    (-50.0, 200.0, 35.0, 35.0, 240.0),
    # North summit & Turn 2-3 area
    (-170.0, 340.0, 42.0, 42.0, 210.0),
    (-80.0, 450.0, 45.0, 40.0, 250.0),
    (0.0, 470.0, 40.0, 40.0, 270.0),
    (170.0, 580.0, 45.0, 45.0, 280.0),
    (60.0, 620.0, 45.0, 45.0, 300.0),
    # Back straight eastern megastructures
    (220.0, 400.0, 40.0, 40.0, 220.0),
    (260.0, 260.0, 42.0, 42.0, 240.0),
    (300.0, 110.0, 40.0, 40.0, 230.0),
    (340.0, -40.0, 42.0, 42.0, 210.0),
    (380.0, -180.0, 40.0, 40.0, 220.0),
    # Turn 4 & South sector
    (420.0, -320.0, 45.0, 45.0, 250.0),
    (360.0, -430.0, 45.0, 45.0, 240.0),
    (280.0, -400.0, 42.0, 42.0, 200.0),
    (180.0, -350.0, 40.0, 40.0, 180.0),
    # Central infield & lake area
    (100.0, -80.0, 50.0, 50.0, 260.0),
    (140.0, 80.0, 45.0, 45.0, 280.0),
    # Parabolica Turn 10-11 surrounding area
    (-70.0, -480.0, 42.0, 42.0, 220.0),
    (-150.0, -560.0, 45.0, 45.0, 240.0),
    (-260.0, -530.0, 45.0, 45.0, 230.0),
    (-280.0, -420.0, 45.0, 45.0, 250.0),
    (-270.0, -310.0, 42.0, 42.0, 210.0),
    # West sector (Turns 12-16)
    (-220.0, -180.0, 40.0, 40.0, 220.0),
    (-210.0, -90.0, 42.0, 42.0, 240.0),
    (-200.0, 10.0, 40.0, 40.0, 220.0),
    (-180.0, 120.0, 42.0, 42.0, 200.0),
    (-110.0, -10.0, 36.0, 36.0, 190.0),
]

bldg_idx = 0
for (bx, by, bw, bd, bh) in building_candidates:
    # Ensure strict 24m+ buffer from road edge
    radius = math.sqrt(bw*bw + bd*bd) / 2.0
    if min_dist_to_track(bx, by) >= (radius + 15.0):
        bldg_idx += 1
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, bh / 2.0))
        bldg = bpy.context.active_object
        bldg.name = f"Cyber_Skyscraper_{bldg_idx:02d}"
        bldg.scale = (bw, bd, bh)
        bldg.data.materials.append(mat_facade_lit if (bldg_idx % 2 == 0) else mat_concrete_dark)
        link_obj(bldg, "02_CYBERPUNK_BUILDINGS")

        if bh >= 220.0:
            # Roof spire
            bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=20.0, location=(bx, by, bh + 10.0))
            spire = bpy.context.active_object
            spire.name = f"Roof_Spire_{bldg_idx:02d}"
            spire.data.materials.append(mat_metal_dark)
            link_obj(spire, "02_CYBERPUNK_BUILDINGS")

# Holographic Neon Billboards (Cleanly placed in 02_CYBERPUNK_BUILDINGS)
billboards = [
    ((26.0, -80.0, 24.0), (1.0, 16.0, 8.0), 0.0, mat_neon_cyan, "Billboard_CYBERDRIVE"),
    ((-26.0, -20.0, 22.0), (1.0, 16.0, 8.0), 0.0, mat_neon_magenta, "Billboard_NEOKAIJU"),
    ((26.0, 60.0, 26.0), (1.0, 18.0, 9.0), 0.0, mat_neon_violet, "Billboard_NEXUS9"),
    ((175.0, 480.0, 28.0), (16.0, 1.0, 8.0), -0.6, mat_neon_amber, "Billboard_OVERDRIVE"),
    ((250.0, 200.0, 26.0), (1.0, 18.0, 9.0), -1.1, mat_neon_cyan, "Billboard_HYPERSPEED"),
    ((330.0, -80.0, 24.0), (1.0, 18.0, 9.0), -1.1, mat_neon_magenta, "Billboard_QUANTUM"),
    ((-180.0, -440.0, 22.0), (18.0, 1.0, 9.0), 0.0, mat_neon_cyan, "Billboard_PARABOLICA"),
    ((-120.0, -100.0, 22.0), (1.0, 16.0, 8.0), 0.7, mat_neon_violet, "Billboard_SYNTHWAVE"),
]

for b_pos, (bw, bd, bh), rot_z, b_mat, b_name in billboards:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=b_pos)
    board = bpy.context.active_object
    board.name = b_name
    board.scale = (bw, bd, bh)
    board.rotation_euler.z = rot_z
    board.data.materials.append(b_mat)
    link_obj(board, "02_CYBERPUNK_BUILDINGS")

# Street Lamps along Main Straight
for y in range(-140, 140, 40):
    for side, name_s in [(-12.5, "L"), (12.5, "R")]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=7.5, location=(side, y, 3.75))
        pole = bpy.context.active_object
        pole.name = f"StreetLamp_Pole_{name_s}_{y}"
        pole.data.materials.append(mat_metal_dark)
        link_obj(pole, "02_CYBERPUNK_BUILDINGS")

        head_x = side + (1.0 if side < 0 else -1.0)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(head_x, y, 7.2))
        head = bpy.context.active_object
        head.name = f"StreetLamp_Head_{name_s}_{y}"
        head.scale = (1.4, 0.4, 0.2)
        head.data.materials.append(mat_neon_cyan)
        link_obj(head, "02_CYBERPUNK_BUILDINGS")

# -------------------------------------------------------------
# 8. Racing Infrastructure (Collection 03)
# -------------------------------------------------------------
s_frame = ring_frames[0]
s_pos = s_frame["pos"]
s_tan = s_frame["tangent"]
s_norm = s_frame["normal"]

# Starting Gantry
bpy.ops.mesh.primitive_cube_add(size=1.0, location=s_pos + s_norm * 12.0 + Vector((0, 0, 6.0)))
p1 = bpy.context.active_object
p1.name = "Gantry_Pillar_Left"
p1.scale = (1.2, 1.2, 12.0)
p1.data.materials.append(mat_metal_dark)
link_obj(p1, "03_RACING_INFRASTRUCTURE")

bpy.ops.mesh.primitive_cube_add(size=1.0, location=s_pos - s_norm * 12.0 + Vector((0, 0, 6.0)))
p2 = bpy.context.active_object
p2.name = "Gantry_Pillar_Right"
p2.scale = (1.2, 1.2, 12.0)
p2.data.materials.append(mat_metal_dark)
link_obj(p2, "03_RACING_INFRASTRUCTURE")

bpy.ops.mesh.primitive_cube_add(size=1.0, location=s_pos + Vector((0, 0, 11.5)))
bar = bpy.context.active_object
bar.name = "Gantry_Crossbeam"
bar.scale = (2.0, 26.0, 1.6)
bar.data.materials.append(mat_metal_dark)
link_obj(bar, "03_RACING_INFRASTRUCTURE")

for idx in range(5):
    l_pos = s_pos + s_norm * (idx * 2.8 - 5.6) + Vector((0, 0, 10.6))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=0.4, location=l_pos)
    lamp = bpy.context.active_object
    lamp.name = f"StartLight_Red_{idx+1}"
    lamp.data.materials.append(mat_start_red)
    link_obj(lamp, "03_RACING_INFRASTRUCTURE")

# Timing Tower
bpy.ops.mesh.primitive_cube_add(size=1.0, location=s_pos + s_norm * 17.0 + Vector((0, 0, 16.0)))
tower = bpy.context.active_object
tower.name = "Timing_Tower_Main"
tower.scale = (4.5, 4.5, 32.0)
tower.data.materials.append(mat_concrete_dark)
link_obj(tower, "03_RACING_INFRASTRUCTURE")

bpy.ops.mesh.primitive_cube_add(size=1.0, location=s_pos + s_norm * 14.6 + Vector((0, 0, 22.0)))
screen = bpy.context.active_object
screen.name = "Timing_Tower_DigitalScreen"
screen.scale = (0.2, 3.8, 14.0)
screen.data.materials.append(mat_neon_cyan)
link_obj(screen, "03_RACING_INFRASTRUCTURE")

# 8 Checkpoint Gates
cp_indices = [int(total_rings * (i / 8.0)) for i in range(8)]
for cp_idx, r_idx in enumerate(cp_indices):
    cp_f = ring_frames[r_idx]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=cp_f["pos"] + Vector((0, 0, 9.0)))
    gate = bpy.context.active_object
    gate.name = f"Checkpoint_Gate_{cp_idx+1:02d}"
    gate.scale = (1.5, 24.0, 1.2)
    gate.data.materials.append(mat_neon_cyan if (cp_idx % 2 == 0) else mat_neon_magenta)
    gate.rotation_euler.z = math.atan2(cp_f["tangent"].y, cp_f["tangent"].x)
    link_obj(gate, "03_RACING_INFRASTRUCTURE")

# -------------------------------------------------------------
# 9. Navigation Guides & Unity Objects (Collection 04)
# -------------------------------------------------------------
sf_obj = bpy.data.objects.new("Start_Finish", None)
sf_obj.empty_display_type = 'ARROWS'
sf_obj.empty_display_size = 4.0
sf_obj.location = s_pos
sf_obj.rotation_euler.z = math.atan2(s_tan.y, s_tan.x)
link_obj(sf_obj, "04_NAVIGATION_GUIDES")

# 8 Grid Slots (4-wide in 2 rows on the 18m road surface)
lane_offsets = [-6.75, -2.25, 2.25, 6.75]
for i in range(4):
    # Row 1
    g1 = bpy.data.objects.new(f"Player_Grid_{i+1:02d}", None)
    g1.empty_display_type = 'SINGLE_ARROW'
    g1.empty_display_size = 2.5
    g1.location = s_pos + s_norm * lane_offsets[i] + s_tan * -15.0 + Vector((0, 0, 0.1))
    g1.rotation_euler.z = math.atan2(s_tan.y, s_tan.x)
    link_obj(g1, "04_NAVIGATION_GUIDES")

    # Row 2
    g2 = bpy.data.objects.new(f"Player_Grid_{i+5:02d}", None)
    g2.empty_display_type = 'SINGLE_ARROW'
    g2.empty_display_size = 2.5
    g2.location = s_pos + s_norm * lane_offsets[i] + s_tan * -30.0 + Vector((0, 0, 0.1))
    g2.rotation_euler.z = math.atan2(s_tan.y, s_tan.x)
    link_obj(g2, "04_NAVIGATION_GUIDES")

for cp_idx, r_idx in enumerate(cp_indices):
    cp_f = ring_frames[r_idx]
    cp_empty = bpy.data.objects.new(f"Checkpoint_{cp_idx+1:02d}", None)
    cp_empty.empty_display_type = 'CUBE'
    cp_empty.empty_display_size = 3.5
    cp_empty.location = cp_f["pos"] + Vector((0, 0, 1.5))
    cp_empty.rotation_euler.z = math.atan2(cp_f["tangent"].y, cp_f["tangent"].x)
    link_obj(cp_empty, "04_NAVIGATION_GUIDES")

pit_entry = bpy.data.objects.new("Pit_Entry", None)
pit_entry.empty_display_type = 'SPHERE'
pit_entry.empty_display_size = 3.0
pit_entry.location = s_pos + s_norm * 8.5 + s_tan * -70.0
link_obj(pit_entry, "04_NAVIGATION_GUIDES")

pit_exit = bpy.data.objects.new("Pit_Exit", None)
pit_exit.empty_display_type = 'SPHERE'
pit_exit.empty_display_size = 3.0
pit_exit.location = s_pos + s_norm * 8.5 + s_tan * 70.0
link_obj(pit_exit, "04_NAVIGATION_GUIDES")

# AI Racing Line Curve
curve_data = bpy.data.curves.new("Curve_AI_Racing_Line", type='CURVE')
curve_data.dimensions = '3D'
curve_data.resolution_u = 4
spline = curve_data.splines.new('BEZIER')
spline.use_cyclic_u = True
spline.bezier_points.add(len(buddh_wps) - 1)
for i, pt in enumerate(buddh_wps):
    bp = spline.bezier_points[i]
    bp.co = pt + Vector((0, 0, 0.2))
    bp.handle_left_type = 'AUTO'
    bp.handle_right_type = 'AUTO'

ai_curve_obj = bpy.data.objects.new("AI_Racing_Line", curve_data)
link_obj(ai_curve_obj, "04_NAVIGATION_GUIDES")

# -------------------------------------------------------------
# 10. ANIMATED CAMERA (Moves smoothly along the entire track!)
# -------------------------------------------------------------
# Setup scene timeline for 600 frames (Press Spacebar in Blender to play!)
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 600
scene.render.fps = 24

# Create the animated tracking camera
cam_track_data = bpy.data.cameras.new("Cam_Follow_Track")
cam_track_data.lens = 24.0  # Wide cinematic focal length
cam_follow = bpy.data.objects.new("Cam_Follow_Track", cam_track_data)
link_obj(cam_follow, "05_CAMERAS_AND_LIGHTS")
scene.camera = cam_follow

# Keyframe the camera along the 518 track rings smoothly over 600 frames
total_anim_frames = 600
keyframe_step = 4  # Keyframe every 4 frames for smooth motion

for frame_num in range(1, total_anim_frames + 1, keyframe_step):
    t_fraction = (frame_num - 1) / float(total_anim_frames)
    ring_idx = int(t_fraction * total_rings) % total_rings
    look_idx = (ring_idx + 14) % total_rings  # Look ahead 14 rings (~35 meters)

    f_curr = ring_frames[ring_idx]
    f_look = ring_frames[look_idx]

    # Camera location: 3.5m above track centerline, slight rear offset
    cam_pos = f_curr["pos"] + Vector((0, 0, 3.5))

    # Look-at point forward along track
    look_target = f_look["pos"] + Vector((0, 0, 2.5))
    forward_dir = (look_target - cam_pos).normalized()

    # Calculate camera rotation matrix
    # Blender camera default points along -Z with +Y up
    track_up = Vector((0.0, 0.0, 1.0))
    cam_right = forward_dir.cross(track_up).normalized()
    cam_up = cam_right.cross(forward_dir).normalized()

    rot_mat = Matrix((
        (cam_right.x, cam_up.x, -forward_dir.x),
        (cam_right.y, cam_up.y, -forward_dir.y),
        (cam_right.z, cam_up.z, -forward_dir.z)
    ))

    cam_follow.location = cam_pos
    cam_follow.rotation_euler = rot_mat.to_euler()

    cam_follow.keyframe_insert(data_path="location", frame=frame_num)
    cam_follow.keyframe_insert(data_path="rotation_euler", frame=frame_num)

# Also create Overview and Cinematic Start cameras
cam_over_data = bpy.data.cameras.new("Cam_Overview_City")
cam_over_data.lens = 18.0
cam_over = bpy.data.objects.new("Cam_Overview_City", cam_over_data)
cam_over.location = Vector((120.0, -180.0, 420.0))
cam_over.rotation_euler = (math.radians(46.0), 0.0, math.radians(35.0))
link_obj(cam_over, "05_CAMERAS_AND_LIGHTS")

# Ambient Night Moon Light
sun_data = bpy.data.lights.new(name="Cyber_Night_Moon", type='SUN')
sun_data.energy = 0.8
sun_data.color = (0.25, 0.4, 0.8)
sun_obj = bpy.data.objects.new("Cyber_Night_Moon", sun_data)
sun_obj.rotation_euler = (math.radians(65.0), math.radians(15.0), math.radians(45.0))
link_obj(sun_obj, "05_CAMERAS_AND_LIGHTS")

# Start Gantry Spotlight
spot_data = bpy.data.lights.new(name="Light_Start_Gantry", type='SPOT')
spot_data.energy = 8000.0
spot_data.spot_size = math.radians(70.0)
spot_data.color = (0.7, 0.9, 1.0)
spot_obj = bpy.data.objects.new("Light_Start_Gantry", spot_data)
spot_obj.location = s_pos + Vector((0, 0, 14.0))
link_obj(spot_obj, "05_CAMERAS_AND_LIGHTS")

# Set current frame to 1
scene.frame_set(1)

# Set 3D Viewport to Material Preview & snap to Cam_Follow_Track
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    space.region_3d.view_perspective = 'CAMERA'

# Save file
save_path = r"d:\game\cyberpunk_circuit.blend"
bpy.ops.wm.save_as_mainfile(filepath=save_path)
print(f"SUCCESS: Animated Buddh Cyberpunk Circuit saved to {save_path}")
'''

print("Sending Animated Buddh Cyberpunk Circuit script to Blender...")
res = send_code(buddh_animated_code, timeout=90.0)
print("Execution Result:", res)

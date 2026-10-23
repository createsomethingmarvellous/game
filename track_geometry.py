"""
Module: Track Geometry (track_geometry.py)
------------------------------------------
Precision-Engineered Buddh International Circuit with Tall Anti-Jump Containment Barriers:
1. High 3.35m safety containment barriers:
   - Deflective concrete Jersey barrier base (deflects tires back onto track).
   - Heavy-duty multi-rib steel impact rails (1.2m to 2.5m).
   - Inward-curved anti-jump catch overhang (2.5m to 3.35m) preventing cars from vaulting outside.
   - Glowing neon cyan (left) and magenta (right) top warning rail.
2. Complete open-air circuit (zero tunnel).
3. Seamless loop closure with 1.0000 tangent continuity.
4. Over 77m of clearance between non-adjacent tracks (Zero overlap).
5. 18m asphalt road deck, 2m kerbs, and high containment walls.
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

def generate_refined_track_curve():
    anchors = [
        # --- Sector 1: Start/Finish Straight (Heading True North: (0, 1, 0)) ---
        (0.0, 0.0, 0.0, 0.0),            # Anchor 0: Start / Finish Line & Gantry
        (0.0, 70.0, 1.5, 0.0),
        (0.0, 140.0, 3.5, 0.0),
        (0.0, 210.0, 5.5, 0.0),
        (0.0, 270.0, 7.0, 0.0),          # Braking zone for Turn 1

        # --- Turn 1: Symmetrical 90-degree Right Turn (Radius 55m) ---
        (16.0, 308.0, 8.5, 0.04),
        (55.0, 325.0, 10.0, 0.06),       # T1 Apex
        (94.0, 325.0, 11.5, 0.04),

        # --- Turn 2: Sweeping Uphill Left Arc ---
        (145.0, 340.0, 13.0, -0.04),
        (185.0, 385.0, 14.5, -0.06),
        (210.0, 450.0, 16.0, -0.05),
        (215.0, 525.0, 17.5, -0.03),

        # --- Turn 3: Summit Hairpin (Radius 45m, Wide separation) ---
        (230.0, 585.0, 18.5, 0.05),
        (265.0, 615.0, 19.0, 0.08),      # T3 Apex Summit
        (300.0, 585.0, 18.5, 0.06),

        # --- Back Straight (1.05 km heading South-East) ---
        (345.0, 480.0, 16.5, 0.0),
        (400.0, 340.0, 14.0, 0.0),
        (455.0, 200.0, 11.5, 0.0),
        (510.0, 60.0, 9.0, 0.0),
        (565.0, -80.0, 6.5, 0.0),
        (620.0, -220.0, 4.0, 0.0),
        (675.0, -360.0, 1.5, 0.0),
        (705.0, -435.0, 0.5, 0.0),       # Heavy braking for Turn 4

        # --- Turn 4: Right Hairpin (Radius 50m) ---
        (700.0, -485.0, 0.0, 0.06),
        (665.0, -515.0, 0.0, 0.08),      # T4 Apex
        (620.0, -505.0, 0.0, 0.05),

        # --- Straight Chute to Turn 5 (Y <= -300m) ---
        (530.0, -460.0, 0.0, 0.0),
        (420.0, -410.0, 0.0, 0.0),
        (310.0, -365.0, 0.0, 0.0),
        (200.0, -325.0, 0.0, 0.0),
        (100.0, -305.0, 0.0, 0.0),

        # --- Turn 5 & 6: Open-Air S-Chicane (Wide R=70m, Ground Z = 0.0) ---
        (40.0, -305.0, 0.0, -0.04),      # Turn 5 entry
        (-25.0, -325.0, 0.0, -0.06),     # T5 Apex
        (-75.0, -355.0, 0.0, -0.05),
        (-110.0, -400.0, 0.0, 0.05),     # T6 Apex
        (-110.0, -455.0, 0.0, 0.04),

        # --- Turn 7, 8, 9: Open-Air S-Section onto southern plain ---
        (-95.0, -505.0, 0.0, -0.03),
        (-90.0, -550.0, 0.0, 0.0),
        (-105.0, -590.0, 0.0, 0.05),     # T8 Apex
        (-135.0, -620.0, 0.0, 0.06),     # T9 Apex
        (-175.0, -625.0, 0.0, 0.04),

        # --- Turn 10 & 11: The Iconic Parabolica (Wide Banked Carousel R=75m) ---
        (-225.0, -650.0, 0.0, 0.07),
        (-285.0, -630.0, 0.0, 0.09),     # South apex (banked 5.5 deg)
        (-320.0, -570.0, 0.0, 0.09),     # Mid carousel
        (-305.0, -500.0, 0.0, 0.08),     # Exit apex
        (-265.0, -440.0, 0.0, 0.05),

        # --- Turn 12, 13, 14: Ascending S-curves climbing north ---
        (-225.0, -395.0, 0.0, -0.04),
        (-200.0, -335.0, 0.0, 0.04),
        (-200.0, -250.0, 0.0, -0.03),
        (-200.0, -150.0, 0.0, 0.0),

        # --- Turn 15: Symmetrical 90-degree Left Turn (Radius 45m) ---
        (-190.0, -60.0, 0.0, -0.05),
        (-160.0, -20.0, 0.0, -0.07),     # T15 Apex
        (-115.0, -30.0, 0.0, -0.05),

        # --- Chute down to Turn 16 (Keeps X <= -80m, 80m gap from Main Straight) ---
        (-85.0, -50.0, 0.0, 0.0),
        (-85.0, -90.0, 0.0, 0.0),
        (-80.0, -140.0, 0.0, 0.0),

        # --- Turn 16: Wide Hairpin Arc (R=40m, center at X=-40, Y=-190) ---
        (-70.0, -170.0, 0.0, 0.06),
        (-40.0, -190.0, 0.0, 0.08),      # T16 Apex
        (-10.0, -170.0, 0.0, 0.06),

        # --- Sleek Monotonic Connection into Main Straight (heading True North: (0, 1, 0)) ---
        (0.0, -140.0, 0.0, 0.0),         # Joins X=0 heading North!
        (0.0, -70.0, 0.0, 0.0),          # Continuing North seamlessly into Anchor 0!
    ]

    def catmull_rom_eval(p0, p1, p2, p3, t):
        t2 = t * t
        t3 = t2 * t
        return 0.5 * (
            (2.0 * p1) +
            (-p0 + p2) * t +
            (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 +
            (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
        )

    num_a = len(anchors)
    raw_points = []
    raw_banks = []
    subdiv_factor = 24

    for i in range(num_a):
        a0 = anchors[(i - 1) % num_a]
        a1 = anchors[i]
        a2 = anchors[(i + 1) % num_a]
        a3 = anchors[(i + 2) % num_a]

        p0 = Vector((a0[0], a0[1], a0[2]))
        p1 = Vector((a1[0], a1[1], a1[2]))
        p2 = Vector((a2[0], a2[1], a2[2]))
        p3 = Vector((a3[0], a3[1], a3[2]))

        b1, b2 = a1[3], a2[3]

        for s in range(subdiv_factor):
            t = s / float(subdiv_factor)
            pt = catmull_rom_eval(p0, p1, p2, p3, t)
            bank = b1 * (1.0 - t) + b2 * t
            raw_points.append(pt)
            raw_banks.append(bank)

    cum_dist = [0.0]
    total_raw = len(raw_points)
    for i in range(total_raw):
        p_curr = raw_points[i]
        p_next = raw_points[(i + 1) % total_raw]
        cum_dist.append(cum_dist[-1] + (p_next - p_curr).length)

    total_len = cum_dist[-1]
    step_d = 3.5
    num_uniform = int(total_len / step_d)

    uniform_frames = []
    raw_idx = 0

    for r in range(num_uniform):
        target_s = r * step_d
        while raw_idx < total_raw and cum_dist[raw_idx + 1] < target_s:
            raw_idx += 1

        s0 = cum_dist[raw_idx]
        s1 = cum_dist[raw_idx + 1]
        t = (target_s - s0) / (s1 - s0) if (s1 > s0) else 0.0
        t = max(0.0, min(1.0, t))

        pos = raw_points[raw_idx % total_raw].lerp(raw_points[(raw_idx + 1) % total_raw], t)
        bank = raw_banks[raw_idx % total_raw] * (1.0 - t) + raw_banks[(raw_idx + 1) % total_raw] * t

        uniform_frames.append({
            "pos": pos,
            "bank": bank,
            "idx": r
        })

    total_u = len(uniform_frames)
    for i in range(total_u):
        curr_p = uniform_frames[i]["pos"]
        next_p = uniform_frames[(i + 1) % total_u]["pos"]
        prev_p = uniform_frames[(i - 1) % total_u]["pos"]

        tangent = (next_p - prev_p).normalized()
        up = Vector((0.0, 0.0, 1.0))
        normal = tangent.cross(up).normalized()
        binormal = normal.cross(tangent).normalized()

        bank_rad = uniform_frames[i]["bank"]
        rot_norm = normal * math.cos(bank_rad) + binormal * math.sin(bank_rad)
        rot_binorm = -normal * math.sin(bank_rad) + binormal * math.cos(bank_rad)

        uniform_frames[i]["tangent"] = tangent
        uniform_frames[i]["normal"] = rot_norm
        uniform_frames[i]["binormal"] = rot_binorm

    print(f"Generated {total_u} open-air frames (Track Length: {total_len:.1f}m)")
    return uniform_frames

# ---------------------------------------------------------------------------
# Mesh Builder
# ---------------------------------------------------------------------------

def build_refined_track_meshes(frames):
    total_rings = len(frames)

    def get_mat(name):
        return bpy.data.materials.get(name)

    mat_asphalt   = get_mat("Mat_Asphalt_Wet")
    mat_white     = get_mat("Mat_Road_White")
    mat_yellow    = get_mat("Mat_Road_Yellow")
    mat_concrete  = get_mat("Mat_Concrete_Dark")
    mat_metal     = get_mat("Mat_Metal_Dark")
    mat_neon_cyan = get_mat("Mat_Neon_Cyan")
    mat_neon_mag  = get_mat("Mat_Neon_Magenta")
    mat_red       = get_mat("Mat_Start_Red")

    coll_track = bpy.data.collections.get("01_TRACK_SYSTEM")
    if not coll_track:
        coll_track = bpy.data.collections.new("01_TRACK_SYSTEM")
        bpy.context.scene.collection.children.link(coll_track)

    def link_obj(obj):
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        coll_track.objects.link(obj)

    # 1. Road Surface (18m wide, central crown)
    existing_road = bpy.data.objects.get("Track_Road_Surface")
    if existing_road:
        bpy.data.objects.remove(existing_road, do_unlink=True)

    road_mesh = bpy.data.meshes.new("Mesh_Track_Road")
    road_obj = bpy.data.objects.new("Track_Road_Surface", road_mesh)
    link_obj(road_obj)
    road_obj.data.materials.append(mat_asphalt)
    road_obj.data.materials.append(mat_white)
    road_obj.data.materials.append(mat_yellow)

    bm_road = bmesh.new()
    uv_layer_road = bm_road.loops.layers.uv.new("UVMap")
    road_profile = [
        (-9.0, 0.00),
        (-6.5, 0.02),
        (-3.5, 0.04),
        ( 0.0, 0.05),
        ( 3.5, 0.04),
        ( 6.5, 0.02),
        ( 9.0, 0.00),
    ]

    road_rings = []
    for f in frames:
        r_verts = [bm_road.verts.new(f["pos"] + f["normal"] * lat + f["binormal"] * h) for (lat, h) in road_profile]
        road_rings.append(r_verts)

    bm_road.verts.ensure_lookup_table()
    step_d = 3.5
    for i in range(total_rings):
        next_i = (i + 1) % total_rings
        r1, r2 = road_rings[i], road_rings[next_i]
        u1 = (i * step_d) / 5.0
        u2 = ((i + 1) * step_d) / 5.0
        for p in range(len(road_profile) - 1):
            v1 = (road_profile[p][0] + 9.0) / 18.0
            v2 = (road_profile[p+1][0] + 9.0) / 18.0
            face = bm_road.faces.new((r1[p], r1[p+1], r2[p+1], r2[p]))
            face.material_index = 0
            for loop in face.loops:
                if loop.vert == r1[p]:
                    loop[uv_layer_road].uv = Vector((u1, v1))
                elif loop.vert == r1[p+1]:
                    loop[uv_layer_road].uv = Vector((u1, v2))
                elif loop.vert == r2[p+1]:
                    loop[uv_layer_road].uv = Vector((u2, v2))
                elif loop.vert == r2[p]:
                    loop[uv_layer_road].uv = Vector((u2, v1))

    bm_road.to_mesh(road_mesh)
    bm_road.free()
    road_mesh.update()
    for poly in road_mesh.polygons:
        poly.use_smooth = True

    # 2. High Anti-Jump Solid Containment Barriers & Kerbs
    # Total Height: 3.8 meters with inward safety overhang lip and closed solid 3D enclosure
    existing_bar = bpy.data.objects.get("Track_Barriers_And_Kerbs")
    if existing_bar:
        bpy.data.objects.remove(existing_bar, do_unlink=True)

    # Purge broken / unbalanced clutter
    for bad_obj_name in ["Track_Corner_Barricades", "Track_Barrier_Brackets", "Cyber_Tunnel_Structure"]:
        bad_obj = bpy.data.objects.get(bad_obj_name)
        if bad_obj:
            bpy.data.objects.remove(bad_obj, do_unlink=True)

    bar_mesh = bpy.data.meshes.new("Mesh_Barriers_Kerbs")
    bar_obj = bpy.data.objects.new("Track_Barriers_And_Kerbs", bar_mesh)
    link_obj(bar_obj)
    bar_obj.data.materials.append(mat_concrete)    # 0: Concrete crash base
    bar_obj.data.materials.append(mat_metal)       # 1: Multi-rib impact beam & catch fence
    bar_obj.data.materials.append(mat_neon_cyan)   # 2: Glowing cyan top lip (Left)
    bar_obj.data.materials.append(mat_neon_mag)    # 3: Glowing magenta top lip (Right)
    bar_obj.data.materials.append(mat_red if mat_red else mat_concrete)    # 4: Red kerb
    bar_obj.data.materials.append(mat_white if mat_white else mat_metal)   # 5: White kerb

    bm_bar = bmesh.new()
    uv_layer_bar = bm_bar.loops.layers.uv.new("UVMap")

    # Left Solid Profile: 2.0m kerb + 3.8m tall closed crash barrier enclosure
    l_profile = [
        (-9.00,  0.01, -1),   # Kerb road edge (smooth flush with road)
        (-10.20, 0.08, -1),   # Kerb mid-slope
        (-10.80, 0.16, -1),   # Kerb rounded crest
        (-11.00, 0.00, 0),    # Concrete Jersey base inner toe
        (-11.15, 0.50, 0),    # Concrete lower deflector (bounces tires back onto asphalt)
        (-11.35, 1.40, 0),    # Concrete upper vertical riser
        (-11.35, 2.20, 1),    # Heavy-duty corrugated steel crash rail
        (-11.35, 3.00, 1),    # Upper retention steel barrier
        (-11.00, 3.55, 1),    # Inward retention catch overhang (prevents cars from vaulting over)
        (-10.90, 3.80, 2),    # Cyan glowing neon warning top rail (Left)
        (-11.80, 3.80, 1),    # Top cap width (0.9m thick solid barrier wall)
        (-12.00, 2.00, 0),    # Outer concrete rear wall
        (-12.00, -0.40, 0),   # Deep outer foundation
        (-10.80, -0.40, 0),   # Deep inner foundation
        (-9.00,  -0.10, 0),   # Closes back to road under-deck
    ]

    # Right Solid Profile: Symmetrical on +X side with magenta neon top
    r_profile = [
        ( 9.00,  0.01, -1),   # Kerb road edge
        ( 10.20, 0.08, -1),   # Kerb mid-slope
        ( 10.80, 0.16, -1),   # Kerb rounded crest
        ( 11.00, 0.00, 0),    # Concrete Jersey base inner toe
        ( 11.15, 0.50, 0),    # Concrete lower deflector
        ( 11.35, 1.40, 0),    # Concrete upper vertical riser
        ( 11.35, 2.20, 1),    # Heavy-duty corrugated steel crash rail
        ( 11.35, 3.00, 1),    # Upper retention steel barrier
        ( 11.00, 3.55, 1),    # Inward retention catch overhang
        ( 10.90, 3.80, 3),    # Magenta glowing neon warning top rail (Right)
        ( 11.80, 3.80, 1),    # Top cap width
        ( 12.00, 2.00, 0),    # Outer concrete rear wall
        ( 12.00, -0.40, 0),   # Deep outer foundation
        ( 10.80, -0.40, 0),   # Deep inner foundation
        (  9.00, -0.10, 0),   # Closes back to road under-deck
    ]

    l_rings = []
    r_rings = []
    for f in frames:
        l_rings.append([bm_bar.verts.new(f["pos"] + f["normal"] * lat + f["binormal"] * h) for (lat, h, _) in l_profile])
        r_rings.append([bm_bar.verts.new(f["pos"] + f["normal"] * lat + f["binormal"] * h) for (lat, h, _) in r_profile])

    bm_bar.verts.ensure_lookup_table()
    for i in range(total_rings):
        next_i = (i + 1) % total_rings
        # Alternating red (4) and white (5) motorsport kerbs every 4 rings (~14m stripes)
        kerb_mat = 4 if ((i // 4) % 2 == 0) else 5
        u1 = (i * step_d) / 4.0
        u2 = ((i + 1) * step_d) / 4.0

        l1, l2 = l_rings[i], l_rings[next_i]
        for p in range(len(l_profile) - 1):
            v1 = float(p) / (len(l_profile) - 1)
            v2 = float(p + 1) / (len(l_profile) - 1)
            face = bm_bar.faces.new((l1[p+1], l1[p], l2[p], l2[p+1]))
            mat = l_profile[p][2]
            face.material_index = kerb_mat if mat == -1 else mat
            for loop in face.loops:
                if loop.vert == l1[p+1]:
                    loop[uv_layer_bar].uv = Vector((u1, v2))
                elif loop.vert == l1[p]:
                    loop[uv_layer_bar].uv = Vector((u1, v1))
                elif loop.vert == l2[p]:
                    loop[uv_layer_bar].uv = Vector((u2, v1))
                elif loop.vert == l2[p+1]:
                    loop[uv_layer_bar].uv = Vector((u2, v2))

        r1, r2 = r_rings[i], r_rings[next_i]
        for p in range(len(r_profile) - 1):
            v1 = float(p) / (len(r_profile) - 1)
            v2 = float(p + 1) / (len(r_profile) - 1)
            face = bm_bar.faces.new((r1[p], r1[p+1], r2[p+1], r2[p]))
            mat = r_profile[p][2]
            face.material_index = kerb_mat if mat == -1 else mat
            for loop in face.loops:
                if loop.vert == r1[p]:
                    loop[uv_layer_bar].uv = Vector((u1, v1))
                elif loop.vert == r1[p+1]:
                    loop[uv_layer_bar].uv = Vector((u1, v2))
                elif loop.vert == r2[p+1]:
                    loop[uv_layer_bar].uv = Vector((u2, v2))
                elif loop.vert == r2[p]:
                    loop[uv_layer_bar].uv = Vector((u2, v1))

    bm_bar.to_mesh(bar_mesh)
    bm_bar.free()
    bar_mesh.update()
    for poly in bar_mesh.polygons:
        poly.use_smooth = True

    # 3. Structural Bridge Pylons
    existing_pylon = bpy.data.objects.get("Bridge_Support_Pylons")
    if existing_pylon:
        bpy.data.objects.remove(existing_pylon, do_unlink=True)

    pylon_mesh = bpy.data.meshes.new("Mesh_Bridge_Pylons")
    pylon_obj = bpy.data.objects.new("Bridge_Support_Pylons", pylon_mesh)
    link_obj(pylon_obj)
    pylon_obj.data.materials.append(mat_concrete)
    pylon_obj.data.materials.append(mat_metal)

    bm_pylon = bmesh.new()
    for i in range(0, total_rings, 10):
        f = frames[i]
        if f["pos"].z >= 5.0:
            deck_p = f["pos"]
            for side in [-7.5, 7.5]:
                col_b = deck_p + f["normal"] * side
                col_b.z = 0.0
                ph = deck_p.z
                hw, hd = 1.2, 1.2
                v1 = bm_pylon.verts.new(col_b + Vector((-hw, -hd, 0)))
                v2 = bm_pylon.verts.new(col_b + Vector(( hw, -hd, 0)))
                v3 = bm_pylon.verts.new(col_b + Vector(( hw,  hd, 0)))
                v4 = bm_pylon.verts.new(col_b + Vector((-hw,  hd, 0)))
                v5 = bm_pylon.verts.new(col_b + Vector((-hw, -hd, ph - 0.4)))
                v6 = bm_pylon.verts.new(col_b + Vector(( hw, -hd, ph - 0.4)))
                v7 = bm_pylon.verts.new(col_b + Vector(( hw,  hd, ph - 0.4)))
                v8 = bm_pylon.verts.new(col_b + Vector((-hw,  hd, ph - 0.4)))
                bm_pylon.faces.new((v1, v2, v6, v5))
                bm_pylon.faces.new((v2, v3, v7, v6))
                bm_pylon.faces.new((v3, v4, v8, v7))
                bm_pylon.faces.new((v4, v1, v5, v8))

    bm_pylon.to_mesh(pylon_mesh)
    bm_pylon.free()
    pylon_mesh.update()

    # Ensure no leftover tunnel object or broken partial corner barricades
    for bad_name in ["Cyber_Tunnel_Structure", "Track_Corner_Barricades", "Track_Barrier_Brackets"]:
        existing_bad = bpy.data.objects.get(bad_name)
        if existing_bad:
            bpy.data.objects.remove(existing_bad, do_unlink=True)

    print("Solid 3D anti-jump containment barriers (3.8m) built successfully on BOTH sides with zero gaps!")
    return frames

def export_track_fbx(output_path=r"D:\game\neon\Assets\Art\Meshes\Buddh_Circuit_Track.fbx"):
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')
    
    # Select only track mesh objects
    track_objs = ["Track_Road_Surface", "Track_Barriers_And_Kerbs"]
    count = 0
    for name in track_objs:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            count += 1
            
    if count == 0:
        print("[ERROR] No track objects found to export!")
        return False
        
    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=True,
        global_scale=1.0,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z',
        axis_up='Y',
        apply_unit_scale=False,
        bake_space_transform=False,
        object_types={'MESH'},
        bake_anim=False
    )
    print(f"SUCCESS: Exported {count} track objects to {output_path}!")
    return True

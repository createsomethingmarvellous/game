"""
Generate the Buddh International Circuit (BIC) layout in Blender.
Configured for wide 4-car parallel racing, high-poly mesh, clean scene without generic terrain.
"""

from blender_client import send_code

circuit_code = r'''
import bpy
import bmesh
import math
from mathutils import Vector

# 1. Clean the scene completely
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for block in bpy.data.meshes:
    if block.users == 0:
        bpy.data.meshes.remove(block)
for block in bpy.data.materials:
    if block.users == 0:
        bpy.data.materials.remove(block)

# 2. Materials Setup (Dark Asphalt, Striped Kerbs, Glowing Sci-Fi ready accents)
def create_mat(name, base_color, metallic=0.0, roughness=0.5, emission=None, emission_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
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

mat_asphalt   = create_mat("Track_Asphalt", (0.04, 0.04, 0.045, 1.0), roughness=0.8)
mat_line      = create_mat("Track_WhiteLine", (0.95, 0.95, 0.95, 1.0), roughness=0.3)
mat_kerb_red  = create_mat("Track_Kerb_Red", (0.85, 0.02, 0.02, 1.0), roughness=0.4)
mat_kerb_wht  = create_mat("Track_Kerb_White", (0.95, 0.95, 0.95, 1.0), roughness=0.4)
mat_barrier   = create_mat("Track_Barrier_Metal", (0.15, 0.16, 0.18, 1.0), metallic=0.9, roughness=0.2)
mat_barrier_light = create_mat("Track_Barrier_Neon", (0.0, 0.8, 1.0, 1.0), emission=(0.0, 0.8, 1.0, 1.0), emission_strength=8.0)
mat_gantry    = create_mat("Gantry_Frame", (0.05, 0.05, 0.06, 1.0), metallic=0.9, roughness=0.2)
mat_red_light = create_mat("Gantry_RedLight", (1.0, 0.05, 0.05, 1.0), emission=(1.0, 0.05, 0.05, 1.0), emission_strength=15.0)

# Car colors for the 4 parallel racers
car_colors = [
    create_mat("Car_NeonCyan", (0.0, 0.85, 1.0, 1.0), metallic=0.7, roughness=0.2),
    create_mat("Car_FlameOrange", (1.0, 0.35, 0.0, 1.0), metallic=0.7, roughness=0.2),
    create_mat("Car_CyberPurple", (0.75, 0.05, 1.0, 1.0), metallic=0.7, roughness=0.2),
    create_mat("Car_AcidGreen", (0.15, 1.0, 0.1, 1.0), metallic=0.7, roughness=0.2),
]
mat_car_cockpit = create_mat("Car_Cockpit", (0.02, 0.02, 0.03, 1.0), metallic=0.95, roughness=0.1)
mat_car_wheel   = create_mat("Car_Wheel", (0.01, 0.01, 0.01, 1.0), roughness=0.9)

# 3. Exact Buddh International Circuit Waypoints (True to Diagram)
# Oriented North: Start straight heads NNW to Turn 1
waypoints = [
    # --- Main Start/Finish Straight ---
    Vector((0.0, 0.0, 4.0)),            # Start Line / Gantry position
    Vector((-35.0, 100.0, 7.5)),
    Vector((-70.0, 200.0, 11.0)),
    Vector((-105.0, 300.0, 14.5)),

    # --- Turn 1: 90 deg uphill right-hander ---
    Vector((-125.0, 355.0, 16.0)),      # T1 Entry
    Vector((-110.0, 375.0, 16.5)),      # T1 Apex
    Vector((-70.0, 375.0, 17.0)),       # T1 Exit

    # --- Turn 2: Sweeping uphill left curve ---
    Vector((-15.0, 385.0, 17.5)),
    Vector((35.0, 415.0, 18.5)),        # T2 Apex
    Vector((70.0, 470.0, 19.5)),

    # --- Turn 3: 135 deg sharp right hairpin at circuit summit ---
    Vector((95.0, 530.0, 21.0)),
    Vector((110.0, 560.0, 21.5)),       # T3 Apex summit
    Vector((125.0, 550.0, 21.0)),       # T3 Exit

    # --- Massive Long Back Straight (1.06 km blast downhill) ---
    Vector((155.0, 440.0, 17.0)),
    Vector((195.0, 300.0, 12.0)),
    Vector((235.0, 150.0, 6.0)),
    Vector((275.0, 0.0, 0.0)),
    Vector((315.0, -150.0, -6.0)),
    Vector((350.0, -280.0, -11.0)),

    # --- Turn 4: Sharp right-hander at bottom-right corner ---
    Vector((365.0, -345.0, -13.0)),     # T4 Entry
    Vector((350.0, -365.0, -13.5)),     # T4 Apex
    Vector((315.0, -355.0, -13.0)),     # T4 Exit

    # --- Straight / Chute heading WNW to Turn 5 ---
    Vector((250.0, -315.0, -10.0)),
    Vector((175.0, -270.0, -7.0)),
    Vector((95.0, -220.0, -4.0)),
    Vector((20.0, -175.0, -1.0)),

    # --- Turn 5 (left sweeper) & Turn 6 (sharp left) ---
    Vector((-35.0, -150.0, 0.0)),       # T5 Apex
    Vector((-75.0, -170.0, 1.0)),
    Vector((-105.0, -205.0, 1.5)),      # T6 Apex

    # --- Turn 7 (right flick) ---
    Vector((-95.0, -245.0, 1.0)),       # T7 Apex
    Vector((-92.0, -280.0, -0.5)),

    # --- Turn 8 & 9 (S-curves / Chicane) ---
    Vector((-98.0, -315.0, -2.5)),      # T8 Apex
    Vector((-120.0, -350.0, -5.0)),     # T9 Apex
    Vector((-125.0, -395.0, -8.0)),

    # --- Turn 10 & 11: Iconic Double-Apex Parabolica Carousel Loop ---
    Vector((-125.0, -450.0, -10.5)),    # T10 Entry
    Vector((-155.0, -485.0, -11.5)),    # T10 South Apex
    Vector((-200.0, -475.0, -11.0)),    # Banked carousel bowl
    Vector((-225.0, -430.0, -9.5)),     # T11 Apex
    Vector((-215.0, -375.0, -7.5)),     # T11 Exit

    # --- Turn 12 & 13: Quick Esses climbing north ---
    Vector((-180.0, -325.0, -4.5)),     # T12 Apex
    Vector((-150.0, -265.0, -1.5)),     # T13 Apex

    # --- Turn 14: Left Kink ---
    Vector((-162.0, -195.0, 1.0)),      # T14 Apex
    Vector((-158.0, -125.0, 3.5)),

    # --- Turn 15: Sharp 90 deg corner ---
    Vector((-155.0, -65.0, 5.0)),
    Vector((-130.0, -48.0, 5.5)),       # T15 Apex
    Vector((-95.0, -68.0, 4.5)),

    # --- Chute down-right to Turn 16 ---
    Vector((-55.0, -95.0, 3.5)),
    Vector((-20.0, -122.0, 2.5)),

    # --- Turn 16: Final right-hander into Main Straight ---
    Vector((8.0, -142.0, 2.0)),         # T16 Apex
    Vector((18.0, -120.0, 2.5)),        # T16 Exit
    Vector((12.0, -60.0, 3.2)),
]

# 4. Catmull-Rom Spline Interpolation
def catmull_rom(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        (2.0 * p1) +
        (-p0 + p2) * t +
        (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 +
        (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
    )

num_wp = len(waypoints)
subdivisions = 16
track_points = []

for i in range(num_wp):
    p0 = waypoints[(i - 1) % num_wp]
    p1 = waypoints[i]
    p2 = waypoints[(i + 1) % num_wp]
    p3 = waypoints[(i + 2) % num_wp]
    for s in range(subdivisions):
        t = s / subdivisions
        track_points.append(catmull_rom(p0, p1, p2, p3, t))

num_rings = len(track_points)
print(f"Generated {num_rings} precision track points for Buddh Circuit.")

# 5. Build Extra-Wide Track (20m tarmac for 4 parallel race cars)
track_mesh = bpy.data.meshes.new("Buddh_Track_Mesh")
track_obj = bpy.data.objects.new("Buddh_Racing_Circuit", track_mesh)
bpy.context.collection.objects.link(track_obj)

for m in [mat_asphalt, mat_line, mat_kerb_red, mat_kerb_wht, mat_barrier, mat_barrier_light]:
    track_obj.data.materials.append(m)

bm = bmesh.new()

# Cross Section Profile (Width: 20m pure tarmac + kerbs + barriers)
# Each car gets a full 5.0m width!
# (lateral_offset, height_offset, material_index)
profile = [
    # Left Outer Guardrail
    (-13.0, 1.4, 4),
    (-13.0, 0.8, 5),   # Glowing cyan neon accent strip
    (-13.0, 0.4, 4),
    (-12.8, 0.0, 4),
    # Left Kerb (2.0m wide)
    (-12.5, 0.15, 2),  # Alternating kerb material (red / white)
    (-10.2, 0.03, 2),
    # Left Edge Line
    (-10.0, 0.01, 1),
    # 4-Lane Tarmac (20 meters total: -10m to +10m)
    (-5.0, 0.04, 0),   # Lane 1
    ( 0.0, 0.06, 0),   # Track Center Camber
    ( 5.0, 0.04, 0),   # Lane 4
    # Right Edge Line
    ( 10.0, 0.01, 1),
    # Right Kerb (2.0m wide)
    ( 10.2, 0.03, 2),
    ( 12.5, 0.15, 2),
    # Right Outer Guardrail
    ( 12.8, 0.0, 4),
    ( 13.0, 0.4, 4),
    ( 13.0, 0.8, 5),   # Glowing cyan neon accent strip
    ( 13.0, 1.4, 4),
]

num_profile_pts = len(profile)
ring_verts = []

for i in range(num_rings):
    curr_pt = track_points[i]
    next_pt = track_points[(i + 1) % num_rings]
    prev_pt = track_points[(i - 1) % num_rings]

    tangent = (next_pt - prev_pt).normalized()
    up = Vector((0.0, 0.0, 1.0))
    normal = tangent.cross(up).normalized()
    binormal = normal.cross(tangent).normalized()

    # Dynamic banking in high speed turns
    curvature = (next_pt - 2.0 * curr_pt + prev_pt).length
    bank = math.sin(i / 12.0) * min(curvature * 0.12, 0.10)
    rot_normal = normal * math.cos(bank) + binormal * math.sin(bank)
    rot_binormal = -normal * math.sin(bank) + binormal * math.cos(bank)

    ring = []
    for (lat_off, h_off, _) in profile:
        v_pos = curr_pt + (rot_normal * lat_off) + (rot_binormal * h_off)
        vert = bm.verts.new(v_pos)
        ring.append(vert)
    ring_verts.append(ring)

bm.verts.ensure_lookup_table()

for i in range(num_rings):
    next_i = (i + 1) % num_rings
    r1 = ring_verts[i]
    r2 = ring_verts[next_i]

    # Kerb color alternates every 3 rings
    kerb_mat = 3 if ((i // 3) % 2 == 0) else 2

    for p in range(num_profile_pts - 1):
        face = bm.faces.new((r1[p], r1[p + 1], r2[p + 1], r2[p]))
        mat_idx = profile[p][2]
        face.material_index = kerb_mat if mat_idx == 2 else mat_idx

bm.to_mesh(track_mesh)
bm.free()
track_mesh.update()
for poly in track_mesh.polygons:
    poly.use_smooth = True

print("Wide 4-car Buddh Circuit track created successfully!")

# 6. Start/Finish Overhead Gantry (spanning all 4 lanes)
start_p = waypoints[0]
start_next = waypoints[1]
s_tangent = (start_next - start_p).normalized()
s_normal = s_tangent.cross(Vector((0, 0, 1))).normalized()

# Left pillar
bpy.ops.mesh.primitive_cube_add(size=1.0, location=start_p + s_normal * 13.5 + Vector((0, 0, 5.0)))
p1 = bpy.context.active_object
p1.name = "Gantry_Pillar_L"
p1.scale = (1.0, 1.0, 10.0)
p1.data.materials.append(mat_gantry)

# Right pillar
bpy.ops.mesh.primitive_cube_add(size=1.0, location=start_p - s_normal * 13.5 + Vector((0, 0, 5.0)))
p2 = bpy.context.active_object
p2.name = "Gantry_Pillar_R"
p2.scale = (1.0, 1.0, 10.0)
p2.data.materials.append(mat_gantry)

# Overhead Crossbar (28 meters span across all 4 lanes)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=start_p + Vector((0, 0, 10.0)))
bar = bpy.context.active_object
bar.name = "Gantry_Crossbar"
bar.scale = (1.2, 28.0, 1.6)
bar.data.materials.append(mat_gantry)

# 5 Formula-style starting lights
for idx in range(5):
    l_pos = start_p + s_normal * (idx * 2.2 - 4.4) + Vector((0, 0, 9.2))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.35, location=l_pos)
    light_obj = bpy.context.active_object
    light_obj.name = f"StartLight_{idx+1}"
    light_obj.data.materials.append(mat_red_light)

# 7. Spawn 4 Stylized Racing Cars Side-by-Side (Demonstrating 4-Car Parallel Space!)
def spawn_race_car(name, location, heading_tangent, mat_body):
    car_coll = bpy.data.collections.get("Parallel_4_Racing_Cars")
    if not car_coll:
        car_coll = bpy.data.collections.new("Parallel_4_Racing_Cars")
        bpy.context.scene.collection.children.link(car_coll)

    # Main aerodynamic body chassis
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location + Vector((0, 0, 0.45)))
    chassis = bpy.context.active_object
    chassis.name = f"{name}_Chassis"
    chassis.scale = (4.4, 2.0, 0.6)
    chassis.data.materials.append(mat_body)

    # Cockpit canopy
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location + Vector((0, 0, 0.85)))
    cockpit = bpy.context.active_object
    cockpit.name = f"{name}_Cockpit"
    cockpit.scale = (2.0, 1.2, 0.45)
    cockpit.data.materials.append(mat_car_cockpit)

    # Rear wing / spoiler
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location - heading_tangent * 2.1 + Vector((0, 0, 1.05)))
    wing = bpy.context.active_object
    wing.name = f"{name}_Wing"
    wing.scale = (0.5, 2.3, 0.1)
    wing.data.materials.append(mat_body)

    # Align rotation to track heading
    angle = math.atan2(heading_tangent.y, heading_tangent.x)
    for obj in [chassis, cockpit, wing]:
        obj.rotation_euler.z = angle - math.radians(90.0)

# Lane offsets for 4 cars in parallel: -7.5m, -2.5m, +2.5m, +7.5m
lane_offsets = [-7.5, -2.5, 2.5, 7.5]
car_names = ["Racer_1_Cyan", "Racer_2_Orange", "Racer_3_Purple", "Racer_4_Green"]

for i in range(4):
    car_pos = start_p + s_normal * lane_offsets[i] + s_tangent * 12.0
    spawn_race_car(car_names[i], car_pos, s_tangent, car_colors[i])

print("Spawned 4 race cars side-by-side on the starting grid!")

# 8. Cinematic Camera & Sun Light
bpy.ops.object.light_add(type='SUN', location=(100.0, 100.0, 300.0))
sun = bpy.context.active_object
sun.name = "Buddh_Sun_Light"
sun.data.energy = 4.5
sun.data.color = (1.0, 0.97, 0.92)
sun.rotation_euler = (math.radians(45.0), math.radians(25.0), math.radians(40.0))

# Camera placed right behind the 4 cars looking forward towards Turn 1
bpy.ops.object.camera_add(location=start_p - s_tangent * 22.0 + Vector((0, 0, 5.0)))
cam = bpy.context.active_object
cam.name = "Buddh_Grid_Camera"
# Aim towards cars
cam.rotation_euler = (math.radians(80.0), 0.0, math.atan2(s_tangent.y, s_tangent.x) - math.radians(90.0))
cam.data.lens = 24.0  # Ultra-wide cinematic view
bpy.context.scene.camera = cam

# Set viewport to Material Preview and Frame the circuit
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            override = {'window': window, 'area': area, 'region': region, 'screen': window.screen}
                            try:
                                with bpy.context.temp_override(**override):
                                    bpy.ops.view3d.view_all(use_all_regions=False)
                            except Exception:
                                pass

print("Buddh Circuit layout loaded live into Blender!")
'''

print("Sending Buddh Circuit to Blender...")
result = send_code(circuit_code, timeout=60.0)
print("Execution Result:", result)

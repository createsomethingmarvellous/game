"""
Generate a high-poly Grand Prix style racing track and massive landscape map in Blender.
Dispatched via Antigravity Live Bridge.
"""

import math
from blender_client import send_code

blender_code = r'''
import bpy
import bmesh
import math
from mathutils import Vector

# 1. Clean the entire scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Clean orphan data blocks
for block in bpy.data.meshes:
    if block.users == 0:
        bpy.data.meshes.remove(block)
for block in bpy.data.materials:
    if block.users == 0:
        bpy.data.materials.remove(block)

# 2. Materials Setup
def create_material(name, base_color, metallic=0.0, roughness=0.5, emission=None, emission_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = base_color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        if emission:
            # Blender 4+ has Emission Color and Emission Strength inputs
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = emission
                bsdf.inputs['Emission Strength'].default_value = emission_strength
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = emission
    return mat

mat_asphalt   = create_material("Track_Asphalt", (0.05, 0.05, 0.05, 1.0), roughness=0.85)
mat_line      = create_material("Track_WhiteLine", (0.92, 0.92, 0.92, 1.0), roughness=0.3)
mat_kerb_red  = create_material("Track_Kerb_Red", (0.85, 0.03, 0.03, 1.0), roughness=0.45)
mat_kerb_wht  = create_material("Track_Kerb_White", (0.92, 0.92, 0.95, 1.0), roughness=0.45)
mat_gravel    = create_material("Track_Gravel", (0.48, 0.38, 0.25, 1.0), roughness=0.95)
mat_barrier   = create_material("Track_Barrier", (0.75, 0.77, 0.80, 1.0), metallic=0.9, roughness=0.25)
mat_terrain   = create_material("Map_Terrain", (0.08, 0.22, 0.05, 1.0), roughness=0.9)
mat_gantry    = create_material("Gantry_Frame", (0.04, 0.04, 0.05, 1.0), metallic=0.8, roughness=0.3)
mat_red_light = create_material("Gantry_RedLight", (1.0, 0.05, 0.05, 1.0), emission=(1.0, 0.05, 0.05, 1.0), emission_strength=15.0)

# 3. Define Circuit Waypoints (High-Speed GP circuit with elevation changes)
waypoints = [
    Vector((0.0, -220.0, 0.0)),       # Main straight
    Vector((90.0, -220.0, 0.0)),
    Vector((180.0, -210.0, 2.0)),
    Vector((260.0, -170.0, 6.0)),     # Turn 1 sweeping right
    Vector((300.0, -80.0, 12.0)),     # Turn 2
    Vector((270.0, 10.0, 18.0)),      # Hill climb
    Vector((200.0, 60.0, 24.0)),      # Esses entry
    Vector((130.0, 40.0, 28.0)),      # Esses mid
    Vector((80.0, 100.0, 32.0)),      # Crest
    Vector((50.0, 180.0, 34.0)),      # Highest point
    Vector((-10.0, 220.0, 30.0)),     # High-altitude hairpin
    Vector((-80.0, 180.0, 24.0)),
    Vector((-130.0, 110.0, 17.0)),    # Downhill fast chute
    Vector((-170.0, 30.0, 12.0)),
    Vector((-140.0, -40.0, 8.0)),     # Reversing curve
    Vector((-190.0, -90.0, 6.0)),     # Chicane left
    Vector((-230.0, -140.0, 4.0)),    # Chicane right
    Vector((-250.0, -190.0, 2.0)),    # Final hairpin entry
    Vector((-210.0, -240.0, 0.5)),    # Final hairpin apex
    Vector((-120.0, -245.0, 0.0)),    # Exit onto start straight
]

# Catmull-Rom spline interpolation for silky smooth high-poly track
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
subdivisions_per_segment = 24
track_points = []

for i in range(num_wp):
    p0 = waypoints[(i - 1) % num_wp]
    p1 = waypoints[i]
    p2 = waypoints[(i + 1) % num_wp]
    p3 = waypoints[(i + 2) % num_wp]
    for s in range(subdivisions_per_segment):
        t = s / subdivisions_per_segment
        pt = catmull_rom(p0, p1, p2, p3, t)
        track_points.append(pt)

num_rings = len(track_points)
print(f"Generated {num_rings} smooth track cross-sections.")

# 4. Build High-Poly Track Mesh using BMesh
track_mesh = bpy.data.meshes.new("Track_Mesh")
track_obj = bpy.data.objects.new("Racing_Track", track_mesh)
bpy.context.collection.objects.link(track_obj)

# Add materials to track object
for m in [mat_asphalt, mat_line, mat_kerb_red, mat_kerb_wht, mat_gravel, mat_barrier]:
    track_obj.data.materials.append(m)

bm = bmesh.new()

# Cross-section profile offsets: (lateral_offset, height_offset, material_index)
# Track width: 14m total tarmac, plus kerbs, gravel runoffs, and safety barriers
profile = [
    # Left Guardrail (Armco)
    (-10.2, 1.2, 5),
    (-10.2, 0.4, 5),
    (-10.0, 0.0, 5),
    # Left Gravel Runoff
    (-7.8, 0.0, 4),
    # Left Kerb
    (-7.5, 0.12, 2),  # Material index swapped conditionally (red/white)
    (-6.5, 0.02, 2),
    # Left Edge Line
    (-6.3, 0.01, 1),
    # Main Tarmac (slight crown)
    (-3.0, 0.03, 0),
    ( 0.0, 0.05, 0),
    ( 3.0, 0.03, 0),
    # Right Edge Line
    ( 6.3, 0.01, 1),
    # Right Kerb
    ( 6.5, 0.02, 2),
    ( 7.5, 0.12, 2),
    # Right Gravel Runoff
    ( 7.8, 0.0, 4),
    (10.0, 0.0, 5),
    # Right Guardrail (Armco)
    (10.2, 0.4, 5),
    (10.2, 1.2, 5),
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

    # Mild banking on high curvature turns
    curvature = (next_pt - 2.0 * curr_pt + prev_pt).length
    bank_angle = math.sin(i / 10.0) * min(curvature * 0.1, 0.08)

    rot_normal = normal * math.cos(bank_angle) + binormal * math.sin(bank_angle)
    rot_binormal = -normal * math.sin(bank_angle) + binormal * math.cos(bank_angle)

    ring = []
    for (lat_off, h_off, _) in profile:
        v_pos = curr_pt + (rot_normal * lat_off) + (rot_binormal * h_off)
        vert = bm.verts.new(v_pos)
        ring.append(vert)
    ring_verts.append(ring)

bm.verts.ensure_lookup_table()

# Create faces between consecutive rings
for i in range(num_rings):
    next_i = (i + 1) % num_rings
    r1 = ring_verts[i]
    r2 = ring_verts[next_i]

    # Kerb color alternates every 4 rings (red / white)
    kerb_is_white = ((i // 4) % 2) == 0
    kerb_mat_idx = 3 if kerb_is_white else 2

    for p in range(num_profile_pts - 1):
        v1 = r1[p]
        v2 = r1[p + 1]
        v3 = r2[p + 1]
        v4 = r2[p]
        face = bm.faces.new((v1, v2, v3, v4))

        # Assign material based on profile zone
        mat_idx = profile[p][2]
        if mat_idx == 2:  # Kerb zone
            face.material_index = kerb_mat_idx
        else:
            face.material_index = mat_idx

bm.to_mesh(track_mesh)
bm.free()

track_mesh.update()
# Smooth shading for realistic reflection
for poly in track_mesh.polygons:
    poly.use_smooth = True

print("Track ribbon geometry created successfully!")

# 5. Create Big Map Landscape Terrain (1000m x 1000m)
terrain_mesh = bpy.data.meshes.new("Terrain_Mesh")
terrain_obj = bpy.data.objects.new("Big_Map_Landscape", terrain_mesh)
bpy.context.collection.objects.link(terrain_obj)
terrain_obj.data.materials.append(mat_terrain)

bm_terr = bmesh.new()
grid_res = 90
grid_size = 1100.0  # 1.1 km across
step = grid_size / (grid_res - 1)
half_size = grid_size / 2.0

grid_verts = []
for gy in range(grid_res):
    row = []
    y = -half_size + gy * step
    for gx in range(grid_res):
        x = -half_size + gx * step

        # Mountain ranges around borders + rolling hills
        dist_from_center = math.sqrt(x*x + y*y)
        hill1 = math.sin(x / 130.0) * math.cos(y / 130.0) * 35.0
        hill2 = math.cos(x / 75.0 + y / 90.0) * 18.0
        outer_mountains = max(0.0, (dist_from_center - 320.0) / 180.0) ** 2 * 45.0

        z = hill1 + hill2 + outer_mountains - 10.0

        # Depress terrain slightly near track center so track stands out cleanly
        if dist_from_center < 350.0:
            z = min(z, 15.0)

        vert = bm_terr.verts.new(Vector((x, y, z)))
        row.append(vert)
    grid_verts.append(row)

bm_terr.verts.ensure_lookup_table()

for gy in range(grid_res - 1):
    for gx in range(grid_res - 1):
        v1 = grid_verts[gy][gx]
        v2 = grid_verts[gy][gx + 1]
        v3 = grid_verts[gy + 1][gx + 1]
        v4 = grid_verts[gy + 1][gx]
        bm_terr.faces.new((v1, v2, v3, v4))

bm_terr.to_mesh(terrain_mesh)
bm_terr.free()
terrain_mesh.update()
for poly in terrain_mesh.polygons:
    poly.use_smooth = True

print("Big Map terrain created successfully!")

# 6. Start/Finish Gantry Arch (over main straight)
gantry_p = waypoints[0]
gantry_next = waypoints[1]
g_tangent = (gantry_next - gantry_p).normalized()
g_normal = g_tangent.cross(Vector((0, 0, 1))).normalized()

# Left pillar
bpy.ops.mesh.primitive_cube_add(size=1.0, location=gantry_p + g_normal * 10.0 + Vector((0, 0, 4.0)))
p1 = bpy.context.active_object
p1.name = "Gantry_Pillar_L"
p1.scale = (0.8, 0.8, 8.0)
p1.data.materials.append(mat_gantry)

# Right pillar
bpy.ops.mesh.primitive_cube_add(size=1.0, location=gantry_p - g_normal * 10.0 + Vector((0, 0, 4.0)))
p2 = bpy.context.active_object
p2.name = "Gantry_Pillar_R"
p2.scale = (0.8, 0.8, 8.0)
p2.data.materials.append(mat_gantry)

# Top crossbar
bpy.ops.mesh.primitive_cube_add(size=1.0, location=gantry_p + Vector((0, 0, 8.0)))
bar = bpy.context.active_object
bar.name = "Gantry_Crossbar"
bar.scale = (0.9, 21.0, 1.2)
bar.data.materials.append(mat_gantry)

# 5 Starting Red Lights
for l_idx in range(5):
    l_pos = gantry_p + g_normal * (l_idx * 1.8 - 3.6) + Vector((0, 0, 7.5))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.3, location=l_pos)
    light_obj = bpy.context.active_object
    light_obj.name = f"StartLight_{l_idx+1}"
    light_obj.data.materials.append(mat_red_light)

# 7. Cinematic Sun Lighting & Atmosphere
bpy.ops.object.light_add(type='SUN', location=(100.0, -100.0, 250.0))
sun = bpy.context.active_object
sun.name = "Track_Sun_Light"
sun.data.energy = 5.0
sun.data.color = (1.0, 0.96, 0.88)
sun.rotation_euler = (math.radians(45.0), math.radians(20.0), math.radians(50.0))

# 8. Cinematic Camera pointing down the Main Straight
bpy.ops.object.camera_add(location=gantry_p - g_tangent * 40.0 + Vector((0, 0, 3.5)))
cam = bpy.context.active_object
cam.name = "Cinematic_Track_Camera"
cam.rotation_euler = (math.radians(82.0), 0.0, math.radians(-90.0))
cam.data.lens = 28.0  # Wide cinematic focal length
bpy.context.scene.camera = cam

# Set 3D Viewport Shading to Material Preview or Rendered if possible
print("Big High-Poly Racing Track & Map generation complete!")
'''

print("Sending racing track generator to Blender...")
result = send_code(blender_code, timeout=45.0)
print("Execution Result:", result)

import bpy
import os
from mathutils import Vector

unity_fbx_path = r"D:\game\neon\Assets\Art\Meshes\SciFi_Vehicle.fbx"
glb_path = r"d:\game\free_sci-fi_vehicle_019_02_-_public_domain_cc0.glb"

# 1. Reset
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb_path)

# 2. Unparent all mesh objects keeping world transforms
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for m in mesh_objs:
    m.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

# 3. Remove non-mesh objects
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)

# 4. Rotate 180 degrees around Z axis so car naturally faces +Z in Unity
bpy.ops.object.select_all(action='SELECT')
bpy.ops.transform.rotate(value=3.141592653589793, orient_axis='Z', orient_type='GLOBAL')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 5. Join wheel submeshes into 6 clean wheels with origins centered at axle pivots
wheel_definitions = [
    ("Wheel_FL", "SFV_wheel_01.003|"),  # Front Left (X ~ -1.2, Y ~ -1.7 -> Unity X < 0, Z > 0)
    ("Wheel_FR", "SFV_wheel_01|"),       # Front Right (X ~ +1.2, Y ~ -1.7 -> Unity X > 0, Z > 0)
    ("Wheel_ML", "SFV_wheel_01.004|"),  # Mid-Front Left (X ~ -1.2, Y ~ -0.8 -> Unity X < 0, Z > 0)
    ("Wheel_MR", "SFV_wheel_01.001|"),  # Mid-Front Right (X ~ +1.2, Y ~ -0.8 -> Unity X > 0, Z > 0)
    ("Wheel_RL", "SFV_wheel_01.005|"),  # Rear Left (X ~ -1.2, Y ~ +2.1 -> Unity X < 0, Z < 0)
    ("Wheel_RR", "SFV_wheel_01.002|"),  # Rear Right (X ~ +1.2, Y ~ +2.1 -> Unity X > 0, Z < 0)
]

for new_name, prefix in wheel_definitions:
    parts = [o for o in bpy.data.objects if o.name.startswith(prefix)]
    if not parts:
        print(f"Warning: no parts found for {prefix}")
        continue
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    wheel = bpy.context.view_layer.objects.active
    wheel.name = new_name
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    print(f"Configured wheel '{wheel.name}' at location: {wheel.location}")

# 6. Export FBX to Unity
os.makedirs(os.path.dirname(unity_fbx_path), exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=unity_fbx_path,
    use_selection=False,
    bake_space_transform=True,
    apply_scale_options='FBX_SCALE_ALL',
    apply_unit_scale=False,
    global_scale=1.0
)
print("SUCCESS: Exported SciFi_Vehicle.fbx with forward orientation facing +Z!")

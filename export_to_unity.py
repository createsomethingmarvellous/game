"""
Export Assets to Unity Project with Correct Scale
--------------------------------------------------
Fixes FBX scale options so the 6-wheeled Sci-Fi vehicle exports
at true 1:1 real-world scale (5.59m long x 2.81m wide x 1.20m high).
"""

import bpy
import os

unity_mesh_dir = r"D:\game\neon\Assets\Art\Meshes"
os.makedirs(unity_mesh_dir, exist_ok=True)

# 1. Export Sci-Fi Vehicle at True 1:1 Scale
glb_path = r"d:\game\free_sci-fi_vehicle_019_02_-_public_domain_cc0.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb_path)

# Enhance neon emissive materials
mat_amber = bpy.data.materials.get("Material.004")
if mat_amber and mat_amber.node_tree:
    bsdf = mat_amber.node_tree.nodes.get("Principled BSDF")
    if bsdf and 'Emission Color' in bsdf.inputs:
        bsdf.inputs['Emission Color'].default_value = (1.0, 0.75, 0.1, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 12.0

mat_red = bpy.data.materials.get("Material.005")
if mat_red and mat_red.node_tree:
    bsdf = mat_red.node_tree.nodes.get("Principled BSDF")
    if bsdf and 'Emission Color' in bsdf.inputs:
        bsdf.inputs['Emission Color'].default_value = (1.0, 0.02, 0.02, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 15.0

bpy.ops.object.select_all(action='SELECT')
car_fbx_path = os.path.join(unity_mesh_dir, "SciFi_Vehicle.fbx")
print(f"Exporting Sci-Fi Vehicle at true 1:1 scale to {car_fbx_path}...")
bpy.ops.export_scene.fbx(
    filepath=car_fbx_path,
    use_selection=True,
    global_scale=1.0,
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y',
    apply_unit_scale=False,
    bake_space_transform=False,
    object_types={'MESH', 'EMPTY'},
    bake_anim=False
)
print("SUCCESS: Exported SciFi_Vehicle.fbx at true 5.59m scale.")

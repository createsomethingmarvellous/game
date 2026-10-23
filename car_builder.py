"""
Module 1: Car Builder (car_builder.py)
--------------------------------------
Integrates the user's high-detail 6-wheeled Sci-Fi vehicle:
`free_sci-fi_vehicle_019_02_-_public_domain_cc0.glb`

Features:
- Completely wipes `02_VEHICLES` and any existing vehicles/wheels before import (zero duplicates, zero dummy objects).
- Creates clean master root `Player_SciFi_Vehicle`.
- Imports GLB directly under `Player_SciFi_Vehicle`.
- Enhances materials with emissive neon headlights and red taillights.
- Exposes all 6 individual wheel hub empties for spinning animation.
"""

import bpy
import os
import math
from mathutils import Vector

def purge_all_vehicles():
    """Wipes any existing vehicles, wheels, and dummy parts completely."""
    # 1. Clean collection 02_VEHICLES
    coll = bpy.data.collections.get("02_VEHICLES")
    if coll:
        for obj in list(coll.objects):
            # Unlink and remove object
            for child in list(obj.children):
                child.parent = None
            if obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)

    # 2. Safety sweep for any unparented leftover car parts or dummy objects across the whole scene
    for obj in list(bpy.data.objects):
        name_lower = obj.name.lower()
        if (
            "dummy" in name_lower or
            "sketchfab" in name_lower or
            "sfv_wheel" in name_lower or
            name_lower.startswith("fed42ee7") or
            name_lower.startswith("rootnode") or
            name_lower.startswith("wheel_fl") or
            name_lower.startswith("wheel_fr") or
            name_lower.startswith("wheel_rl") or
            name_lower.startswith("wheel_rr") or
            name_lower.startswith("car_")
        ):
            try:
                for child in list(obj.children):
                    child.parent = None
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception as e:
                pass

    # 3. Purge orphaned meshes
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    print("Purge completed: All old vehicles and dummy parts removed.")

def build_dummy_car(location=(0, 0, 0)):
    """
    Main entry point: Cleans all vehicles, imports GLB,
    and returns (root_empty, list_of_6_wheels).
    """
    purge_all_vehicles()

    coll_name = "02_VEHICLES"
    coll = bpy.data.collections.get(coll_name)
    if not coll:
        coll = bpy.data.collections.new(coll_name)
        bpy.context.scene.collection.children.link(coll)

    glb_path = r"d:\game\free_sci-fi_vehicle_019_02_-_public_domain_cc0.glb"
    if not os.path.exists(glb_path):
        raise FileNotFoundError(f"Car file not found at {glb_path}")

    # Track new objects
    existing_objs = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb_path)
    new_objs = [o for o in bpy.data.objects if o not in existing_objs]

    # Move all new objects strictly into 02_VEHICLES
    for o in new_objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)

    # Create clean master root empty
    root = bpy.data.objects.new("Player_SciFi_Vehicle", None)
    root.empty_display_type = 'ARROWS'
    root.empty_display_size = 3.5
    root.location = location
    coll.objects.link(root)

    # Parent imported top empty to root
    imported_root = None
    for o in new_objs:
        if o.parent is None and o != root:
            imported_root = o
            break

    if imported_root:
        imported_root.parent = root
        imported_root.location = Vector((0.0, 0.0, 0.0))

    # Enhance emissive shaders
    mat_amber = bpy.data.materials.get("Material.004")
    if mat_amber and mat_amber.node_tree:
        bsdf = mat_amber.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = (1.0, 0.75, 0.1, 1.0)
                bsdf.inputs['Emission Strength'].default_value = 12.0
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = (1.0, 0.75, 0.1, 1.0)

    mat_red = bpy.data.materials.get("Material.005")
    if mat_red and mat_red.node_tree:
        bsdf = mat_red.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = (1.0, 0.02, 0.02, 1.0)
                bsdf.inputs['Emission Strength'].default_value = 15.0
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = (1.0, 0.02, 0.02, 1.0)

    # Collect the 6 wheel empties
    wheels = []
    for o in new_objs:
        if o.name.startswith("SFV_wheel_01") and o.type == 'EMPTY' and len(o.children) > 0 and 'Dupli' not in o.name:
            wheels.append(o)

    print(f"Successfully configured Player_SciFi_Vehicle with {len(wheels)} active wheels!")
    return root, wheels

if __name__ == "__main__":
    build_dummy_car()

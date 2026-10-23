"""
Update Car in Blend File (update_car_in_blend.py)
-------------------------------------------------
Executes total dummy car purge, imported sci-fi vehicle setup,
6-wheel animation, camera rigs, and renders verification stills.
"""

import sys
import os

workspace_dir = r"d:\game"
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import bpy
import car_builder
import car_animator
import camera_rig
import track_geometry

import importlib
importlib.reload(car_builder)
importlib.reload(car_animator)
importlib.reload(camera_rig)
importlib.reload(track_geometry)

print("--- 1. Getting Track Geometry Frames ---")
frames = track_geometry.generate_refined_track_curve()

print("--- 2. Purging Dummy Objects & Building Sci-Fi Car ---")
car_root, wheels = car_builder.build_dummy_car(location=(0, 0, 0))

print("--- 3. Keyframing 6-Wheel Driving Animation along Buddh Circuit ---")
car_animator.animate_car(car_root, wheels=wheels, frames=frames, total_frames=600)

print("--- 4. Attaching Chase & Cockpit Cameras ---")
chase_cam, cockpit_cam = camera_rig.setup_camera_rig(car_root)

# Set timeline to frame 1
bpy.context.scene.frame_set(1)
bpy.context.scene.camera = chase_cam

# Save blend file
save_path = r"d:\game\cyberpunk_circuit.blend"
bpy.ops.wm.save_as_mainfile(filepath=save_path)
print(f"SUCCESS: Saved updated vehicle to {save_path}")

# Render verification preview from Chase Cam
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.filepath = r"d:\game\scifi_car_preview.png"
bpy.ops.render.render(write_still=True)
print("Rendered chase camera preview to d:\\game\\scifi_car_preview.png")

# Render verification preview from Cockpit Cam
bpy.context.scene.camera = cockpit_cam
bpy.context.scene.render.filepath = r"d:\game\scifi_cockpit_preview.png"
bpy.ops.render.render(write_still=True)
print("Rendered cockpit camera preview to d:\\game\\scifi_cockpit_preview.png")

# Reset active camera to Chase Cam for the user
bpy.context.scene.camera = chase_cam
bpy.ops.wm.save_as_mainfile(filepath=save_path)
print("Saved final blend file with Chase Cam active.")

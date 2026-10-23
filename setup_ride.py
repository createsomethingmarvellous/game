"""
Master Orchestrator: Setup Ride (setup_ride.py)
-----------------------------------------------
Executes the modular pipeline:
1. car_builder.py  -> Builds the high-tech dummy race car.
2. car_animator.py -> Animates the car & wheels along the Buddh Circuit across 600 frames.
3. camera_rig.py   -> Configures 3rd-person chase and 1st-person cockpit cameras.
"""

from blender_client import send_code

code = r'''
import sys
import os

workspace_dir = r"d:\game"
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

# Import the 3 clean modular scripts
import car_builder
import car_animator
import camera_rig

# Reload modules in case of updates
import importlib
importlib.reload(car_builder)
importlib.reload(car_animator)
importlib.reload(camera_rig)

import bpy

print("--- Step 1: Building Dummy Race Car ---")
car_root, wheels = car_builder.build_dummy_car(location=(0, 0, 0))

print("--- Step 2: Animating Car Driving along Buddh Circuit ---")
car_animator.animate_car(car_root, wheels=wheels, total_frames=600)

print("--- Step 3: Setting Up Chase & Cockpit Camera Rig ---")
chase_cam, cockpit_cam = camera_rig.setup_camera_rig(car_root)

# Set timeline to frame 1
bpy.context.scene.frame_set(1)

# Save blend file
save_path = r"d:\game\cyberpunk_circuit.blend"
bpy.ops.wm.save_as_mainfile(filepath=save_path)
print(f"SUCCESS: Scene saved to {save_path}")

# Render quick preview from chase camera
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.filepath = r"d:\game\ride_preview.png"
bpy.ops.render.render(write_still=True)
print("Preview rendered to d:\\game\\ride_preview.png")
'''

print("Executing modular car & ride setup...")
res = send_code(code, timeout=90.0)
print("Result:", res)

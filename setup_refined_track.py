"""
Master Orchestrator: Setup Refined Track & Ride
------------------------------------------------
Rebuilds the circuit with FIA Grade-1 geometric refinement:
- True straights, circular arcs, uniform 3.5m quad density.
- Re-aligns start gantry, timing tower, and checkpoint gates.
- Re-animates dummy car and sets up chase camera.
"""

from blender_client import send_code

code = r'''
import sys
workspace_dir = r"d:\game"
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import track_geometry
import car_builder
import car_animator
import camera_rig

import importlib
importlib.reload(track_geometry)
importlib.reload(car_builder)
importlib.reload(car_animator)
importlib.reload(camera_rig)

import bpy
import math
from mathutils import Vector

print("--- Step 1: Generating Mathematically Refined Geometric Track ---")
frames = track_geometry.generate_refined_track_curve()
track_geometry.build_refined_track_meshes(frames)

print("--- Step 2: Re-aligning Racing Infrastructure & Navigation Guides ---")
s_frame = frames[0]
s_pos = s_frame["pos"]
s_tan = s_frame["tangent"]
s_norm = s_frame["normal"]

# Re-align Start Gantry
p1 = bpy.data.objects.get("Gantry_Pillar_Left")
p2 = bpy.data.objects.get("Gantry_Pillar_Right")
bar = bpy.data.objects.get("Gantry_Crossbeam")
if p1 and p2 and bar:
    p1.location = s_pos + s_norm * 12.0 + Vector((0, 0, 6.0))
    p2.location = s_pos - s_norm * 12.0 + Vector((0, 0, 6.0))
    bar.location = s_pos + Vector((0, 0, 11.5))
    bar.rotation_euler.z = math.atan2(s_tan.y, s_tan.x)

# Re-align Start Lights
mat_red = bpy.data.materials.get("Mat_Start_Red")
for idx in range(5):
    lamp = bpy.data.objects.get(f"StartLight_Red_{idx+1}")
    if lamp:
        lamp.location = s_pos + s_norm * (idx * 2.8 - 5.6) + Vector((0, 0, 10.6))

# Re-align Timing Tower
tower = bpy.data.objects.get("Timing_Tower_Main")
screen = bpy.data.objects.get("Timing_Tower_DigitalScreen")
if tower:
    tower.location = s_pos + s_norm * 17.0 + Vector((0, 0, 16.0))
if screen:
    screen.location = s_pos + s_norm * 14.6 + Vector((0, 0, 22.0))

# Re-align 8 Checkpoint Gates along the refined frames
total_f = len(frames)
cp_indices = [int(total_f * (i / 8.0)) for i in range(8)]
for cp_idx, r_idx in enumerate(cp_indices):
    cp_f = frames[r_idx]
    gate = bpy.data.objects.get(f"Checkpoint_Gate_{cp_idx+1:02d}")
    if gate:
        gate.location = cp_f["pos"] + Vector((0, 0, 9.0))
        gate.rotation_euler.z = math.atan2(cp_f["tangent"].y, cp_f["tangent"].x)

    cp_empty = bpy.data.objects.get(f"Checkpoint_{cp_idx+1:02d}")
    if cp_empty:
        cp_empty.location = cp_f["pos"] + Vector((0, 0, 1.5))
        cp_empty.rotation_euler.z = math.atan2(cp_f["tangent"].y, cp_f["tangent"].x)

# Re-align Start_Finish Empty
sf = bpy.data.objects.get("Start_Finish")
if sf:
    sf.location = s_pos
    sf.rotation_euler.z = math.atan2(s_tan.y, s_tan.x)

# Rebuild AI_Racing_Line directly from the refined track centerline
existing_ai = bpy.data.objects.get("AI_Racing_Line")
if existing_ai:
    bpy.data.objects.remove(existing_ai, do_unlink=True)
old_curve = bpy.data.curves.get("Curve_AI_Racing_Line")
if old_curve:
    bpy.data.curves.remove(old_curve)

curve_data = bpy.data.curves.new("Curve_AI_Racing_Line", type='CURVE')
curve_data.dimensions = '3D'
curve_data.resolution_u = 6
curve_data.bevel_depth = 0.08
curve_data.bevel_resolution = 2

spline = curve_data.splines.new('BEZIER')
spline.use_cyclic_u = True
sample_indices = list(range(0, total_f, 8))
spline.bezier_points.add(len(sample_indices) - 1)

for i, idx in enumerate(sample_indices):
    f = frames[idx]
    bp = spline.bezier_points[i]
    bp.co = f["pos"] + f["binormal"] * 0.15
    bp.handle_left_type = 'AUTO'
    bp.handle_right_type = 'AUTO'

ai_obj = bpy.data.objects.new("AI_Racing_Line", curve_data)
mat_cyan = bpy.data.materials.get("Mat_Neon_Cyan")
if mat_cyan:
    ai_obj.data.materials.append(mat_cyan)

coll_nav = bpy.data.collections.get("04_NAVIGATION_GUIDES")
if not coll_nav:
    coll_nav = bpy.data.collections.get("03_NAVIGATION_GUIDES")
if coll_nav:
    coll_nav.objects.link(ai_obj)

# Re-align 8 Grid Slots (4-wide in 2 rows on the 18m road surface)
lane_offsets = [-6.75, -2.25, 2.25, 6.75]
for i in range(4):
    g1 = bpy.data.objects.get(f"Player_Grid_{i+1:02d}")
    if g1:
        g1.location = s_pos + s_norm * lane_offsets[i] + s_tan * -15.0 + Vector((0, 0, 0.1))
        g1.rotation_euler.z = math.atan2(s_tan.y, s_tan.x)

    g2 = bpy.data.objects.get(f"Player_Grid_{i+5:02d}")
    if g2:
        g2.location = s_pos + s_norm * lane_offsets[i] + s_tan * -30.0 + Vector((0, 0, 0.1))
        g2.rotation_euler.z = math.atan2(s_tan.y, s_tan.x)

print("--- Step 3: Building & Animating Dummy Car ---")
car_root, wheels = car_builder.build_dummy_car(location=(0, 0, 0))
car_animator.animate_car(car_root, wheels=wheels, frames=frames, total_frames=600)

print("--- Step 4: Configuring Camera Rig ---")
chase_cam, cockpit_cam = camera_rig.setup_camera_rig(car_root)

# Set scene timeline to frame 1
bpy.context.scene.frame_set(1)

# Save file
save_path = r"d:\game\cyberpunk_circuit.blend"
bpy.ops.wm.save_as_mainfile(filepath=save_path)
print(f"SUCCESS: Saved geometrically refined circuit to {save_path}")

# Render verification preview
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.filepath = r"d:\game\refined_ride_preview.png"
bpy.ops.render.render(write_still=True)
print("Rendered verification preview to d:\\game\\refined_ride_preview.png")
'''

print("Executing refined track build...")
res = send_code(code, timeout=90.0)
print("Result:", res)

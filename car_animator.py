"""
Module 2: Car Animator (car_animator.py)
----------------------------------------
Animates Player_SciFi_Vehicle along the refined circuit over 600 frames:
- Constant-speed path traversal and chassis banking.
- Dynamic front & mid wheel steering into track corners (Ackermann yaw).
- Realistic 6-wheel spin roll rotation around local axles.
- Sets Euler rotation order to 'ZXY' (steer Z, then spin X) so Blender evaluates both.
"""

import bpy
import math
from mathutils import Vector, Matrix

def animate_car(car_root, wheels=None, frames=None, total_frames=600, key_step=2):
    if not frames:
        import track_geometry
        frames = track_geometry.generate_refined_track_curve()

    total_rings = len(frames)

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.fps = 24

    wheel_radius = 0.40  # Sci-Fi vehicle wheel radius is 0.40m

    # 1. Clear old animation data
    if car_root.animation_data:
        car_root.animation_data_clear()

    if wheels:
        for w in wheels:
            if w.animation_data:
                w.animation_data_clear()
            # Set to ZXY Euler: Z steers first, X spins around the steered axle
            w.rotation_mode = 'ZXY'

    # Map wheels to axle roles: Front, Mid, Rear
    wheel_roles = {}
    if wheels:
        for w in wheels:
            name = w.name
            if name in ["SFV_wheel_01", "SFV_wheel_01.003"]:
                wheel_roles[w] = "FRONT"  # Full steering
            elif name in ["SFV_wheel_01.001", "SFV_wheel_01.004"]:
                wheel_roles[w] = "MID"    # 25% steering (6x6 scrub reduction)
            else:
                wheel_roles[w] = "REAR"   # Fixed forward (0% steer)

    speed_per_frame = 3.2  # meters per frame

    for f_idx in range(1, total_frames + 1, key_step):
        u = (f_idx - 1) / float(total_frames)
        idx_curr = int(u * total_rings) % total_rings
        idx_look1 = (idx_curr + 4) % total_rings
        idx_look2 = (idx_curr + 9) % total_rings

        f_curr = frames[idx_curr]
        f_look1 = frames[idx_look1]
        f_look2 = frames[idx_look2]

        # Vehicle position resting cleanly on tarmac
        car_pos = f_curr["pos"] + Vector((0, 0, 0.05))

        # Forward orientation (+Y forward)
        forward = (f_look1["pos"] - f_curr["pos"]).normalized()
        up_vec = Vector((0, 0, 1))
        side = forward.cross(up_vec).normalized()
        true_up = side.cross(forward).normalized()

        # Dynamic banking from geometric curvature
        bank = f_curr["bank"]
        rot_side = side * math.cos(bank) + true_up * math.sin(bank)
        rot_up   = -side * math.sin(bank) + true_up * math.cos(bank)

        # 3x3 orientation matrix (local forward +Y, up +Z, side +X)
        mat_rot = Matrix((
            (rot_side.x, forward.x, rot_up.x),
            (rot_side.y, forward.y, rot_up.y),
            (rot_side.z, forward.z, rot_up.z)
        ))

        car_root.location = car_pos
        car_root.rotation_euler = mat_rot.to_euler()

        car_root.keyframe_insert(data_path="location", frame=f_idx)
        car_root.keyframe_insert(data_path="rotation_euler", frame=f_idx)

        # Dynamic Steering Angle calculation from track curvature
        dir1 = (f_look1["pos"] - f_curr["pos"]).normalized()
        dir2 = (f_look2["pos"] - f_look1["pos"]).normalized()
        cross_z = dir1.x * dir2.y - dir1.y * dir2.x
        dot_f = max(-1.0, min(1.0, dir1.x * dir2.x + dir1.y * dir2.y))
        d_heading = math.atan2(cross_z, dot_f)

        # Steer angle: proportional to curvature, clamped to [-28 deg, +28 deg]
        max_steer = math.radians(28.0)
        steer_base = max(-max_steer, min(max_steer, d_heading * 22.0))

        # Spin angle: distance traveled divided by wheel radius
        spin_angle = (f_idx * speed_per_frame) / wheel_radius

        if wheels:
            for w in wheels:
                role = wheel_roles.get(w, "REAR")
                if role == "FRONT":
                    steer = steer_base
                elif role == "MID":
                    steer = steer_base * 0.25
                else:
                    steer = 0.0

                w.rotation_euler = (spin_angle, 0.0, steer)
                w.keyframe_insert(data_path="rotation_euler", frame=f_idx)

    print("Sci-Fi vehicle animated with active wheel spin & dynamic corner steering!")

if __name__ == "__main__":
    root = bpy.data.objects.get("Player_SciFi_Vehicle") or bpy.data.objects.get("Player_Dummy_Car")
    if root:
        animate_car(root)

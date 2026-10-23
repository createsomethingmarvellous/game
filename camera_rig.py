"""
Module 3: Camera Rig (camera_rig.py)
------------------------------------
Creates dynamic driving camera viewpoints attached to Player_Dummy_Car:
1. Cam_Chase_Car: 3rd-person chase camera riding behind the rear bumper.
2. Cam_Cockpit_View: 1st-person cockpit view looking over the hood/windshield.
Sets Cam_Chase_Car as the active scene camera.
"""

import bpy
import math
from mathutils import Vector, Euler

def setup_camera_rig(car_root):
    coll_name = "05_CAMERAS_AND_LIGHTS"
    coll = bpy.data.collections.get(coll_name)
    if not coll:
        coll = bpy.data.collections.get("04_CAMERAS_AND_LIGHTS")
    if not coll:
        coll = bpy.data.collections.new("05_CAMERAS_AND_LIGHTS")
        bpy.context.scene.collection.children.link(coll)

    def link_obj(obj):
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        coll.objects.link(obj)

    # 1. Cam_Chase_Car (3rd-Person Chase Cam behind Sci-Fi Vehicle)
    chase_cam_obj = bpy.data.objects.get("Cam_Chase_Car")
    if not chase_cam_obj:
        chase_cam_data = bpy.data.cameras.new("Cam_Chase_Car")
        chase_cam_data.lens = 22.0
        chase_cam_obj = bpy.data.objects.new("Cam_Chase_Car", chase_cam_data)
        link_obj(chase_cam_obj)

    chase_cam_obj.parent = car_root
    # Position: 7.2m behind car (-Y), 2.5m above road (+Z)
    chase_cam_obj.location = Vector((0.0, -7.2, 2.5))
    chase_cam_obj.rotation_euler = Euler((math.radians(82.0), 0.0, 0.0), 'XYZ')

    # 2. Cam_Cockpit_View (1st-Person In-Car Camera)
    cockpit_cam_obj = bpy.data.objects.get("Cam_Cockpit_View")
    if not cockpit_cam_obj:
        cockpit_cam_data = bpy.data.cameras.new("Cam_Cockpit_View")
        cockpit_cam_data.lens = 18.0
        cockpit_cam_obj = bpy.data.objects.new("Cam_Cockpit_View", cockpit_cam_data)
        link_obj(cockpit_cam_obj)

    cockpit_cam_obj.parent = car_root
    # Position inside cockpit
    cockpit_cam_obj.location = Vector((0.0, 0.35, 0.95))
    cockpit_cam_obj.rotation_euler = Euler((math.radians(88.0), 0.0, 0.0), 'XYZ')

    # Set Chase Cam as primary
    bpy.context.scene.camera = chase_cam_obj

    # Snap 3D Viewport to Camera View
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
                        space.region_3d.view_perspective = 'CAMERA'

    print("Camera Rig configured! Active camera: Cam_Chase_Car")
    return chase_cam_obj, cockpit_cam_obj

if __name__ == "__main__":
    root = bpy.data.objects.get("Player_SciFi_Vehicle") or bpy.data.objects.get("Player_Dummy_Car")
    if root:
        setup_camera_rig(root)

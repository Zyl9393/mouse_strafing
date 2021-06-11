bl_info = {
    "name": "Mouse Strafing",
    "description": "Strafe in the 3D View using the mouse.",
    "author": "Zyl",
    "version": (2, 1),
    "blender": (2, 92, 0),
    "category": "3D View"
}

import bpy
from . import mouse_strafing
from . import prefs

def unregister():
    mouse_strafing.unregister_keymaps()
    bpy.utils.unregister_class(prefs.MouseStrafingPreferences)
    bpy.utils.unregister_class(mouse_strafing.MouseStrafingOperator)
    bpy.utils.unregister_class(mouse_strafing.CameraStates)
    bpy.utils.unregister_class(mouse_strafing.CameraState)

def register():
    bpy.utils.register_class(mouse_strafing.CameraState)
    bpy.utils.register_class(mouse_strafing.CameraStates)
    bpy.types.Scene.mstrf_camera_save_states = bpy.props.PointerProperty(type = mouse_strafing.CameraStates, options = {"HIDDEN"})
    bpy.utils.register_class(mouse_strafing.MouseStrafingOperator)
    bpy.utils.register_class(prefs.MouseStrafingPreferences)
    mouse_strafing.register_keymaps()

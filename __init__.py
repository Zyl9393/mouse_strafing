bl_info = {
    "name": "Mouse Strafing",
    "description": "Strafe in the 3D View using the mouse.",
    "author": "Zyl",
    "version": (2, 2),
    "blender": (2, 92, 0),
    "category": "3D View"
}

import bpy
from . import mouse_strafing
from . import prefs

def unregister():
    mouse_strafing.unregister_keymaps()
    bpy.types.VIEW3D_PT_view3d_properties.remove(mouse_strafing.drawStrafeSensitivity)
    bpy.utils.unregister_class(prefs.MouseStrafingPreferences)
    bpy.utils.unregister_class(mouse_strafing.MouseStrafingOperator)
    bpy.utils.unregister_class(mouse_strafing.UnsetSceneStrafeSensitivity)
    bpy.utils.unregister_class(mouse_strafing.CameraStates)
    bpy.utils.unregister_class(mouse_strafing.CameraState)

def register():
    bpy.utils.register_class(mouse_strafing.CameraState)
    bpy.utils.register_class(mouse_strafing.CameraStates)
    bpy.utils.register_class(mouse_strafing.UnsetSceneStrafeSensitivity)
    bpy.utils.register_class(mouse_strafing.MouseStrafingOperator)
    bpy.utils.register_class(prefs.MouseStrafingPreferences)
    bpy.types.VIEW3D_PT_view3d_properties.append(mouse_strafing.drawStrafeSensitivity)
    mouse_strafing.register_keymaps()

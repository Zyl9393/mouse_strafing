bl_info = {
    "name": "Mouse Strafing",
    "description": "Strafe in the 3D View using the mouse.",
    "author": "Zyl",
    "version": (2, 0),
    "blender": (2, 80, 0),
    "category": "3D View"
}

import bpy
from . import mouse_strafing
from . import prefs

def unregister():
    mouse_strafing.unregister_keymaps()
    bpy.utils.unregister_class(prefs.MouseStrafingPreferences)
    bpy.utils.unregister_class(mouse_strafing.MouseStrafingOperator)

def register():
    bpy.utils.register_class(mouse_strafing.MouseStrafingOperator)
    bpy.utils.register_class(prefs.MouseStrafingPreferences)
    mouse_strafing.register_keymaps()

bl_info = {
    "name": "Mouse Strafing",
    "description": "Strafe in the 3D View using the mouse.",
    "author": "Zyl",
    "version": (2, 4),
    "blender": (2, 93, 0),
    "category": "3D View"
}

import bpy
from . import mouse_strafing
from . import prefs

def registerProperties():
    if not hasattr(bpy.types.Scene, "mstrf_camera_save_states"):
        bpy.types.Scene.mstrf_camera_save_states = bpy.props.PointerProperty(type = mouse_strafing.CameraStates, options = {"HIDDEN"})

def unregisterProperties():
    if hasattr(bpy.types.Scene, "mstrf_camera_save_states"):
        del bpy.types.Scene.mstrf_camera_save_states

def initAddonPreferences():
    p: prefs.MouseStrafingPreferences = bpy.context.preferences.addons[prefs.MouseStrafingPreferences.bl_idname].preferences
    if len(p.buttonBindings) == 0:
        p.buttonBindings.clear()
        b = p.buttonBindings.add()
        b.button1, b.button2, b.action = "lmb", "omit", "turnXY"
        b = p.buttonBindings.add()
        b.button1, b.button2, b.action = "rmb", "omit", "strafeXY"
        b = p.buttonBindings.add()
        b.button1, b.button2, b.action = "lmb", "rmb", "strafeXZ"
        b = p.buttonBindings.add()
        b.button1, b.button2, b.action = "mmb", "omit", "roll"
        bpy.context.preferences.use_preferences_save = True

def unregister():
    mouse_strafing.unregister_keymaps()
    unregisterProperties()

    bpy.utils.unregister_class(mouse_strafing.MouseStrafingOperator)

    bpy.utils.unregister_class(prefs.MouseStrafingPreferences)
    bpy.utils.unregister_class(mouse_strafing.CameraStates)
    bpy.utils.unregister_class(mouse_strafing.CameraState)

    bpy.utils.unregister_class(prefs.MoveButtonBindingDown)
    bpy.utils.unregister_class(prefs.MoveButtonBindingUp)
    bpy.utils.unregister_class(prefs.RemoveButtonBinding)
    bpy.utils.unregister_class(prefs.AddButtonBinding)

    bpy.utils.unregister_class(prefs.NavigationMouseButtonBinding)

def register():
    bpy.utils.register_class(prefs.NavigationMouseButtonBinding)

    bpy.utils.register_class(prefs.AddButtonBinding)
    bpy.utils.register_class(prefs.RemoveButtonBinding)
    bpy.utils.register_class(prefs.MoveButtonBindingUp)
    bpy.utils.register_class(prefs.MoveButtonBindingDown)

    bpy.utils.register_class(mouse_strafing.CameraState)
    bpy.utils.register_class(mouse_strafing.CameraStates)
    bpy.utils.register_class(prefs.MouseStrafingPreferences)

    bpy.utils.register_class(mouse_strafing.MouseStrafingOperator)

    registerProperties()
    initAddonPreferences()
    mouse_strafing.register_keymaps()

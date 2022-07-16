bl_info = {
    "name": "Mouse Strafing",
    "description": "Strafe in the 3D View using the mouse.",
    "author": "Zyl",
    "version": (2, 5),
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

addonClasses = [ \
    prefs.NavigationMouseButtonBinding, \
    prefs.AddButtonBinding, \
    prefs.RemoveButtonBinding, \
    prefs.MoveButtonBindingUp, \
    prefs.MoveButtonBindingDown, \
    mouse_strafing.CameraState, \
    mouse_strafing.CameraStates, \
    prefs.MouseStrafingPreferences, \
    mouse_strafing.MouseStrafingOperator, \
]

def register():
    for addonClass in addonClasses:
        bpy.utils.register_class(addonClass)
    registerProperties()
    initAddonPreferences()
    mouse_strafing.register_keymaps()


def unregister():
    mouse_strafing.unregister_keymaps()
    unregisterProperties()

    for addonClass in reversed(addonClasses):
        bpy.utils.unregister_class(addonClass)
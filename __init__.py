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
from .util import *

def setGear(self, value):
    self.mstrf_gear = value
    for scene in bpy.data.scenes:
        scene.mstrf_gear = value

def getGear(self):
    if self.mstrf_gear != 0.0:
        return self.mstrf_gear
    for scene in bpy.data.scenes:
        if scene.mstrf_gear != 0.0:
            return scene.mstrf_gear
    return 1.0

strafeSensitivitySourceOptions = [ \
    ("global", "Addon", "Use the mouse strafing sensitivity from the addon preferences", "NONE", 0), \
    ("file", "File", "Use a custom mouse strafing sensitivity for this file", "NONE", 1), \
    ("scene", "Scene", "Use a custom mouse strafing sensitivity for every scene in this file", "NONE", 2)]

def setStrafeSensitivitySource(self, value):
    oldValue = getStrafeSensitivitySource(self)
    if value == oldValue:
        return
    displayedValue = getStrafeSensitivity(self)
    self.mstrf_use_shared_scene_strafe_sensitivity = False
    for scene in bpy.data.scenes:
        scene.mstrf_use_shared_scene_strafe_sensitivity = False
    if value == 0:
        self.mstrf_use_scene_strafe_sensitivity = False
    elif value == 1:
        self.mstrf_use_shared_scene_strafe_sensitivity = True
        setStrafeSensitivity(self, displayedValue)
    elif value == 2:
        self.mstrf_use_scene_strafe_sensitivity = True
        setStrafeSensitivity(self, displayedValue)

def getStrafeSensitivitySource(self):
    sharingScene = findStrafeSensitivitySharingScene(self)
    if sharingScene is not None:
        return 1
    if self.mstrf_use_scene_strafe_sensitivity:
        return 2
    return 0

def registerProperties():
    if not hasattr(bpy.types.Scene, "mstrf_camera_save_states"):
        bpy.types.Scene.mstrf_camera_save_states = bpy.props.PointerProperty(type = mouse_strafing.CameraStates, options = {"HIDDEN"})
    if not hasattr(bpy.types.Scene, "mstrf_gear"):
        bpy.types.Scene.mstrf_gear = bpy.props.FloatProperty(default = 0.0, options = {"HIDDEN"})
    if not hasattr(bpy.types.Scene, "mstrf_gear_proxy"):
        bpy.types.Scene.mstrf_gear_proxy = bpy.props.FloatProperty(default = 1.0, options = {"HIDDEN"}, set = setGear, get = getGear)
    if not hasattr(bpy.types.Scene, "mstrf_sensitivity_strafe"):
        bpy.types.Scene.mstrf_sensitivity_strafe = bpy.props.FloatProperty(default = 1.0, options = {"HIDDEN"}, min = 0.001, soft_min = 0.01, max = 100.0, soft_max = 10.0, step = 1, precision = 3, description = "Strafe sensitivity multiplier for the current scene")
    if not hasattr(bpy.types.Scene, "mstrf_use_scene_strafe_sensitivity"):
        bpy.types.Scene.mstrf_use_scene_strafe_sensitivity = bpy.props.BoolProperty(name = "Use scene-specific Strafe Sensitivity", description = "Click to set a custom mouse strafe sensitivity for the current scene", options = {"HIDDEN"})
    if not hasattr(bpy.types.Scene, "mstrf_use_shared_scene_strafe_sensitivity"):
        bpy.types.Scene.mstrf_use_shared_scene_strafe_sensitivity = bpy.props.BoolProperty(name = "Use custom Strafe Sensitivity", description = "Click to set a custom mouse strafe sensitivity for all scenes", options = {"HIDDEN"})
    if not hasattr(bpy.types.Scene, "mstrf_strafe_sensitivity_source"):
        bpy.types.Scene.mstrf_strafe_sensitivity_source = bpy.props.EnumProperty(name = "Source", description = "Set where to read mouse strafing sensitivity from", items = strafeSensitivitySourceOptions, default = "global", \
            set = setStrafeSensitivitySource, get = getStrafeSensitivitySource)

def unregisterProperties():
    if hasattr(bpy.types.Scene, "mstrf_camera_save_states"):
        del bpy.types.Scene.mstrf_camera_save_states
    if hasattr(bpy.types.Scene, "mstrf_gear"):
        del bpy.types.Scene.mstrf_gear
    if hasattr(bpy.types.Scene, "mstrf_gear_proxy"):
        del bpy.types.Scene.mstrf_gear_proxy
    if hasattr(bpy.types.Scene, "mstrf_sensitivity_strafe"):
        del bpy.types.Scene.mstrf_sensitivity_strafe
    if hasattr(bpy.types.Scene, "mstrf_use_scene_strafe_sensitivity"):
        del bpy.types.Scene.mstrf_use_scene_strafe_sensitivity
    if hasattr(bpy.types.Scene, "mstrf_use_shared_scene_strafe_sensitivity"):
        del bpy.types.Scene.mstrf_use_shared_scene_strafe_sensitivity

def unregister():
    mouse_strafing.unregister_keymaps()
    bpy.types.VIEW3D_PT_view3d_properties.remove(mouse_strafing.drawStrafeSensitivity)
    unregisterProperties()
    bpy.utils.unregister_class(prefs.MouseStrafingPreferences)
    bpy.utils.unregister_class(mouse_strafing.MouseStrafingOperator)
    bpy.utils.unregister_class(mouse_strafing.CameraStates)
    bpy.utils.unregister_class(mouse_strafing.CameraState)

def register():
    bpy.utils.register_class(mouse_strafing.CameraState)
    bpy.utils.register_class(mouse_strafing.CameraStates)
    bpy.utils.register_class(mouse_strafing.MouseStrafingOperator)
    bpy.utils.register_class(prefs.MouseStrafingPreferences)
    registerProperties()
    bpy.types.VIEW3D_PT_view3d_properties.append(mouse_strafing.drawStrafeSensitivity)
    mouse_strafing.register_keymaps()

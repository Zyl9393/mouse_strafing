import bpy
from .prefs import MouseStrafingPreferences

def findStrafeSensitivitySharingScene(sceneOrContext) -> bpy.types.Scene:
    if type(sceneOrContext) is bpy.types.Scene and sceneOrContext.mstrf_use_shared_scene_strafe_sensitivity:
        return sceneOrContext
    if type(sceneOrContext) is bpy.types.Context and sceneOrContext.scene.mstrf_use_shared_scene_strafe_sensitivity:
        return sceneOrContext.scene
    else:
        for scene in bpy.data.scenes:
            if scene.mstrf_use_shared_scene_strafe_sensitivity:
                return scene
    return None

def getStrafeSensitivity(sceneOrContext):
    scene = sceneOrContext
    if type(sceneOrContext) is bpy.types.Context:
        scene = sceneOrContext.scene
    sharingScene = findStrafeSensitivitySharingScene(scene)
    if sharingScene is not None:
        return sharingScene.mstrf_sensitivity_strafe
    if scene.mstrf_use_scene_strafe_sensitivity:
        return scene.mstrf_sensitivity_strafe
    prefs: MouseStrafingPreferences = bpy.context.preferences.addons[MouseStrafingPreferences.bl_idname].preferences
    return prefs.sensitivityStrafeDefault

def setStrafeSensitivity(sceneOrContext, value: float):
    scene = sceneOrContext
    if type(sceneOrContext) is bpy.types.Context:
        scene = sceneOrContext.scene
    sharingScene = findStrafeSensitivitySharingScene(scene)
    if sharingScene is not None:
        sharingScene.mstrf_sensitivity_strafe = value
    elif scene.mstrf_use_scene_strafe_sensitivity:
        scene.mstrf_sensitivity_strafe = value
    else:
        prefs: MouseStrafingPreferences = bpy.context.preferences.addons[MouseStrafingPreferences.bl_idname].preferences
        prefs.sensitivityStrafeDefault = value


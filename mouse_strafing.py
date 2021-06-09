import math
import time

import bpy
import blf
from mathutils import Vector
from mathutils import Quaternion
import mathutils

from .prefs import MouseStrafingPreferences

def getViews3D(context: bpy.types.Context) -> (bpy.types.SpaceView3D, bpy.types.RegionView3D):
    sv3d = getSpaceView3D(context)
    if not context.space_data.region_quadviews:
        return (sv3d, sv3d.region_3d)
    else:
        i = -1
        for region in context.area.regions:
            if region.type == 'WINDOW':
                i += 1
                if context.region == region:
                    break
        else:
            return (sv3d, sv3d.region_3d)
        return (sv3d, context.space_data.region_quadviews[i])

def getSpaceView3D(context: bpy.types.Context) -> bpy.types.SpaceView3D:
    area = context.area
    if area is not None and area.type == "VIEW_3D":
        return area.spaces[0]
    return None

def getViewPos(rv3d: bpy.types.RegionView3D) -> (Vector, Vector):
    pivotPos = Vector(rv3d.view_location)
    viewDir = Vector((0, 0, -1))
    viewDir.rotate(Quaternion(rv3d.view_rotation))
    return (pivotPos - viewDir * rv3d.view_distance, viewDir)

def setViewPos(rv3d: bpy.types.RegionView3D, viewPos: Vector):
    curPos, _viewDir = getViewPos(rv3d)
    offset = viewPos - curPos
    rv3d.view_location += offset

def signExp(base, exponent) -> float:
    v = abs(base)
    s = math.pow(v, exponent)
    return s if base > 0 else -s

running = False

class MouseStrafingOperator(bpy.types.Operator):
    """Strafe in the 3D View using the mouse."""
    bl_idname = "view_3d.mouse_strafing"
    bl_label = "Mouse Strafing"
    bl_options = { "BLOCKING" }

    mouseSanityMultiplierPan = 0.0025
    mouseSanityMultiplierStrafe = 0.025

    wasdKeys = [ "W", "A", "S", "D", "Q", "E" ]
    inFast, inSlowStrafe, inSlowPan = False, False, False

    lmbDown, rmbDown, mmbDown = False, False, False
    isInMouseMode = False
    modeKeyDown = True
    modeKeyPresses = 0
    inEscape = False

    wDown, aDown, sDown, dDown, qDown, eDown = False, False, False, False, False, False
    isWasding = False
    wasdStartTime = time.perf_counter()
    wasdPreviousTime = time.perf_counter()
    wasdCurSpeed = 0.0
    stopSignal = None

    cDown = False
    adjustPivotSuccess = False
    
    prefs: MouseStrafingPreferences = None
    area = None
    region = None
    drawCallbackHandle = None
    
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        global running
        if not running and event.value == "PRESS":
            self.area = context.area
            _sv3d, self.region = getViews3D(context)
            self.considerCenterCameraView(context)
            running = True
            self.prefs = context.preferences.addons["mouse_strafing"].preferences
            context.window_manager.modal_handler_add(self)
            args = (self, context, event)
            self.drawCallbackHandle = bpy.types.SpaceView3D.draw_handler_add(drawCallback, args, "WINDOW", "POST_PIXEL")
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        return {"PASS_THROUGH"}

    def considerCenterCameraView(self, context: bpy.types.Context):
        sv3d, rv3d = getViews3D(context)
        if rv3d.view_perspective == "CAMERA":
            rv3d.view_camera_offset = (0.0, 0.0)

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if not running:
            return {"CANCELLED"}
        self.inFast, self.inSlowStrafe, self.inSlowPan = event.shift, event.ctrl, event.alt
        if event.type == kmi.type:
            if event.value == "PRESS":
                self.modeKeyPresses = self.modeKeyPresses + (0 if self.modeKeyDown else 1)
                self.modeKeyDown = True
            elif event.value == "RELEASE":
                self.modeKeyDown = False
            return self.considerExitOperator(context)
        elif event.type == "ESC":
            self.inEscape = True if event.value == "PRESS" else (False if event.value == "RELEASE" else self.inEscape)
            return self.considerExitOperator(context)
        elif event.type in [ "LEFTMOUSE", "RIGHTMOUSE", "MIDDLEMOUSE" ]:
            return self.updateMode(context, event)
        elif event.type in [ "MOUSEMOVE", "INBETWEEN_MOUSEMOVE" ]:
            if not self.isInMouseMode or (event.mouse_x == event.mouse_prev_x and event.mouse_y == event.mouse_prev_y):
                return {"RUNNING_MODAL"}
            if self.lmbDown and not self.rmbDown:
                self.performMouseAction(context, event, self.prefs.lmbAction)
            elif not self.lmbDown and self.rmbDown:
                self.performMouseAction(context, event, self.prefs.rmbAction)
            elif self.lmbDown and self.rmbDown:
                self.performMouseAction(context, event, self.prefs.bmbAction)
            elif self.mmbDown:
                self.performMouseAction(context, event, self.prefs.mmbAction)
            self.resetMouse(context, event)
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        elif event.type == "WHEELUPMOUSE" or event.type == "WHEELDOWNMOUSE":
            sv3d, rv3d = getViews3D(context)
            if self.prefs.wheelMoveFunction == "moveZ":
                mod = self.modScaleStrafe()
                self.move3dView(sv3d, rv3d, \
                    Vector((0, 0, -self.prefs.wheelDistance * mod if event.type == "WHEELUPMOUSE" else self.prefs.wheelDistance * mod)), \
                    Vector((0, 0, 0)))
            elif self.prefs.wheelMoveFunction == "changeFOV":
                self.nudgeFov(sv3d, rv3d, (True if event.type == "WHEELUPMOUSE" else False) != self.prefs.invertMouse)
            return {"RUNNING_MODAL"}
        elif event.type in self.wasdKeys:
            if self.stopSignal is None:
                self.stopSignal = [False]
                pinnedSv3d, pinnedRv3d = getViews3D(context)
                pinnedStopSignal = self.stopSignal
                bpy.app.timers.register(lambda: fpsMove(self, pinnedSv3d, pinnedRv3d, pinnedStopSignal))
            self.updateKeys(context, event)
            return {"RUNNING_MODAL"}
        elif event.type == "C":
            self.cDown = event.value == "PRESS" if event.type == "C" else self.cDown
            if event.value == "PRESS":
                self.adjustPivot(context)
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        elif event.type == "R":
            if event.value == "PRESS":
                self.resetRoll(context)
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        return {"PASS_THROUGH"}

    def nudgeFov(self, sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D, up: bool):
        if rv3d.view_perspective == "CAMERA":
            if sv3d.lock_camera and sv3d.camera is not None and sv3d.camera.type == "CAMERA" and type(sv3d.camera.data) is bpy.types.Camera:
                cam = bpy.types.Camera(sv3d.camera.data)
                cam.lens = nudgeFovValue(cam.lens, up)
        else:
            sv3d.lens = nudgeFovValue(sv3d.lens, up)

    def modScaleStrafe(self):
        inFastStrafe, inSlowStrafe = self.inFast and (self.inFast != self.inSlowStrafe), self.inSlowStrafe and (self.inSlowStrafe != self.inFast)
        if inFastStrafe:
            return 5
        if inSlowStrafe and self.inSlowPan:
            return 0.02
        if inSlowStrafe:
            return 0.2
        if self.inSlowPan:
            return 0.5
        return 1

    def modScalePan(self):
        inSlowStrafe = self.inSlowStrafe and (self.inSlowStrafe != self.inFast)
        if self.inSlowPan:
            return 0.2
        if inSlowStrafe:
            return 0.5
        return 1

    def updateMode(self, context: bpy.types.Context, event: bpy.types.Event):
        self.lmbDown = event.value == "PRESS" if event.type == "LEFTMOUSE" else self.lmbDown
        self.rmbDown = event.value == "PRESS" if event.type == "RIGHTMOUSE" else self.rmbDown
        self.mmbDown = event.value == "PRESS" if event.type == "MIDDLEMOUSE" else self.mmbDown
        enteringMouseMode = (self.lmbDown or self.rmbDown or self.mmbDown) and not self.isInMouseMode
        leavingMouseMode = self.isInMouseMode and not (self.lmbDown or self.rmbDown or self.mmbDown)
        self.isInMouseMode = self.lmbDown or self.rmbDown or self.mmbDown
        if enteringMouseMode:
            context.window.cursor_set("NONE")
            context.area.tag_redraw()
        elif leavingMouseMode:
            self.exitMouseMode(context)
            return self.considerExitOperator(context)
        return {"RUNNING_MODAL"}

    def updateKeys(self, context: bpy.types.Context, event: bpy.types.Event):
        wasWasding = self.isWasding
        self.wDown = event.value == "PRESS" if event.type == "W" else self.wDown
        self.aDown = event.value == "PRESS" if event.type == "A" else self.aDown
        self.sDown = event.value == "PRESS" if event.type == "S" else self.sDown
        self.dDown = event.value == "PRESS" if event.type == "D" else self.dDown
        self.qDown = event.value == "PRESS" if event.type == "Q" else self.qDown
        self.eDown = event.value == "PRESS" if event.type == "E" else self.eDown
        self.isWasding = self.wDown or self.aDown or self.sDown or self.dDown or self.qDown or self.eDown
        if not wasWasding or not self.isWasding:
            self.wasdCurSpeed = 0.0
        if not wasWasding and self.isWasding:
            self.wasdStartTime = time.perf_counter()
            self.wasdPreviousTime = self.wasdStartTime

    def performMouseAction(self, context: bpy.types.Context, event: bpy.types.Event, action):
        delta = Vector((event.mouse_x - event.mouse_prev_x, event.mouse_y - event.mouse_prev_y))
        modPan = self.modScalePan()
        modStrafe = self.modScaleStrafe()

        # Panning feels more sensitive during WASD movement as well as rappel movement.
        panDelta = delta * self.mouseSanityMultiplierPan * ((self.prefs.sensitivityPan * 0.85) if self.isWasding else self.prefs.sensitivityPan) * modPan
        panDeltaRappel = 0.8 * panDelta

        # It is easier to make larger mouse movements sideways than back and forth. That is useful for panning the view, because there generally
        # is a greater need to turn left/right than up/down. For strafing, forwards/backwards should not be more physically taxing than sideways movement.
        # By doing the following, we give more oomph to back and forwards movements to make up for the shortcomings of mouse ergonomics.
        deltaStrafe = Vector((delta[0], delta[1]*1.2))
        strafeDelta = deltaStrafe * self.mouseSanityMultiplierStrafe * self.prefs.sensitivityStrafe * modStrafe

        sv3d, rv3d = getViews3D(context)
        if action == "turnXY":
            self.pan3dView(sv3d, rv3d, Vector((panDelta[0], -panDelta[1] if self.prefs.invertMouse else panDelta[0])))
        elif action == "roll":
            self.roll3dView(sv3d, rv3d, Vector((panDelta[0], -panDelta[1] if self.prefs.invertMouse else panDelta[1])))
        else:
            if action == "strafeXZ":
                self.move3dView(sv3d, rv3d, Vector((strafeDelta[0], 0, -strafeDelta[1])), Vector((0, 0, 0)))
            elif action == "strafeXY":
                self.move3dView(sv3d, rv3d, Vector((strafeDelta[0], strafeDelta[1], 0)), Vector((0, 0, 0)))
            elif action == "strafeXRappel":
                self.move3dView(sv3d, rv3d, Vector((strafeDelta[0], 0, 0)), Vector((0, 0, strafeDelta[1])))
            elif action == "turnXRappel":
                self.move3dView(sv3d, rv3d, Vector((0, 0, 0)), Vector((0, 0, strafeDelta[1])))
                self.pan3dView(sv3d, rv3d, Vector((panDeltaRappel[0], 0)))

    def pan3dView(self, sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D, delta: Vector):
        viewPos, rot, _viewDir = prepareCameraTransformation(sv3d, rv3d)
        yawRot = Quaternion(Vector((0, 0, 1)), -delta[0])
        pitchAxis = Vector((1, 0, 0))
        pitchAxis.rotate(rot)
        pitchRot = Quaternion(pitchAxis, delta[1])
        rot.rotate(pitchRot)
        rot.rotate(yawRot)
        applyCameraTranformation(sv3d, rv3d, viewPos, rot)

    def roll3dView(self, sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D, delta: Vector):
        viewPos, rot, viewDir = prepareCameraTransformation(sv3d, rv3d)
        roll = Quaternion(viewDir, delta[0])
        rot.rotate(roll)
        applyCameraTranformation(sv3d, rv3d, viewPos, rot)

    def move3dView(self, sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D, delta: Vector, globalDelta: Vector):
        viewPos, rot, _viewDir = prepareCameraTransformation(sv3d, rv3d)
        delta.rotate(Quaternion(rot))
        viewPos = viewPos + delta + globalDelta
        applyCameraTranformation(sv3d, rv3d, viewPos, rot)

    def adjustPivot(self, context: bpy.types.Context):
        sv3d, rv3d = getViews3D(context)
        viewPos, rot, viewDir = prepareCameraTransformation(sv3d, rv3d)
        castStart = viewPos + viewDir * sv3d.clip_start
        self.adjustPivotSuccess = False
        attemptCount = 0
        invert = False # there is no way to retrieve all hits, so we need to spam some rays back and forth.
        minCast = viewPos + viewDir * sv3d.clip_start
        maxCast = viewPos + viewDir * sv3d.clip_end
        while attemptCount < 100:
            attemptCount = attemptCount + 1
            castDir = -viewDir if invert else viewDir
            castLength = (minCast - castStart).dot(castDir) if invert else (maxCast - minCast).dot(castDir)
            if not invert and castLength <= 0:
                break
            hit = context.scene.ray_cast(context.window.view_layer.depsgraph, castStart, castDir, distance = castLength)
            if not hit[0]:
                break
            hitBackface = Vector(hit[2]).dot(viewDir) > 0
            if hitBackface and sv3d.shading.show_backface_culling:
                if invert:
                    invert = not invert
                    continue
                nudge = castStart.length * 0.000001
                if nudge < 0.00001:
                    nudge = 0.00001
                elif nudge > 0.004:
                    nudge = 0.004
                castStart = hit[1] + viewDir * nudge
                invert = not invert
                continue
            newPivotPos = viewPos + (Vector(hit[1]) - viewPos) * (1.0 + self.prefs.pivotDig * 0.01)
            rv3d.view_distance = (newPivotPos - viewPos).length
            applyCameraTranformation(sv3d, rv3d, viewPos, rot, True)
            self.adjustPivotSuccess = True
            break

    def resetRoll(self, context: bpy.types.Context):
        sv3d, rv3d = getViews3D(context)
        viewPos, rot, viewDir = prepareCameraTransformation(sv3d, rv3d)
        up = Vector((0, 1, 0))
        up.rotate(rot)
        py = getPitchYaw(viewDir, up)
        newRot = Quaternion(Vector((1, 0, 0)), py[0])
        if py[0] != 0:
            newRot.rotate(Quaternion(Vector((0, 0, 1)), py[1]))
        applyCameraTranformation(sv3d, rv3d, viewPos, newRot)

    def wasdDelta(self):
        now = time.perf_counter()
        delta = self.modScaleStrafe() * self.wasdCurSpeed * (now - self.wasdPreviousTime)
        self.wasdPreviousTime = now
        return delta
    
    def wasdAccelerate(self):
        if self.wasdCurSpeed < self.prefs.wasdTopSpeed and self.prefs.wasdTime > 0.0005:
            self.wasdCurSpeed = self.prefs.wasdTopSpeed * ((time.perf_counter() - self.wasdStartTime) / self.prefs.wasdTime)
        else:
            self.wasdCurSpeed = self.prefs.wasdTopSpeed
        if self.wasdCurSpeed > self.prefs.wasdTopSpeed:
            self.wasdCurSpeed = self.prefs.wasdTopSpeed

    def exitMouseMode(self, context: bpy.types.Context):
        self.isInMouseMode = False
        self.centerMouse(context)
        context.window.cursor_set("DEFAULT")
        context.area.tag_redraw()

    def considerExitOperator(self, context: bpy.types.Context):
        if (not self.prefs.toggleMode and not self.modeKeyDown and not self.isInMouseMode) or (self.prefs.toggleMode and self.modeKeyPresses > 0) or (self.inEscape):
            if self.isInMouseMode:
                self.exitMouseMode(context)
            return self.exitOperator(context)
        return {"RUNNING_MODAL"}

    def exitOperator(self, context: bpy.types.Context):
        global running
        running = False
        if self.stopSignal is not None:
            self.stopSignal[0] = True
            self.stopSignal = None
        if self.prefs.adjustPivot:
            self.adjustPivot(context)
        bpy.types.SpaceView3D.draw_handler_remove(self.drawCallbackHandle, "WINDOW")
        context.area.tag_redraw()
        return {"CANCELLED"}

    def centerMouse(self, context: bpy.types.Context):
        context.window.cursor_warp(context.region.x + context.region.width // 2, context.region.y + context.region.height // 2)

    def resetMouse(self, context: bpy.types.Context, event: bpy.types.Event):
        if not (event.mouse_x < context.region.x + context.region.width // 3 or event.mouse_x > context.region.x + 2 * context.region.width // 3 \
                or event.mouse_y < context.region.y + context.region.height // 3 or event.mouse_y > context.region.y + 2 * context.region.height // 3):
            return
        context.window.cursor_warp(context.region.x + context.region.width // 2, context.region.y + context.region.height // 2)

def clamp(x, min, max):
    return min if x < min else (max if x > max else x)

def clampLensValue(lensFunc):
    def clampFunc(lens: float, up: bool):
        return clamp(lensFunc(lens, up), 1.0, 250.0)
    return clampFunc

@clampLensValue
def nudgeFovValue(lens: float, up: bool) -> float:
    lens = round(lens * 8, 0) / 8.0
    if up:
        if lens >= 50:
            return lens + 2
        if lens >= 20:
            return lens + 1
        if lens >= 10:
            return lens + 0.5
        if lens >= 5:
            return lens + 0.25
        return lens + 0.125
    else:
        if lens > 50:
            return lens - 2
        if lens > 20:
            return lens - 1
        if lens > 10:
            return lens - 0.5
        if lens > 5:
            return lens - 0.25
        return lens - 0.125

def prepareCameraTransformation(sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D) -> (Vector, Quaternion, Vector):
    considerViewToCamera(sv3d, rv3d)
    viewPos, _viewDir = getViewPos(rv3d)
    viewRot = Quaternion(rv3d.view_rotation)
    if rv3d.view_perspective == "CAMERA" and sv3d.lock_camera and sv3d.camera is not None:
        viewPos = sv3d.camera.location
        viewRot = getObjectRotationQuaternion(sv3d.camera)
    viewDir = Vector((0, 0, -1))
    viewDir.rotate(viewRot)
    return viewPos, viewRot, viewDir

def applyCameraTranformation(sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D, viewPos: Vector, viewRot: Quaternion, forceSetView = False):
    if not forceSetView and rv3d.view_perspective == "CAMERA" and sv3d.lock_camera and sv3d.camera is not None:
        sv3d.camera.location = viewPos
        setObjectRotationQuaternion(sv3d.camera, viewRot)
    else:
        rv3d.view_rotation = viewRot
        setViewPos(rv3d, viewPos)

def considerViewToCamera(sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D):
    if rv3d.view_perspective == "CAMERA" and not sv3d.lock_camera and sv3d.camera is not None:
        viewToCamera(sv3d, rv3d)
        rv3d.view_perspective = "PERSP"

def viewToCamera(sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D):
    camera = sv3d.camera
    rv3d.view_rotation = getObjectRotationQuaternion(camera)
    setViewPos(rv3d, camera.location)

def getObjectRotationQuaternion(obj: bpy.types.Object) -> Quaternion:
    if obj.rotation_mode == "QUATERNION":
        return Quaternion(obj.rotation_quaternion)
    elif obj.rotation_mode == "AXIS_ANGLE":
        return Quaternion(Vector((obj.rotation_axis_angle[0], obj.rotation_axis_angle[1], obj.rotation_axis_angle[2])), obj.rotation_axis_angle[3])
    return mathutils.Euler(obj.rotation_euler).to_quaternion()

def setObjectRotationQuaternion(obj: bpy.types.Object, rot: Quaternion):
    if obj.rotation_mode == "QUATERNION":
        obj.rotation_quaternion = rot
    elif obj.rotation_mode == "AXIS_ANGLE":
        obj.rotation_axis_angle = rot.to_axis_angle()
    else:
        obj.rotation_euler = rot.to_euler(obj.rotation_mode)

def getPitchYaw(dir: Vector, up: Vector):
    pitch = 0.0 if dir[2] <= -1 else (math.pi if dir[2] >= 1 else math.acos(-dir[2]))
    yaw = 0.0
    flatDir = dir
    if not (flatDir[2] > -0.999999 and flatDir[2] < 0.999999):
        flatDir = up
    elif not (flatDir[2] > -0.999 and flatDir[2] < 0.999):
        flatDir = flatDir * 1024 # normalizing a vector involves squaring its elements. making it longer here eliminates the chance of a division by zero.
    mirrorYaw = flatDir[1] < 0
    flatDir[2] = 0
    flatDir.normalize()
    x = flatDir[0]
    yaw = 0.5 * math.pi if x <= -1 else (-0.5 * math.pi if x >= 1 else -math.asin(x))
    if mirrorYaw:
        yaw = math.pi - yaw
    return Vector((pitch, yaw))

def fpsMove(op: MouseStrafingOperator, sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D, stopSignal):
    if not running or stopSignal[0]: return None
    if op.isWasding: op.wasdAccelerate()
    delta = op.wasdDelta()
    if op.wDown: op.move3dView(sv3d, rv3d, Vector((0, 0, -delta)), Vector((0, 0, 0)))
    if op.aDown: op.move3dView(sv3d, rv3d, Vector((-delta, 0, 0)), Vector((0, 0, 0)))
    if op.sDown: op.move3dView(sv3d, rv3d, Vector((0, 0, delta)), Vector((0, 0, 0)))
    if op.dDown: op.move3dView(sv3d, rv3d, Vector((delta, 0, 0)), Vector((0, 0, 0)))
    if op.qDown: op.move3dView(sv3d, rv3d, Vector((0, -delta, 0)), Vector((0, 0, 0)))
    if op.eDown: op.move3dView(sv3d, rv3d, Vector((0, delta, 0)), Vector((0, 0, 0)))
    return 0.0001

def drawCallback(op: MouseStrafingOperator, context: bpy.types.Context, event: bpy.types.Event):
    if context.area != op.area:
        return
    sv3d, rv3d = getViews3D(context)
    if rv3d != op.region:
        return
    fontId = 0
    blf.size(fontId, 20, 72)
    if op.prefs.showCrosshair:
        x, y = context.region.width // 2 - 8, context.region.height // 2 - 7
        blf.color(fontId, 0, 0, 0, 0.8)
        blf.position(fontId, x, y, 0)
        blf.draw(fontId, "+")
        color = ((0.1, 1, 0.05, 1) if op.adjustPivotSuccess else (1, 0.1, 0.05, 1)) if op.cDown else \
            (1, 1, 1, 1) if op.isInMouseMode else (0.75, 0.75, 0.75, 1)
        blf.color(fontId, *color)
        blf.position(fontId, x, y+1, 0)
        blf.draw(fontId, "+")

km = None
kmi = None

def register_keymaps():
    global km
    global kmi
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.find(name = "3D View", space_type = "VIEW_3D", region_type = "WINDOW")
        if km is None:
            km = kc.keymaps.new(name = "3D View", space_type = "VIEW_3D", region_type = "WINDOW", modal=False)
        kmi = km.keymap_items.new(MouseStrafingOperator.bl_idname, "SPACE", "PRESS", head=True)

def unregister_keymaps():
    global km
    global kmi
    km.keymap_items.remove(kmi)

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

lastDistPre = 0.0
lastDynSens = 0.0

def setDynamicSensitivityStats(delta: Vector, prefs: MouseStrafingPreferences):
    dist = math.sqrt(delta[0]*delta[0] + delta[1]*delta[1])
    distPre = dist * prefs.mousePreMultiplier
    global lastDistPre
    global lastDynSens
    lastDistPre = distPre
    lastDynSens = getDynamicSensitivity(delta, prefs)

def getDynamicSensitivity(delta: Vector, prefs: MouseStrafingPreferences) -> float:
    dist = math.sqrt(delta[0]*delta[0] + delta[1]*delta[1])
    distPre = dist * prefs.mousePreMultiplier

    minDynamicSensitivity = prefs.minDynamicSensitivity / 100.0
    dynSens = 0.0

    # these would probably be configurable in a more demanding application
    minPrecisionWidth = 0.02
    transitionQuadraticPart = 0.9

    if distPre >= 1.0:
        dynSens = 1.0
    elif distPre <= minPrecisionWidth:
        dynSens = minDynamicSensitivity
    else:
        a = (minDynamicSensitivity - 1) / (-(minPrecisionWidth - 1)*(minPrecisionWidth - 1))
        dynamicSensitivityQuadratic = 1 + a*(-(distPre-1)*(distPre-1))

        s = (1 - minDynamicSensitivity) / (1 - minPrecisionWidth)
        dynamicSensitivityLinear = minDynamicSensitivity + s * (distPre - minPrecisionWidth)

        dynSens = transitionQuadraticPart * dynamicSensitivityQuadratic + (1 - transitionQuadraticPart) * dynamicSensitivityLinear
    return dynSens

running = False

class MouseStrafingOperator(bpy.types.Operator):
    """Strafe in the 3D View using the mouse."""
    bl_idname = "view_3d.mouse_strafing"
    bl_label = "Mouse Strafing"
    bl_options = { "BLOCKING" }

    mousePostSanityMultiplierPan = 0.003
    mousePostSanityMultiplierStrafe = 0.05

    wasdKeys = [ "W", "A", "S", "D", "Q", "E" ]
    inFast, inSlowStrafe, inSlowPan = False, False, False

    lmbDown, rmbDown, mmbDown = False, False, False
    isClicking = False
    modeKeyReleased = False

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
            running = True
            self.prefs = context.preferences.addons["mouse_strafing"].preferences
            context.window_manager.modal_handler_add(self)
            args = (self, context, event)
            self.drawCallbackHandle = bpy.types.SpaceView3D.draw_handler_add(drawCallback, args, "WINDOW", "POST_PIXEL")
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        return {"PASS_THROUGH"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if not running:
            return {"CANCELLED"}
        self.inFast, self.inSlowStrafe, self.inSlowPan = event.shift, event.ctrl, event.alt
        if event.type == kmi.type:
            if event.value == "PRESS":
                self.modeKeyReleased = False
            elif event.value == "RELEASE":
                self.modeKeyReleased = True
            return self.considerExitOperator(context)
        elif event.type in [ "LEFTMOUSE", "RIGHTMOUSE", "MIDDLEMOUSE" ]:
            return self.updateMode(context, event)
        elif event.type == "MOUSEMOVE":
            if event.mouse_x == event.mouse_prev_x and event.mouse_y == event.mouse_prev_y:
                return {"RUNNING_MODAL"}
            if self.isClicking:
                self.resetMouse(context, event)
            if self.lmbDown and not self.rmbDown:
                self.performMouseAction(context, event, self.prefs.lmbAction)
            elif not self.lmbDown and self.rmbDown:
                self.performMouseAction(context, event, self.prefs.rmbAction)
            elif self.lmbDown and self.rmbDown:
                self.performMouseAction(context, event, self.prefs.bmbAction)
            elif self.mmbDown:
                self.performMouseAction(context, event, self.prefs.mmbAction)
            return {"RUNNING_MODAL"}
        elif event.type == "WHEELUPMOUSE" or event.type == "WHEELDOWNMOUSE":
            mod = self.modScaleStrafe()
            sv3d, rv3d = getViews3D(context)
            self.move3dView(sv3d, rv3d, \
                Vector((0, 0, -self.prefs.wheelDistance * mod if event.type == "WHEELUPMOUSE" else self.prefs.wheelDistance * mod)), \
                Vector((0, 0, 0)))
            return {"RUNNING_MODAL"}
        elif event.type in self.wasdKeys:
            if self.stopSignal is None:
                self.stopSignal = [False]
                pinnedStopSignal = self.stopSignal
                pinnedSv3d, pinnedRv3d = getViews3D(context)
                bpy.app.timers.register(lambda: fpsMove(self, pinnedSv3d, pinnedRv3d, pinnedStopSignal))
            return self.updateKeys(context, event)
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
        enteringStrafe = (self.lmbDown or self.rmbDown or self.mmbDown) and not self.isClicking
        leavingStrafe = self.isClicking and not (self.lmbDown or self.rmbDown or self.mmbDown)
        self.isClicking = self.lmbDown or self.rmbDown or self.mmbDown
        if enteringStrafe:
            context.window.cursor_set("NONE")
            context.area.tag_redraw()
        elif leavingStrafe:
            return self.exitStrafe(context)
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
        return {"RUNNING_MODAL"}

    def performMouseAction(self, context: bpy.types.Context, event: bpy.types.Event, action):
        delta = Vector((event.mouse_x - event.mouse_prev_x, event.mouse_y - event.mouse_prev_y))
        modPan = self.modScalePan()
        modStrafe = self.modScaleStrafe()

        setDynamicSensitivityStats(delta, self.prefs)
        processedPanDelta = delta * getDynamicSensitivity(delta, self.prefs)
        panDelta = processedPanDelta * self.mousePostSanityMultiplierPan * ((self.prefs.sensitivityPan * 0.75) if self.isWasding else self.prefs.sensitivityPan) * modPan
        panDeltaRappel = 0.75 * panDelta

        # A few words about what is going on here:
        # It is easier to make larger mouse movements sideways than back and forth. That is useful for panning the view, because there generally
        # is a greater need to turn left/right than up/down. For strafing, all directions are equally relevant. By doing the following, we
        # 1. give more oomph to back and forwards movements to make up for the shortcomings of mouse ergonomics
        # 2. eliminate unwanted side-strafing by applying sensitivity per axis
        deltaStrafe = Vector((delta[0], delta[1]*1.2))
        processedStrafeDelta = deltaStrafe * Vector((getDynamicSensitivity((deltaStrafe[0], 0), self.prefs), getDynamicSensitivity((0, deltaStrafe[1]), self.prefs)))
        strafeDelta = processedStrafeDelta * self.mousePostSanityMultiplierStrafe * self.prefs.sensitivityStrafe * modStrafe

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
            hit = context.scene.ray_cast(context.window.view_layer, castStart, castDir, distance = castLength)
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

    def exitStrafe(self, context: bpy.types.Context):
        self.centerMouse(context)
        context.window.cursor_set("DEFAULT")
        context.area.tag_redraw()
        return self.considerExitOperator(context)

    def considerExitOperator(self, context: bpy.types.Context):
        if self.modeKeyReleased and not self.isClicking:
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
        delta = Vector((event.mouse_x - event.mouse_prev_x, event.mouse_y - event.mouse_prev_y))
        offset = Vector((-clamp(delta[0]*0.5, -context.region.width // 2, context.region.width // 2), \
            -clamp(delta[1]*0.5, -context.region.height // 2, context.region.height // 2)))
        context.window.cursor_warp(context.region.x + context.region.width // 2 + offset[0], context.region.y + context.region.height // 2 + offset[1])

def clamp(x, min, max):
    return min if x < min else (max if x > max else x)

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
    return 0.001

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
            (1, 1, 1, 1) if op.isClicking else (0.75, 0.75, 0.75, 1)
        blf.color(fontId, *color)
        blf.position(fontId, x, y+1, 0)
        blf.draw(fontId, "+")
    if op.prefs.displayDynamicSensitivityStats:
        global lastDistPre
        global lastDynSens
        if lastDistPre >= 1:
            blf.color(fontId, 0.95, 0.95, 0.95, 0.99)
            blf.position(fontId, 100, 70, 0)
            blf.draw(fontId, "[ MAXED OUT ]")
        else:
            blf.color(fontId, 0.75, 0.75, 0.75, 0.99)
        blf.position(fontId, 100, 100, 0)
        blf.draw(fontId, "DynamicSensitivity(%.3f) = %.1f%%" % (lastDistPre, lastDynSens * 100.0))

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

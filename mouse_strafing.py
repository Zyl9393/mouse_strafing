import math
import time

import bpy
import blf
from mathutils import Vector
from mathutils import Quaternion
import mathutils

from .prefs import MouseStrafingPreferences
from .prefs import NavigationMouseButtonBinding

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
    viewDir.rotate(rv3d.view_rotation)
    return (pivotPos - viewDir * rv3d.view_distance, viewDir)

def setViewPos(rv3d: bpy.types.RegionView3D, viewPos: Vector):
    curPos, _viewDir = getViewPos(rv3d)
    offset = viewPos - curPos
    rv3d.view_location += offset

def signExp(base, exponent) -> float:
    v = abs(base)
    s = math.pow(v, exponent)
    return s if base > 0 else -s

def getKeyDown(previousKeyState: bool, event: bpy.types.Event) -> bool:
    return True if event.value == "PRESS" else (False if event.value == "RELEASE" else previousKeyState)

running = False
drawCallbackHandle = None

class CameraState(bpy.types.PropertyGroup):
    viewPos: bpy.props.FloatVectorProperty(size = 3, options = {"HIDDEN"})
    rot: bpy.props.FloatVectorProperty(size = 4, options = {"HIDDEN"})
    viewDist: bpy.props.FloatProperty(options = {"HIDDEN"})
    lens: bpy.props.FloatProperty(options = {"HIDDEN"})
    isPerspective: bpy.props.BoolProperty(options = {"HIDDEN"})

class CameraStates(bpy.types.PropertyGroup):
    savedStates: bpy.props.CollectionProperty(type = CameraState, options = {"HIDDEN"})
    usedStates: bpy.props.BoolVectorProperty(size = 10, default = (False, False, False, False, False, False, False, False, False, False), options = {"HIDDEN"})
    imminentState: bpy.props.PointerProperty(type = CameraState, options = {"HIDDEN"})
    imminentSlot: bpy.props.IntProperty(options = {"HIDDEN"}, default = -1)

class MouseStrafingOperator(bpy.types.Operator):
    """Strafe in the 3D View using the mouse."""
    bl_idname = "view3d.mouse_strafing"
    bl_label = "Mouse Strafing"
    bl_options = { "BLOCKING" }

    __slots__ = 'mouseSanityMultiplierPan', 'mouseSanityMultiplierStrafe', 'strafeSensitivityRanges', 'focalLengthRanges', 'fovRanges', \
        'operatorKey', 'operatorKeyDown', 'operatorKeyPresses', 'inEscape', 'stopSignal', 'isInMouseAction', \
        'increasedMagnitude', 'increasedPrecision', 'alternateControl', \
        'lmbDown', 'rmbDown', 'mmbDown', 'mb4Down', 'mb5Down', 'mb6Down', 'mb7Down', \
        'keyDownForward', 'keyDownLeft', 'keyDownBackward', 'keyDownRight', 'keyDownDown', 'keyDownUp', \
        'isWasding', 'wasdStartTime', 'wasdPreviousTime', 'wasdSpeedPercentage', \
        'keySaveStateDown', 'keySaveStateSlotDown', 'loadCameraState', 'loadedCameraState', 'imminentSaveStateTime',  \
        'keyDownRelocatePivot', 'relocatePivotLock', 'adjustPivotSuccess', \
        'editStrafeSensitivityTime', 'editFovTime', 'editGearTime', 'redrawAfterDrawCallback', 'keyCycleGearsDown', \
        'bewareWarpDist', 'previousDelta', 'ignoreMouseEvents', \
        'prefs', 'area', 'sv3d', 'rv3d'

    def initFields(self, context: bpy.types.Context, event: bpy.types.Event):
        self.mouseSanityMultiplierPan = 0.003
        self.mouseSanityMultiplierStrafe = 0.02
        self.strafeSensitivityRanges = ((0.001, 0.001), (0.02, 0.002), (0.05, 0.005), (0.1, 0.01), (0.2, 0.02), (0.5, 0.05), (1.0, 0.1), (2.0, 0.2), (5.0, 0.5), (10.0, 1.0), (20.0, 2.0), (50.0, 5.0), 100)
        self.focalLengthRanges = ((1, 0.125), (5, 0.25), (10, 0.5), (20, 1), (50, 2), (100, 2.5), (175, 5), 250)
        self.fovRanges = ((0.125, 0.125), (5, 0.25), (15, 0.5), (30, 1), (130, 0.5), (160, 0.25), 179)

        self.operatorKey = event.type
        self.operatorKeyDown = True
        self.operatorKeyPresses = 0
        self.inEscape = False
        self.isInMouseAction = False
        self.stopSignal = None

        self.increasedMagnitude, self.increasedPrecision, self.alternateControl = False, False, False

        self.lmbDown, self.rmbDown, self.mmbDown, self.mb4Down, self.mb5Down, self.mb6Down, self.mb7Down = False, False, False, False, False, False, False

        self.keyDownForward, self.keyDownLeft, self.keyDownBackward, self.keyDownRight, self.keyDownDown, self.keyDownUp = False, False, False, False, False, False

        self.isWasding = False
        self.wasdStartTime = time.perf_counter() - 9999
        self.wasdPreviousTime = time.perf_counter() - 9999
        self.wasdSpeedPercentage = 0.0

        self.keySaveStateDown = False
        self.keySaveStateSlotDown = [False, False, False, False, False, False, False, False, False, False]
        self.loadCameraState = False
        self.loadedCameraState = False
        self.imminentSaveStateTime = time.perf_counter() - 9999

        self.keyDownRelocatePivot = False
        self.relocatePivotLock = False
        self.adjustPivotSuccess = False

        self.editStrafeSensitivityTime = time.perf_counter() - 9999
        self.editFovTime = time.perf_counter() - 9999
        self.editGearTime = time.perf_counter() - 9999
        self.redrawAfterDrawCallback = False
        self.keyCycleGearsDown = False

        self.bewareWarpDist = None
        self.previousDelta = None
        self.ignoreMouseEvents = 0

        self.prefs = context.preferences.addons[MouseStrafingPreferences.bl_idname].preferences
        self.area = context.area
        self.sv3d, self.rv3d = getViews3D(context)

        self.snapGear()

        self.updateMode(context, event)

    def getActionFunc(self, action):
        if action == "turnXY":
            return self.turnXY
        elif action == "roll":
            return self.roll
        elif action == "strafeXZ":
            return self.strafeXZ
        elif action == "strafeXY":
            return self.strafeXY
        elif action == "strafeXRappel":
            return self.strafeXRappel
        elif action == "turnXRappel":
            return self.turnXRappel
        return self.nop

    def nop():
        return

    def turnXY(self, delta: Vector):
        panDelta = delta * self.mouseSanityMultiplierPan * self.prefs.sensitivityPan * (0.85 if self.isWasding else 1) * self.getPanFactor()
        self.pan3dView(Vector((-panDelta[0] if self.prefs.invertMouseX else panDelta[0], -panDelta[1] if self.prefs.invertMouse else panDelta[1])))

    def roll(self, delta: Vector):
        rollDelta = delta * self.mouseSanityMultiplierPan * self.prefs.sensitivityPan * (0.85 if self.isWasding else 1) * self.getRollFactor()
        self.roll3dView(Vector((-rollDelta[0] if self.prefs.invertMouseX else rollDelta[0], -rollDelta[1] if self.prefs.invertMouse else rollDelta[1])))

    def strafeXZ(self, delta: Vector):
        strafeDelta = Vector((delta[0], delta[1])) * self.getMovementFactor(True, True)
        self.move3dView(Vector((-strafeDelta[0] if self.prefs.invertStrafeX else strafeDelta[0], 0, strafeDelta[1] if self.prefs.invertStrafeZ else -strafeDelta[1])), Vector((0, 0, 0)))

    def strafeXY(self, delta: Vector):
        strafeDelta = Vector((delta[0], delta[1])) * self.getMovementFactor(True, True)
        self.move3dView(Vector((-strafeDelta[0] if self.prefs.invertStrafeX else strafeDelta[0], -strafeDelta[1] if self.prefs.invertStrafeY else strafeDelta[1], 0)), Vector((0, 0, 0)))

    def strafeXRappel(self, delta: Vector):
        strafeDelta = Vector((delta[0], delta[1])) * self.getMovementFactor(True, True)
        self.move3dView(Vector((-strafeDelta[0] if self.prefs.invertStrafeX else strafeDelta[0], 0, 0)), Vector((0, 0, -strafeDelta[1] if self.prefs.invertStrafeY else strafeDelta[1])))

    def turnXRappel(self, delta: Vector):
        panDelta = delta * self.mouseSanityMultiplierPan * self.prefs.sensitivityPan * (0.85 if self.isWasding else 1) * self.getPanFactor()
        strafeDelta = Vector((delta[0], delta[1])) * self.getMovementFactor(True, True)
        self.move3dView(Vector((0, 0, 0)), Vector((0, 0, -strafeDelta[1] if self.prefs.invertStrafeY else strafeDelta[1])))
        self.pan3dView(Vector((panDelta[0] * 0.8, 0)))

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        global running
        global drawCallbackHandle
        self.initFields(context, event)
        if not running and event.value == "PRESS":
            self.considerCenterCameraView()
            running = True
            context.window_manager.modal_handler_add(self)
            args = (self, context)
            if drawCallbackHandle is not None:
                bpy.types.SpaceView3D.draw_handler_remove(drawCallbackHandle, "WINDOW")
                drawCallbackHandle = None
            drawCallbackHandle = bpy.types.SpaceView3D.draw_handler_add(drawCallback, args, "WINDOW", "POST_PIXEL")
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        return {"PASS_THROUGH"}

    def initSaveStates(self, context: bpy.types.Context):
        states: CameraStates = context.scene.mstrf_camera_save_states
        while len(states.savedStates) < 10:
            states.savedStates.add()

    def considerCenterCameraView(self):
        if self.rv3d.view_perspective == "CAMERA":
            self.rv3d.view_camera_offset = (0.0, 0.0)

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        try:
            if not running:
                return {"CANCELLED"}
            if event.type == self.operatorKey:
                if event.value == "PRESS":
                    self.operatorKeyPresses = self.operatorKeyPresses + (0 if self.operatorKeyDown else 1)
                    self.operatorKeyDown = True
                elif event.value == "RELEASE":
                    self.operatorKeyDown = False
                if self.shouldExitOperator():
                    return self.exitOperator(context)
            self.increasedMagnitude, self.increasedPrecision, self.alternateControl = event.shift, event.ctrl, event.alt
            if event.type in { "MOUSEMOVE", "INBETWEEN_MOUSEMOVE" }:
                if self.ignoreMouseEvents > 0:
                    self.ignoreMouseEvents = self.ignoreMouseEvents - 1
                    self.bewareWarpDist = None
                    return {"RUNNING_MODAL"}
                delta = Vector((event.mouse_x - event.mouse_prev_x, event.mouse_y - event.mouse_prev_y))
                if self.bewareWarpDist is not None:
                    if delta.length > self.bewareWarpDist * 0.5 and delta.length > self.previousDelta.length * 2:
                        if self.prefs.debug:
                            print("mouse_strafing: detected cursor_warp glitch: using last mouse delta (" + str(self.previousDelta[0]) + ", " + str(self.previousDelta[1]) + ") instead of (" + str(delta[0]) + ", " + str(delta[1]) + ")")
                        delta = self.previousDelta
                    self.bewareWarpDist = None
                if self.isInMouseAction and not (event.mouse_x == event.mouse_prev_x and event.mouse_y == event.mouse_prev_y):
                    binding = self.getSatisfiedBinding()
                    if binding is not None:
                        self.getActionFunc(binding.action)(delta)
                    self.resetMouse(context, event)
            elif event.type in { "LEFTMOUSE", "RIGHTMOUSE", "MIDDLEMOUSE", "BUTTON4MOUSE", "BUTTON5MOUSE", "BUTTON6MOUSE", "BUTTON7MOUSE" }:
                return self.updateMode(context, event)
            elif event.type == "WHEELUPMOUSE" or event.type == "WHEELDOWNMOUSE":
                if event.alt:
                    self.nudgeFov(context, (event.type == "WHEELUPMOUSE") != self.prefs.scrollUpToZoomIn)
                elif self.prefs.wheelMoveFunction == "moveZ":
                    strafeFactor = self.getMovementFactor(False, self.prefs.useGearsWheel)
                    self.move3dView(Vector((0, 0, -self.prefs.wheelDistance * strafeFactor if event.type == "WHEELUPMOUSE" else self.prefs.wheelDistance * strafeFactor)), Vector((0, 0, 0)))
                elif self.prefs.wheelMoveFunction == "changeStrafeSensitivity":
                    magnitude = 1 if event.type == "WHEELUPMOUSE" else -1
                    magnitude = magnitude * 5 if self.increasedMagnitude else magnitude
                    prefs = bpy.context.preferences.addons[MouseStrafingPreferences.bl_idname].preferences
                    prefs.sensitivityStrafe = nudgeValue(prefs.sensitivityStrafe, magnitude, self.increasedPrecision, self.strafeSensitivityRanges)
                    bpy.context.preferences.use_preferences_save = True
                    self.editStrafeSensitivityTime = time.perf_counter()
            elif event.type == self.prefs.keyCycleGears:
                if event.value == "PRESS":
                    self.cycleGear(context, event.shift, not self.keyCycleGearsDown)
                self.keyCycleGearsDown = getKeyDown(self.keyCycleGearsDown, event)
            elif event.type in {self.prefs.keyForward, self.prefs.keyLeft, self.prefs.keyBackward, self.prefs.keyRight, self.prefs.keyDown, self.prefs.keyUp}:
                self.updateKeys(context, event)
                if self.stopSignal is None:
                    self.stopSignal = [False]
                    pinnedSv3d, pinnedRv3d = self.sv3d, self.rv3d
                    pinnedStopSignal = self.stopSignal
                    bpy.app.timers.register(lambda: fpsMove(self, pinnedSv3d, pinnedRv3d, pinnedStopSignal))
            elif event.type in {"ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"}:
                self.keySaveStateDown = getKeyDown(self.keySaveStateDown, event)
                slotIndex = parseDigitString(event.type)
                if self.keySaveStateDown and self.keySaveStateSlotDown[slotIndex]:
                    return {"RUNNING_MODAL"}
                self.keySaveStateSlotDown[slotIndex] = self.keySaveStateDown
                if self.keySaveStateDown:
                    self.processSaveState(slotIndex, context)
                else:
                    self.loadedCameraState = False
            elif event.type == self.prefs.keyLoadCameraState:
                if event.value == "PRESS":
                    self.loadCameraState = not self.loadCameraState
            elif event.type == self.prefs.keyRelocatePivot:
                if event.value == "PRESS" and not self.keyDownRelocatePivot:
                    if event.shift:
                        self.prefs.adjustPivot = not self.prefs.adjustPivot
                        bpy.context.preferences.use_preferences_save = True
                        self.relocatePivotLock = True
                        self.adjustPivotSuccess = False
                    else:
                        self.relocatePivotLock = False
                        if self.prefs.adjustPivot:
                            self.prefs.adjustPivot = False
                            bpy.context.preferences.use_preferences_save = True
                self.keyDownRelocatePivot = getKeyDown(self.keyDownRelocatePivot, event)
                if self.keyDownRelocatePivot and not self.prefs.adjustPivot and not self.relocatePivotLock and not event.shift:
                    self.adjustPivot(context)
            elif event.type == self.prefs.keyResetRoll:
                if event.value == "PRESS":
                    self.resetRoll(context)
            elif event.type == "ESC":
                self.inEscape = getKeyDown(self.inEscape, event)
                return self.considerExitOperator(context)
            else:
                return {"RUNNING_MODAL"}
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        except:
            self.exitOperator(context, True)
            raise

    def getSatisfiedBinding(self) -> NavigationMouseButtonBinding:
        downButtons = []
        for button in ["lmb", "rmb", "mmb", "mb4", "mb5", "mb6", "mb7"]:
            if self.isButtonDown(button):
                downButtons.append(button)
        if len(downButtons) > 2 or len(downButtons) == 0:
            return None
        for binding in self.prefs.buttonBindings:
            if binding.button1 in downButtons and ((binding.button2 in downButtons and (binding.button2 != binding.button1 or len(downButtons) == 1)) or (binding.button2 == "omit" and len(downButtons) == 1)):
                return binding
        return None

    def isButtonDown(self, button: str) -> bool:
        return {"lmb": self.lmbDown, "rmb": self.rmbDown, "mmb": self.mmbDown, "mb4": self.mb4Down, "mb5": self.mb5Down, "mb6": self.mb6Down, "mb7": self.mb7Down}[button]

    def isAnyButtonDown(self) -> bool:
        return self.lmbDown or self.rmbDown or self.mmbDown or self.mb4Down or self.mb5Down or self.mb6Down or self.mb7Down

    def updateMode(self, context: bpy.types.Context, event: bpy.types.Event):
        self.lmbDown = event.value == "PRESS" if event.type == "LEFTMOUSE" else self.lmbDown
        self.rmbDown = event.value == "PRESS" if event.type == "RIGHTMOUSE" else self.rmbDown
        self.mmbDown = event.value == "PRESS" if event.type == "MIDDLEMOUSE" else self.mmbDown
        self.mb4Down = event.value == "PRESS" if event.type == "BUTTON4MOUSE" else self.mb4Down
        self.mb5Down = event.value == "PRESS" if event.type == "BUTTON5MOUSE" else self.mb5Down
        self.mb6Down = event.value == "PRESS" if event.type == "BUTTON6MOUSE" else self.mb6Down
        self.mb7Down = event.value == "PRESS" if event.type == "BUTTON7MOUSE" else self.mb7Down
        isAnyButtonDown = self.isAnyButtonDown()
        enteringMouseMode = isAnyButtonDown and not self.isInMouseAction
        leavingMouseMode = self.isInMouseAction and not isAnyButtonDown
        if enteringMouseMode:
            self.isInMouseAction = True
            context.window.cursor_set("NONE")
        elif leavingMouseMode:
            self.exitMouseMode(context)
            return self.considerExitOperator(context)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def updateKeys(self, context: bpy.types.Context, event: bpy.types.Event):
        wasWasding = self.isWasding
        self.keyDownForward = event.value == "PRESS" if event.type == self.prefs.keyForward else self.keyDownForward
        self.keyDownLeft = event.value == "PRESS" if event.type == self.prefs.keyLeft else self.keyDownLeft
        self.keyDownBackward = event.value == "PRESS" if event.type == self.prefs.keyBackward else self.keyDownBackward
        self.keyDownRight = event.value == "PRESS" if event.type == self.prefs.keyRight else self.keyDownRight
        self.keyDownDown = event.value == "PRESS" if event.type == self.prefs.keyDown else self.keyDownDown
        self.keyDownUp = event.value == "PRESS" if event.type == self.prefs.keyUp else self.keyDownUp
        self.isWasding = self.keyDownForward or self.keyDownLeft or self.keyDownBackward or self.keyDownRight or self.keyDownDown or self.keyDownUp
        if not wasWasding or not self.isWasding:
            self.wasdSpeedPercentage = 0.0
        if not wasWasding and self.isWasding:
            self.wasdStartTime = time.perf_counter()
            self.wasdPreviousTime = self.wasdStartTime

    def pan3dView(self, delta: Vector):
        viewPos, _viewDir = getViewPos(self.rv3d)
        viewRot = self.rv3d.view_rotation
        yawRot = Quaternion(Vector((0, 0, 1)), -delta[0])
        pitchAxis = Vector((1, 0, 0))
        pitchAxis.rotate(viewRot)
        pitchRot = Quaternion(pitchAxis, delta[1])
        viewRot.rotate(pitchRot)
        viewRot.rotate(yawRot)
        applyCameraTranformation(self.sv3d, self.rv3d, viewPos, viewRot)

    def roll3dView(self, delta: Vector):
        viewPos, rot, viewDir = prepareCameraTransformation(self.sv3d, self.rv3d)
        roll = Quaternion(viewDir, delta[0])
        rot.rotate(roll)
        applyCameraTranformation(self.sv3d, self.rv3d, viewPos, rot)

    def move3dView(self, delta: Vector, globalDelta: Vector):
        viewPos, rot, _viewDir = prepareCameraTransformation(self.sv3d, self.rv3d)
        delta.rotate(Quaternion(rot))
        viewPos = viewPos + delta + globalDelta
        applyCameraTranformation(self.sv3d, self.rv3d, viewPos, rot)

    def cycleGear(self, context: bpy.types.Context, gearDown: bool, allowWrap: bool):
        availableGears = self.getGears()
        gear, gearIndex = self.findGear(availableGears)
        if gearIndex == -1:
            return
        change = -1 if gearDown else 1
        gearIndex = gearIndex + change
        if not allowWrap:
            if gearIndex < 0:
                gearIndex = 0
            elif gearIndex >= len(availableGears):
                gearIndex = len(availableGears) - 1
        else:
            gearIndex = gearIndex % len(availableGears)
        self.prefs.strafeGearSelected = availableGears[gearIndex]
        bpy.context.preferences.use_preferences_save = True
        self.editGearTime = time.perf_counter()

    def getGears(self):
        availableGears = []
        for gear in self.prefs.strafeGears:
            if gear != 0.0:
                availableGears.append(gear)
        return availableGears

    def findGear(self, gears: list) -> (float, int):
        smallestError = math.inf
        smallestErrorGear = 1.0
        smallestErrorGearIndex = -1
        index = 0
        for gear in gears:
            error = abs(gear - self.prefs.strafeGearSelected)
            if error <= smallestError:
                smallestError = error
                smallestErrorGear = gear
                smallestErrorGearIndex = index
            index = index + 1
        return smallestErrorGear, smallestErrorGearIndex

    def snapGear(self):
        self.prefs.strafeGearSelected, _gearIndex = self.findGear(self.getGears())

    def nudgeFov(self, context: bpy.types.Context, zoomOut: bool):
        if self.rv3d.view_perspective == "CAMERA":
            if self.sv3d.lock_camera and self.sv3d.camera is not None and self.sv3d.camera.type == "CAMERA" and type(self.sv3d.camera.data) is bpy.types.Camera:
                cam = bpy.types.Camera(self.sv3d.camera.data)
                sensorSize = getSensorSize(context, cam)
                cam.lens = self.nudgeLensValue(cam.lens, sensorSize[0], sensorSize[1], self.prefs.altWheelMoveFunction, zoomOut)
                self.editFovTime = time.perf_counter()
        else:
            sensorSize = getSensorSizeView3d(context)
            self.sv3d.lens = self.nudgeLensValue(self.sv3d.lens, sensorSize[0], sensorSize[1], self.prefs.altWheelMoveFunction, zoomOut)
            self.editFovTime = time.perf_counter()

    def nudgeLensValue(self, lens: float, sensorWidth: float, sensorHeight: float, method: str, zoomOut: bool) -> float:
        magnitude = 1 if zoomOut else -1
        magnitude = -magnitude if method == "changeFOV" else magnitude
        magnitude = magnitude * 5 if self.increasedMagnitude else magnitude
        if method == "changeHFOV":
            return fovToFocalLength(nudgeValue(focalLengthToFov(lens, sensorWidth), magnitude, self.increasedPrecision, self.fovRanges), sensorWidth)
        elif method == "changeVFOV":
            return fovToFocalLength(nudgeValue(focalLengthToFov(lens, sensorHeight), magnitude, self.increasedPrecision, self.fovRanges), sensorHeight)
        return nudgeValue(lens, magnitude, self.increasedPrecision, self.focalLengthRanges)

    def processSaveState(self, saveStateSlot, context: bpy.types.Context):
        self.initSaveStates(context)
        now = time.perf_counter()
        states: CameraStates = context.scene.mstrf_camera_save_states
        if self.loadCameraState:
            if states.imminentSlot != 0:
                self.saveCameraState(states, states.imminentSlot, states.imminentState)
                states.imminentSlot = -1
            if states.usedStates[saveStateSlot]:
                self.applyCameraState(context, states.savedStates[saveStateSlot])
                self.loadedCameraState = True
            self.loadCameraState = False
        elif states.imminentSlot == saveStateSlot and self.imminentSaveStateTime > now - 1.0:
            if not states.usedStates[states.imminentSlot]:
                self.saveCameraState(states, states.imminentSlot, states.imminentState)
            self.applyCameraState(context, states.savedStates[saveStateSlot])
            self.loadedCameraState = True
            states.imminentSlot = -1
        else:
            self.loadedCameraState = False
            if states.imminentSlot >= 0:
                self.saveCameraState(states, states.imminentSlot, states.imminentState)
            viewPos, rot, _viewDir = prepareCameraTransformation(self.sv3d, self.rv3d)
            states.imminentState.viewPos = viewPos
            states.imminentState.rot = rot
            states.imminentState.viewDist = self.rv3d.view_distance
            states.imminentState.lens = self.sv3d.lens
            states.imminentState.isPerspective = self.rv3d.is_perspective
            states.imminentSlot = saveStateSlot
            self.imminentSaveStateTime = now

    def saveCameraState(self, states: CameraStates, slot, state: CameraState):
        states.usedStates[slot] = True
        states.savedStates[slot].viewPos = state.viewPos
        states.savedStates[slot].rot = state.rot
        states.savedStates[slot].viewDist = state.viewDist
        states.savedStates[slot].lens = state.lens
        states.savedStates[slot].isPerspective = state.isPerspective

    def applyCameraState(self, context:bpy.types.Context, cameraState: CameraState):
        if self.rv3d.is_perspective != cameraState.isPerspective:
            bpy.ops.view3d.view_persportho()
        self.rv3d.view_distance = cameraState.viewDist
        if not self.prefs.leaveFOV:
            self.sv3d.lens = cameraState.lens

        vP = cameraState.viewPos
        r = cameraState.rot
        applyCameraTranformation(self.sv3d, self.rv3d, Vector((vP[0], vP[1], vP[2])), Quaternion((r[0], r[1], r[2], r[3])))

    def getPanFactor(self):
        mod = 1.0
        if self.alternateControl:
            maxMod = 0.25
            mod = maxMod / ((self.getContextualFocalLength() / 50) if self.alternateControl else 1)
            if mod > maxMod:
                mod = maxMod
        if self.isPrecisionRequested():
            return mod * 0.5
        return mod

    def getRollFactor(self):
        mod = 1.0
        if self.alternateControl:
            mod = 0.25
        if self.isPrecisionRequested():
            return mod * 0.5
        return mod

    def getMovementFactor(self, isForMouseMovement: bool, useGear: bool) -> float:
        modStrafe = self.getMovementFactorModifier()
        gear = self.prefs.strafeGearSelected if useGear else 1
        if isForMouseMovement:
            return self.mouseSanityMultiplierStrafe * self.prefs.sensitivityStrafe * gear * modStrafe
        return gear * modStrafe

    def getMovementFactorModifier(self):
        if self.isHigherMagnitudeRequested():
            return 5
        if self.isPrecisionRequested():
            if self.alternateControl:
                return 0.02
            else:
                return 0.2
        if self.alternateControl:
            return 0.5
        return 1

    def getContextualFocalLength(self) -> float:
        if self.rv3d.view_perspective == "CAMERA" and self.sv3d.camera is not None and self.sv3d.camera.type == "CAMERA" and type(self.sv3d.camera.data) is bpy.types.Camera:
            cam = bpy.types.Camera(self.sv3d.camera.data)
            return cam.lens
        return self.sv3d.lens

    def isHigherMagnitudeRequested(self) -> bool:
        return self.increasedMagnitude and (self.increasedMagnitude != self.increasedPrecision)

    def isPrecisionRequested(self) -> bool:
        return self.increasedPrecision and (self.increasedPrecision != self.increasedMagnitude)

    def adjustPivot(self, context: bpy.types.Context):
        self.adjustPivotSuccess = False
        hit = None
        viewPos, rot, viewDir = prepareCameraTransformation(self.sv3d, self.rv3d)
        castStart = viewPos + viewDir * self.sv3d.clip_start
        castLength = self.sv3d.clip_end - self.sv3d.clip_start
        if self.prefs.pivotAdjustmentIgnoreBackfaces == "always" or (self.prefs.pivotAdjustmentIgnoreBackfaces == "whenCulling" and self.sv3d.shading.show_backface_culling):
            hit = rayCastIgnoringBackfaces(context.scene, context.window.view_layer.depsgraph, castStart, viewDir, castLength)
        else:
            hit = context.scene.ray_cast(context.window.view_layer.depsgraph, castStart, viewDir, distance = castLength)
        if hit[0]:
            newPivotPos = viewPos + (Vector(hit[1]) - viewPos) * (1.0 + self.prefs.pivotDig * 0.01)
            self.rv3d.view_distance = (newPivotPos - viewPos).length
            applyCameraTranformation(self.sv3d, self.rv3d, viewPos, rot, True)
            self.adjustPivotSuccess = True

    def resetRoll(self, context: bpy.types.Context):
        viewPos, rot, viewDir = prepareCameraTransformation(self.sv3d, self.rv3d)
        up = Vector((0, 1, 0))
        up.rotate(rot)
        py = getPitchYaw(viewDir, up)
        newRot = Quaternion(Vector((1, 0, 0)), py[0])
        if py[0] != 0:
            newRot.rotate(Quaternion(Vector((0, 0, 1)), py[1]))
        applyCameraTranformation(self.sv3d, self.rv3d, viewPos, newRot)

    def wasdDelta(self):
        now = time.perf_counter()
        moveFactor = self.getMovementFactor(False, self.prefs.useGearsWasd)
        delta = moveFactor * self.wasdSpeedPercentage * self.prefs.wasdTopSpeed * (now - self.wasdPreviousTime)
        self.wasdPreviousTime = now
        return delta
    
    def wasdAccelerate(self):
        if self.wasdSpeedPercentage < 1 and self.prefs.wasdTime > 0.0005:
            self.wasdSpeedPercentage = ((time.perf_counter() - self.wasdStartTime) / self.prefs.wasdTime)
            if self.wasdSpeedPercentage > 1:
                self.wasdSpeedPercentage = 1
        else:
            self.wasdSpeedPercentage = 1

    def exitMouseMode(self, context: bpy.types.Context):
        self.isInMouseAction = False
        self.centerMouse(context)
        context.window.cursor_set("DEFAULT")

    def centerMouse(self, context: bpy.types.Context):
        context.window.cursor_warp(context.region.x + context.region.width // 2, context.region.y + context.region.height // 2)
        self.ignoreMouseEvents = 1

    def resetMouse(self, context: bpy.types.Context, event: bpy.types.Event):
        if not (event.mouse_x < context.region.x + context.region.width // 4 or event.mouse_x > context.region.x + (3 * context.region.width) // 4 \
                or event.mouse_y < context.region.y + context.region.height // 4 or event.mouse_y > context.region.y + (3 * context.region.height) // 4):
            return
        target = (context.region.x + context.region.width // 2, context.region.y + context.region.height // 2)
        context.window.cursor_warp(target[0], target[1])
        self.previousDelta = Vector((event.mouse_x - event.mouse_prev_x, event.mouse_y - event.mouse_prev_y))
        self.bewareWarpDist = Vector((target[0] - event.mouse_x, target[1] - event.mouse_y)).length

    def considerExitOperator(self, context: bpy.types.Context):
        if self.shouldExitOperator():
            return self.exitOperator(context)
        return {"RUNNING_MODAL"}

    def shouldExitOperator(self):
        return (not self.prefs.toggleMode and not self.operatorKeyDown and not self.isInMouseAction) or (self.prefs.toggleMode and self.operatorKeyPresses > 0) or (self.inEscape)

    def exitOperator(self, context: bpy.types.Context, forceResetMouse: bool = False):
        global running
        global drawCallbackHandle
        if self.isInMouseAction or forceResetMouse:
            self.exitMouseMode(context)
        running = False
        if self.stopSignal is not None:
            self.stopSignal[0] = True
            self.stopSignal = None
        bpy.types.SpaceView3D.draw_handler_remove(drawCallbackHandle, "WINDOW")
        drawCallbackHandle = None
        if self.prefs.adjustPivot:
            self.adjustPivot(context)
        context.area.tag_redraw()
        return {"CANCELLED"}

def rayCastIgnoringBackfaces(scene: bpy.types.Scene, depsgraph, origin: Vector, direction: Vector, maxDistance: float):
    attemptCount = 0
    invert = False # there is no way to retrieve all hits, so we need to spam some rays back and forth.
    minCast = origin
    maxCast = origin + direction * maxDistance
    while attemptCount < 100:
        attemptCount = attemptCount + 1
        castDir = -direction if invert else direction
        castLength = (minCast - origin).dot(castDir) if invert else (maxCast - minCast).dot(castDir)
        if not invert and castLength <= 0:
            return rayCastMiss()
        hit = scene.ray_cast(depsgraph, origin, castDir, distance = castLength)
        if not hit[0]:
            return rayCastMiss()
        hitBackface = Vector(hit[2]).dot(direction) > 0
        if hitBackface:
            if invert:
                invert = not invert
                continue
            nudge = origin.length * 0.000001
            if nudge < 0.00001:
                nudge = 0.00001
            elif nudge > 0.004:
                nudge = 0.004
            origin = hit[1] + direction * nudge
            invert = not invert
            continue
        return hit
    return rayCastMiss()

def rayCastMiss():
    return (False, None, None, -1, None, None)

def clamp(x, min, max):
    return min if x < min else (max if x > max else x)

def magnitudeRepeat(nudgeFunc):
    def repeatNudgeFunc(value: float, magnitude: int, fine: bool, ranges: list) -> float:
        for i in range(0, -magnitude if magnitude < 0 else magnitude, 1):
            value = nudgeFunc(value, 1 if magnitude >= 0 else -1, fine, ranges)
        return value
    return repeatNudgeFunc

@magnitudeRepeat
def nudgeValue(value: float, magnitude: int, fine: bool, ranges: list) -> float:
    minimum = ranges[0][0]
    maximum = ranges[len(ranges) - 1]
    for i in range(len(ranges) - 2, -1, -1):
        if value+0.00001 >= ranges[i][0]:
            snappedValue = round(value, 3) if fine else round(value / ranges[i][1], 0) * ranges[i][1]
            if (snappedValue > value + 0.00001 and magnitude >= 0) or snappedValue < value - 0.00001 and magnitude < 0:
                value = snappedValue
                break
            value = snappedValue + (magnitude * 0.001 if fine else (ranges[i][1] if magnitude >= 0 else -ranges[i][1]))
            value = round(value, 3) if fine else round(value / ranges[i][1], 0) * ranges[i][1]
            if not fine and i > 0 and magnitude < 0 and value+0.00001 < ranges[i][0]:
                value = ranges[i][0] - ranges[i-1][1]
            break
    if value-0.00001 <= minimum:
        return minimum
    if value+0.00001 >= maximum:
        return maximum
    return value

def prepareCameraTransformation(sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D) -> (Vector, Quaternion, Vector):
    considerViewToCamera(sv3d, rv3d)
    viewPos, _viewDir = getViewPos(rv3d)
    viewRot = rv3d.view_rotation
    if rv3d.view_perspective == "CAMERA" and sv3d.lock_camera and sv3d.camera is not None:
        viewPos, viewRot, _viewScale = sv3d.camera.matrix_local.decompose()
    viewDir = Vector((0, 0, -1))
    viewDir.rotate(viewRot)
    return viewPos, viewRot, viewDir

def applyCameraTranformation(sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D, viewPos: Vector, viewRot: Quaternion, forceSetView = False):
    if not forceSetView and rv3d.view_perspective == "CAMERA" and sv3d.lock_camera and sv3d.camera is not None:
        axis, angle = viewRot.to_axis_angle()
        scale = sv3d.camera.matrix_local.to_scale()
        mat = mathutils.Matrix.Translation(viewPos) @ mathutils.Matrix.Rotation(angle, 4, axis) @ mathutils.Matrix.Diagonal(Vector((scale[0], scale[1], scale[2], 1)))
        sv3d.camera.matrix_local = mat
    else:
        rv3d.view_rotation = viewRot
        setViewPos(rv3d, viewPos)

def considerViewToCamera(sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D):
    if rv3d.view_perspective == "CAMERA" and not sv3d.lock_camera and sv3d.camera is not None:
        viewToCamera(sv3d, rv3d)
        rv3d.view_perspective = "PERSP"

def viewToCamera(sv3d: bpy.types.SpaceView3D, rv3d: bpy.types.RegionView3D):
    camera = sv3d.camera
    rv3d.view_rotation = camera.matrix_local.to_quaternion()
    setViewPos(rv3d, camera.location)

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
    if op.keyDownForward: op.move3dView(Vector((0, 0, -delta)), Vector((0, 0, 0)))
    if op.keyDownLeft: op.move3dView(Vector((-delta, 0, 0)), Vector((0, 0, 0)))
    if op.keyDownBackward: op.move3dView(Vector((0, 0, delta)), Vector((0, 0, 0)))
    if op.keyDownRight: op.move3dView(Vector((delta, 0, 0)), Vector((0, 0, 0)))
    if op.keyDownDown: op.move3dView(Vector((0, 0, 0)) if op.prefs.wasdGlobalZ else Vector((0, -delta, 0)), Vector((0, 0, -delta)) if op.prefs.wasdGlobalZ else Vector((0, 0, 0)))
    if op.keyDownUp: op.move3dView(Vector((0, 0, 0)) if op.prefs.wasdGlobalZ else Vector((0, delta, 0)), Vector((0, 0, delta)) if op.prefs.wasdGlobalZ else Vector((0, 0, 0)))
    return 0.001

def drawCallback(op: MouseStrafingOperator, context: bpy.types.Context):
    global drawCallbackHandle
    try:
        if context.area != op.area:
            return
        sv3d, rv3d = getViews3D(context)
        if rv3d != op.rv3d:
            return
        drawCrosshair(op, context)
        drawFovInfo(op, context)
        drawStrafeSensitivityInfo(op, context)
        drawGears(op, context)
        if op.redrawAfterDrawCallback:
            op.redrawAfterDrawCallback = False
            bpy.app.timers.register(context.area.tag_redraw, first_interval = 0)
    except:
        if drawCallbackHandle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(drawCallbackHandle, "WINDOW")
            drawCallbackHandle = None
        raise

def drawCrosshair(op: MouseStrafingOperator, context: bpy.types.Context):
    color = (0.75, 0.75, 0.75, 1)
    if op.keyDownRelocatePivot:
        if op.prefs.adjustPivot:
            color = (1, 1, 0.05, 1)
        elif op.adjustPivotSuccess:
            color = (0.1, 1, 0.05, 1)
        else:
            color = (1, 0.1, 0.05, 1)
    elif op.keySaveStateDown:
        if op.loadedCameraState:
            color = (1, 1, 1, 1)
        else:
            color = (1, 0.05, 1, 1)
    elif op.loadCameraState:
        color = (0.05, 0.15, 1, 1)
    elif op.getSatisfiedBinding() is not None:
        if not op.prefs.showCrosshair:
            return
        color = (1, 1, 1, 1)
    blf.color(0, *color)
    blf.enable(0, blf.SHADOW)
    blf.shadow(0, 3, 0, 0, 0, 1)
    uiScale = context.preferences.system.ui_scale
    blf.size(0, int(20*uiScale), 72)
    x, y = context.region.width // 2 - int(8*uiScale), context.region.height // 2 - int(6*uiScale)
    blf.position(0, x, y, 0)
    blf.draw(0, "+")

def drawFovInfo(op: MouseStrafingOperator, context: bpy.types.Context):
    alphaFactor = drawFadeAlpha(op, op.editFovTime, 1.0, 0.5)
    if alphaFactor == 0:
        return
    uiScale = context.preferences.system.ui_scale
    focalLength, sensorSize, hFov, vFov = None, None, None, None
    isCameraData = False
    if op.rv3d.view_perspective == "CAMERA" and op.sv3d.lock_camera and op.sv3d.camera is not None and op.sv3d.camera.type == "CAMERA" and type(op.sv3d.camera.data) is bpy.types.Camera:
        cam = bpy.types.Camera(op.sv3d.camera.data)
        sensorSize = getSensorSize(context, cam)
        focalLength = cam.lens
        isCameraData = True
    else:
        sensorSize = getSensorSizeView3d(context)
        focalLength = op.sv3d.lens
    hFov = focalLengthToFov(focalLength, sensorSize[0])
    vFov = focalLengthToFov(focalLength, sensorSize[1])

    textLens = f"      {focalLength:.3f}mm"
    textHFov = f"  {hFov:.3f}°"
    textVFov = f"  {vFov:.3f}°"

    blf.enable(0, blf.SHADOW)
    blf.shadow(0, 3, 0, 0, 0, alphaFactor)
    blf.size(0, int(20*uiScale), 72)
    x, y = context.region.width // 2, context.region.height // 2

    b = 1 if op.prefs.altWheelMoveFunction == "changeVFOV" else 0.75
    blf.color(0, b, b, b, alphaFactor)
    drawText(x + int(100*uiScale), y, textVFov, halign = "CENTER", valign = "MIDDLE")

    b = 1 if op.prefs.altWheelMoveFunction == "changeFOV" else 0.75
    blf.color(0, b, b, b, alphaFactor)
    drawText(x + int(50*uiScale), y - (25*uiScale), textLens, halign = "CENTER", valign = "MIDDLE")

    b = 1 if op.prefs.altWheelMoveFunction == "changeHFOV" else 0.75
    blf.color(0, b, b, b, alphaFactor)
    drawText(x, y - int(50*uiScale), textHFov, halign = "CENTER", valign = "MIDDLE")

    if isCameraData:
        blf.size(0, int(12*uiScale), 72)
        blf.color(0, 1, 0.5, 0.1, alphaFactor)
        drawText(x, y - int(95*uiScale), "Showing Camera Values", halign = "CENTER")

def drawStrafeSensitivityInfo(op: MouseStrafingOperator, context: bpy.types.Context):
    alphaFactor = drawFadeAlpha(op, op.editStrafeSensitivityTime, 1.0, 0.5)
    if alphaFactor == 0:
        return
    x, y = context.region.width // 2, context.region.height // 2
    blf.enable(0, blf.SHADOW)
    blf.shadow(0, 3, 0, 0, 0, alphaFactor)
    uiScale = context.preferences.system.ui_scale
    blf.size(0, int(20*uiScale), 72)
    blf.color(0, 1, 1, 1, alphaFactor)
    drawText(x, y + int(40*uiScale), f"{op.prefs.sensitivityStrafe:.3f}", halign = "CENTER")

def drawGears(op: MouseStrafingOperator, context: bpy.types.Context):
    alphaFactor = drawFadeAlpha(op, op.editGearTime, 1.0, 0.5)
    if alphaFactor == 0:
        return
    x, y = context.region.width // 2, context.region.height // 2
    blf.enable(0, blf.SHADOW)
    blf.shadow(0, 3, 0, 0, 0, alphaFactor)
    uiScale = context.preferences.system.ui_scale
    blf.size(0, int(20*uiScale), 72)
    blf.color(0, 1, 1, 1, alphaFactor)
    availableGears = op.getGears()
    yoffset = ((len(availableGears) - 1) * 25) / 2
    index = 0
    for gear in availableGears:
        if gear == op.prefs.strafeGearSelected:
            blf.color(0, 1, 1, 1, alphaFactor)
        else:
            blf.color(0, 0.75, 0.75, 0.75, alphaFactor)
        drawText(x - (110*uiScale), y - int((yoffset-index*25)*uiScale), f"{gear:0.3f}", halign = "CENTER", valign = "MIDDLE")
        index = index + 1

def drawFadeAlpha(op: MouseStrafingOperator, wakeTime: float, holdTime: float, fadeTime: float) -> float:
    now = time.perf_counter()
    passed = now - wakeTime
    alphaFactor = 1.0
    if passed > holdTime:
        alphaFactor = 1.0 - (passed - holdTime) / fadeTime
    if alphaFactor <= 0:
        alphaFactor = 0.0
    else:
        op.redrawAfterDrawCallback = True
    return alphaFactor

def getSensorSizeView3d(context: bpy.types.Context) -> (float, float):
    sensorWidth = 72.0
    aspect = context.region.width / context.region.height
    if aspect < 1:
        sensorWidth = sensorWidth * aspect
    sensorHeight = sensorWidth / aspect
    return (sensorWidth, sensorHeight)

def getSensorSize(context: bpy.types.Context, cam: bpy.types.Camera) -> (float, float):
    aspect = (context.scene.render.resolution_x / context.scene.render.pixel_aspect_y) / (context.scene.render.resolution_y / context.scene.render.pixel_aspect_x)
    sensorWidth = cam.sensor_width
    sensorHeight = cam.sensor_height
    if cam.sensor_fit == "AUTO":
        if aspect < 1:
            sensorWidth = sensorWidth * aspect
        sensorHeight = sensorWidth / aspect
    elif cam.sensor_fit == "HORIZONTAL":
        sensorHeight = sensorWidth / aspect
    elif cam.sensor_fit == "VERTICAL":
        sensorWidth = sensorHeight * aspect
    return (sensorWidth, sensorHeight)

def focalLengthToFov(focalLength: float, sensorSideLength: float) -> float:
    return math.degrees(2 * math.atan(sensorSideLength / 2 / focalLength))

def fovToFocalLength(fov: float, sensorSideLength: float) -> float:
    return sensorSideLength / 2 / math.tan(math.radians(fov)/2)

def drawText(x: int, y: int, text: str, halign: str = "LEFT", valign: str = "BASELINE"):
    dims = blf.dimensions(0, text)
    if halign == "CENTER":
        x = x - dims[0]/2
    elif halign == "RIGHT":
        x = x - dims[0]
    if valign == "MIDDLE":
        y = y - dims[1]/2
    blf.position(0, x, y, 0)
    blf.draw(0, text)

def parseDigitString(s):
    options = { \
        "ZERO":  0, \
        "ONE":   1, \
        "TWO":   2, \
        "THREE": 3, \
        "FOUR":  4, \
        "FIVE":  5, \
        "SIX":   6, \
        "SEVEN": 7, \
        "EIGHT": 8, \
        "NINE":  9, \
    }
    return options[s]

km = None
kmi = None

def register_keymaps():
    global km
    global kmi
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name = "3D View", space_type = "VIEW_3D", region_type = "WINDOW", modal=False)
        kmi = km.keymap_items.new(MouseStrafingOperator.bl_idname, "SPACE", "PRESS", head=True)

def unregister_keymaps():
    global km
    global kmi
    km.keymap_items.remove(kmi)

# Mouse Strafing Addon for Blender
# Copyright (C) 2019 Zyl
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import math
import time

import bpy
import blf
from mathutils import Vector
from mathutils import Quaternion

from .prefs import MouseStrafingPreferences

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

def scaleDelta(delta, distance, sensitivity) -> float:
    unadjustedDistance = signExp(1000 * 0.1 / 20, sensitivity) * 20
    return signExp(delta * 0.1, sensitivity) * (distance / unadjustedDistance)

running = False

class MouseStrafingOperator(bpy.types.Operator):
    """Strafe in the 3D View using the mouse."""
    bl_idname = "view_3d.mouse_strafing"
    bl_label = "Mouse Strafing"
    bl_options = { "REGISTER", "BLOCKING" }

    wasdKeys = [ "W", "A", "S", "D", "Q", "E" ]
    inFast, inSlow = False, False

    lmbDown, rmbDown, mmbDown = False, False, False
    isClicking = False

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
    drawCallbackHandle = None
    
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        global running
        if not running and event.value == "PRESS":
            self.area = context.area
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
        self.inFast, self.inSlow = event.shift, event.ctrl or event.alt
        if event.type == kmi.type and event.value == "RELEASE":
            return self.exitOperator(context)
        elif event.type in [ "LEFTMOUSE", "RIGHTMOUSE", "MIDDLEMOUSE" ]:
            return self.updateMode(context, event)
        elif event.type == "MOUSEMOVE":
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
            mod = self.modScale(True)
            self.move3dView(getSpaceView3D(context).region_3d, \
                Vector((0, 0, -self.prefs.wheelDistance * mod if event.type == "WHEELUPMOUSE" else self.prefs.wheelDistance * mod)), \
                Vector((0, 0, 0)))
            return {"RUNNING_MODAL"}
        elif event.type in self.wasdKeys:
            if self.stopSignal is None:
                self.stopSignal = [False]
                pinnedStopSignal = self.stopSignal
                pinnedRv3d = getSpaceView3D(context).region_3d
                bpy.app.timers.register(lambda: fpsMove(self, pinnedRv3d, pinnedStopSignal))
            return self.updateKeys(context, event)
        elif event.type == "C":
            self.cDown = event.value == "PRESS" if event.type == "C" else self.cDown
            if event.value == "PRESS":
                self.adjustPivot(context)
            context.area.tag_redraw()
            return {"RUNNING_MODAL"}
        return {"PASS_THROUGH"}

    def modScale(self, allowFast):
        return 1 if self.inFast == self.inSlow else (5 if allowFast else 1) if self.inFast else 0.2

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
            self.exitStrafe(context)
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
        xDelta = event.mouse_x - event.mouse_prev_x
        yDelta = event.mouse_y - event.mouse_prev_y
        modStrafe = self.modScale(True)
        modTurn = self.modScale(False)
        if action == "turnXY":
            self.pan3dView(getSpaceView3D(context).region_3d, Vector((xDelta * modTurn, -yDelta * modTurn if self.prefs.invertMouse else yDelta * modTurn)), \
                self.prefs.sensitivityWasd if self.isWasding else self.prefs.sensitivityDefault)
        else:
            xDeltaStrafe = modStrafe * scaleDelta(xDelta, self.prefs.strafingDistance, self.prefs.strafingPotential)
            yDeltaStrafe = modStrafe * scaleDelta(yDelta, self.prefs.strafingDistance, self.prefs.strafingPotential)
            if action == "strafeXZ":
                self.move3dView(getSpaceView3D(context).region_3d, Vector((xDeltaStrafe, 0, -yDeltaStrafe)), Vector((0, 0, 0)))
            elif action == "strafeXY":
                self.move3dView(getSpaceView3D(context).region_3d, Vector((xDeltaStrafe, yDeltaStrafe, 0)), Vector((0, 0, 0)))
            elif action == "strafeXRappel":
                self.move3dView(getSpaceView3D(context).region_3d, Vector((xDeltaStrafe, 0, 0)), Vector((0, 0, yDeltaStrafe)))
            elif action == "turnXRappel":
                self.move3dView(getSpaceView3D(context).region_3d, Vector((0, 0, 0)), Vector((0, 0, yDeltaStrafe)))
                self.pan3dView(getSpaceView3D(context).region_3d, Vector((xDelta * modTurn, 0)), self.prefs.sensitivityRappel)

    def pan3dView(self, rv3d: bpy.types.RegionView3D, delta: Vector, sensitivity):
        if sensitivity == 0:
            return
        viewPos, _viewDir = getViewPos(rv3d)
        rot = Quaternion(rv3d.view_rotation)
        yawRot = Quaternion(Vector((0, 0, 1)), -delta[0]*0.017453292*sensitivity)
        pitchAxis = Vector((1, 0, 0))
        pitchAxis.rotate(rot)
        pitchRot = Quaternion(pitchAxis, delta[1]*0.017453292*sensitivity)
        rot.rotate(pitchRot)
        rot.rotate(yawRot)
        rv3d.view_rotation = rot
        setViewPos(rv3d, viewPos)

    def move3dView(self, rv3d: bpy.types.RegionView3D, delta: Vector, globalDelta: Vector):
        delta.rotate(Quaternion(rv3d.view_rotation))
        rv3d.view_location = rv3d.view_location + delta + globalDelta

    def wasdDelta(self):
        now = time.perf_counter()
        delta = self.modScale(True) * self.wasdCurSpeed * (now - self.wasdPreviousTime)
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

    def exitOperator(self, context: bpy.types.Context):
        global running
        running = False
        if self.isClicking:
            self.exitStrafe(context)
        if self.stopSignal is not None:
            self.stopSignal[0] = True
            self.stopSignal = None
        if self.prefs.adjustPivot:
            self.adjustPivot(context)
        bpy.types.SpaceView3D.draw_handler_remove(self.drawCallbackHandle, "WINDOW")
        context.area.tag_redraw()
        return {"CANCELLED"}

    def adjustPivot(self, context: bpy.types.Context):
        sv3d = getSpaceView3D(context)
        rv3d = sv3d.region_3d
        viewPos, viewDir = getViewPos(rv3d)
        castStart = viewPos + viewDir * sv3d.clip_start
        self.adjustPivotSuccess = False
        attemptCount = 0
        while attemptCount < 100:
            attemptCount = attemptCount + 1
            hit = context.scene.ray_cast(context.window.view_layer, castStart, viewDir, \
                distance = sv3d.clip_end - sv3d.clip_start)
            if not hit[0]:
                break
            isLookingAtBackface = Vector(hit[2]).dot(viewDir) > 0
            if isLookingAtBackface and sv3d.shading.show_backface_culling:
                nudge = castStart.length * 0.00001
                if nudge < 0.00001:
                    nudge = 0.00001
                castStart = hit[1] + viewDir * nudge
                continue
            newPivotPos = viewPos + (Vector(hit[1]) - viewPos) * (1.0 + self.prefs.pivotDig * 0.01)
            rv3d.view_distance = (newPivotPos - viewPos).length
            self.adjustPivotSuccess = hit
            setViewPos(rv3d, viewPos)
            self.adjustPivotSuccess = True
            break;

    def centerMouse(self, context: bpy.types.Context):
        context.window.cursor_warp(context.region.x + context.region.width // 2, context.region.y + context.region.height // 2)
    
    def resetMouse(self, context: bpy.types.Context, event: bpy.types.Event):
        context.window.cursor_warp(context.region.x + context.region.width // 2 - (event.mouse_x - event.mouse_prev_x)*0.5, \
            context.region.y + context.region.height // 2 - (event.mouse_y - event.mouse_prev_y)*0.5)

def fpsMove(op: MouseStrafingOperator, rv3d: bpy.types.RegionView3D, stopSignal):
    if not running or stopSignal[0]: return None
    if op.isWasding: op.wasdAccelerate()
    delta = op.wasdDelta()
    if op.wDown: op.move3dView(rv3d, Vector((0, 0, -delta)), Vector((0, 0, 0)))
    if op.aDown: op.move3dView(rv3d, Vector((-delta, 0, 0)), Vector((0, 0, 0)))
    if op.sDown: op.move3dView(rv3d, Vector((0, 0, delta)), Vector((0, 0, 0)))
    if op.dDown: op.move3dView(rv3d, Vector((delta, 0, 0)), Vector((0, 0, 0)))
    if op.qDown: op.move3dView(rv3d, Vector((0, -delta, 0)), Vector((0, 0, 0)))
    if op.eDown: op.move3dView(rv3d, Vector((0, delta, 0)), Vector((0, 0, 0)))
    return 0.001

def drawCallback(op: MouseStrafingOperator, context: bpy.types.Context, event: bpy.types.Event):
    if context.area != op.area:
        return
    if op.prefs.showCrosshair:
        x, y = context.region.width // 2 - 8, context.region.height // 2 - 7
        fontId = 0
        blf.size(fontId, 20, 72)
        blf.color(fontId, 0, 0, 0, 0.8)
        blf.position(fontId, x, y, 0)
        blf.draw(fontId, "+")
        color = ((0.1, 1, 0.05, 1) if op.adjustPivotSuccess else (1, 0.1, 0.05, 1)) if op.cDown else \
            (1, 1, 1, 1) if op.isClicking else (0.75, 0.75, 0.75, 1)
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

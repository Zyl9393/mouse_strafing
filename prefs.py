import bpy

class NavigationMouseButtonBinding(bpy.types.PropertyGroup):

    def markPreferencesForSaving(self, context):
        bpy.context.preferences.use_preferences_save = True

    mouseButtonItems = [ \
        ("lmb", "LMB", "Left Mouse Button", "NONE", 1), \
        ("rmb", "RMB", "Right Mouse Button", "NONE", 2), \
        ("mmb", "MMB", "Middle Mouse Button", "NONE", 3), \
        ("mb4", "MB4", "Mouse Button 4", "NONE", 4), \
        ("mb5", "MB5", "Mouse Button 5", "NONE", 5), \
        ("mb6", "MB6", "Mouse Button 6", "NONE", 6), \
        ("mb7", "MB7", "Mouse Button 7", "NONE", 7)]
    mouseButtonItemsOmitable = [("omit", "-", "Omit: make this binding for a single mouse button instead of a combination of two", "NONE", 0)] + mouseButtonItems
    button1: bpy.props.EnumProperty(name = "Button 1", description = "Button to press to activate this binding", items = mouseButtonItems, default = "lmb", options = {"HIDDEN"}, update = markPreferencesForSaving)
    button2: bpy.props.EnumProperty(name = "Button 2", description = "Button which also has to be held for this binding", items = mouseButtonItemsOmitable, default = "omit", options = {"HIDDEN"}, update = markPreferencesForSaving)

    navigationActionItems = [ \
        ("turnXY", "Look around", "Look around (Essential)", "NONE", 0), \
        ("strafeXZ", "Strafe left/right/forward/backwards", "Strafe left/right/forward/backwards (Essential)", "NONE", 1), \
        ("strafeXY", "Strafe left/right/up/down", "Strafe left/right/up/down (Essential)", "NONE", 2), \
        ("strafeXRappel", "Strafe left/right and rappel", "Strafe left/right and rappel (move up/down world Z-axis)", "NONE", 3), \
        ("turnXRappel", "Turn left/right and rappel", "Turn left/right and rappel (move up/down world Z-axis)", "NONE", 4), \
        ("roll", "Roll the camera", "Roll the camera (press R to reset roll)", "NONE", 5)]
    action: bpy.props.EnumProperty(name = "Action", description = "Set navigation method to use while holding specified buttons", items = navigationActionItems, default = "turnXY", update = markPreferencesForSaving)

    def equals(self, other):
        return other is not None and ((self.button1 == other.button1 and self.button2 == other.button2) or (self.button1 == other.button2 and self.button2 == other.button1)) and self.action == other.action

class AddButtonBinding(bpy.types.Operator):
    """Add Mouse Button Binding"""
    bl_idname = "view3d.mouse_strafing_add_button_binding"
    bl_label = "Add Mouse Button Binding"
    def invoke(self, context, event):
        prefs: MouseStrafingPreferences = bpy.context.preferences.addons[MouseStrafingPreferences.bl_idname].preferences
        prefs.buttonBindings.add()
        bpy.context.preferences.use_preferences_save = True
        return {"FINISHED"}

class RemoveButtonBinding(bpy.types.Operator):
    """Remove Mouse Button Binding"""
    bl_idname = "view3d.mouse_strafing_remove_button_binding"
    bl_label = "Remove Mouse Button Binding"
    index: bpy.props.IntProperty()
    def invoke(self, context, event):
        prefs: MouseStrafingPreferences = bpy.context.preferences.addons[MouseStrafingPreferences.bl_idname].preferences
        prefs.buttonBindings.remove(self.index)
        bpy.context.preferences.use_preferences_save = True
        return {"FINISHED"}

class MoveButtonBindingUp(bpy.types.Operator):
    """Move Mouse Button Binding up"""
    bl_idname = "view3d.mouse_strafing_move_button_binding_up"
    bl_label = "Move Mouse Button Binding up"
    index: bpy.props.IntProperty()
    def invoke(self, context, event):
        prefs: MouseStrafingPreferences = bpy.context.preferences.addons[MouseStrafingPreferences.bl_idname].preferences
        prefs.buttonBindings.move(self.index, self.index-1)
        bpy.context.preferences.use_preferences_save = True
        return {"FINISHED"}

class MoveButtonBindingDown(bpy.types.Operator):
    """Move Mouse Button Binding down"""
    bl_idname = "view3d.mouse_strafing_move_button_binding_down"
    bl_label = "Move Mouse Button Binding down"
    index: bpy.props.IntProperty()
    def invoke(self, context, event):
        prefs: MouseStrafingPreferences = bpy.context.preferences.addons[MouseStrafingPreferences.bl_idname].preferences
        prefs.buttonBindings.move(self.index, self.index+1)
        bpy.context.preferences.use_preferences_save = True
        return {"FINISHED"}

class MouseStrafingPreferences(bpy.types.AddonPreferences):
    bl_idname = "mouse_strafing"

    buttonBindings: bpy.props.CollectionProperty(type = NavigationMouseButtonBinding, name = "Mouse button bindings", description = "Specify which mouse button or mouse button combination engages which navigation behavior")

    sensitivityPan: bpy.props.FloatProperty(name = "Pan Sensitivity", description = "Mouse speed multiplier when panning the 3D View", \
        default = 1.0, min = 0.001, max = 100.0, soft_min = 0.01, soft_max = 10.0, step = 1, precision = 3)
    sensitivityStrafe: bpy.props.FloatProperty(name = "Strafe Sensitivity", description = "Mouse speed multiplier for mouse strafing", \
        default = 1.0, min = 0.001, soft_min = 0.01, max = 100.0, soft_max = 10.0, step = 1, precision = 3)
    increasedMagnitudeSpeedFactor: bpy.props.FloatProperty(name = "Fast Speed Factor", description = "Strafe speed multiplier to apply while holding magnitude key (default is Shift)", default = 5, min = 1, max = 100, soft_min = 1.2, soft_max = 10)
    increasedPrecisionSpeedFactor: bpy.props.FloatProperty(name = "Slow Speed Factor", description = "Strafe speed multiplier to apply while holding precision key (default is Alt)", default = 0.2, min = 0.01, max = 1, soft_min = 0.1, soft_max = 0.8)
    strafeGears: bpy.props.FloatVectorProperty(name = "Gears", description = "Set additional strafe speed multipliers to cycle through with G and Shift + G. Entries set to 0 are ignored", \
        size = 7, default = (0.025, 0.1, 0.333, 1.0, 3.00, 0, 0), min = 0.0, max = 100.0, soft_min = 0.0, soft_max = 10.0, step = 5, precision = 2)
    strafeGearSelected: bpy.props.FloatProperty(name = "Selected Gear", default = 1.0, options = {"HIDDEN"})

    invertMouseX: bpy.props.BoolProperty(name = "Invert Horizontal Panning", description = "Invert effect of horizontal mouse movement when looking around", default = False)
    invertMouse: bpy.props.BoolProperty(name = "Invert Vertical Panning", description = "Invert effect of vertical mouse movement when looking around", default = False)

    invertStrafeX: bpy.props.BoolProperty(name = "Invert Strafe X", description = "Invert direction of sideways mouse strafe movement", default = False)
    invertStrafeY: bpy.props.BoolProperty(name = "Invert Strafe Y", description = "Invert direction of upwards/downwards mouse strafe movement", default = False)
    invertStrafeZ: bpy.props.BoolProperty(name = "Invert Strafe Z", description = "Invert direction of forwards/backwards mouse strafe movement", default = False)

    wasdTopSpeed: bpy.props.FloatProperty(name = "WASD Top Speed", description = "Top speed, in units per second, when using WASD keys to move", \
        default = 8.0, min = 0.001, max = 20000, soft_min = 0.01, soft_max = 4000, step = 10, precision = 2)
    wasdTime: bpy.props.FloatProperty(name = "WASD Acceleration Time", description = "Time, in seconds, until top speed is reached when using WASD keys to move", \
        default = 0.2, min = 0.0, max = 4.0, soft_min = 0.0, soft_max = 1000, step = 1, precision = 2)
    wasdGlobalZ: bpy.props.BoolProperty(name = "Use Global Z", description = "When checked, makes WASD up/down movement aligned to global Z-axis instead of view Z-axis", default = False)
    useGearsWasd: bpy.props.BoolProperty(name = "Apply Gear to WASD Speed", description = "When checked, apply gear strafe speed multiplier to WASD move distance, too", default = True)

    def getUnusedModifierKey(self):
        keys = {"ctrl", "shift", "alt"}
        keys.discard(self.increasedMagnitudeKey)
        keys.discard(self.increasedPrecisionKey)
        keys.discard(self.changedBehaviorKey)
        return list(keys)[0]

    def updateIncreasedMagnitudeKey(self, context):
        if self.increasedMagnitudeKey == "omit":
            return
        if self.increasedPrecisionKey == self.increasedMagnitudeKey:
            self.increasedPrecisionKey = self.getUnusedModifierKey()
        if self.changedBehaviorKey == self.increasedMagnitudeKey:
            self.changedBehaviorKey = self.getUnusedModifierKey()

    def updateIncreasedPrecisionKey(self, context):
        if self.increasedPrecisionKey == "omit":
            return
        if self.increasedMagnitudeKey == self.increasedPrecisionKey:
            self.increasedMagnitudeKey = self.getUnusedModifierKey()
        if self.changedBehaviorKey == self.increasedPrecisionKey:
            self.changedBehaviorKey = self.getUnusedModifierKey()

    def updateChangedBehaviorKey(self, context):
        if self.changedBehaviorKey == "omit":
            return
        if self.increasedMagnitudeKey == self.changedBehaviorKey:
            self.increasedMagnitudeKey = self.getUnusedModifierKey()
        if self.increasedPrecisionKey == self.changedBehaviorKey:
            self.increasedPrecisionKey = self.getUnusedModifierKey()

    modifierKeyItems = [ \
        ("ctrl", "Ctrl", "The control (Ctrl) key", "NONE", 0), \
        ("shift", "Shift", "The shift key", "NONE", 1), \
        ("alt", "Alt", "The alternate (Alt) key", "NONE", 2), \
        ("omit", "Omit", "Disables modifications by associating no modifier key with it", "NONE", 3) ]
    increasedMagnitudeKey: bpy.props.EnumProperty(name = "Magnitude Key", description = "Specify key which increases action magnitude (move faster, increase increment size) while held", items = modifierKeyItems, default = "shift", update = updateIncreasedMagnitudeKey)
    increasedPrecisionKey: bpy.props.EnumProperty(name = "Precision Key", description = "Specify key which increases action precision (move slower, decrease increment size) while held", items = modifierKeyItems, default = "alt", update = updateIncreasedPrecisionKey)
    changedBehaviorKey: bpy.props.EnumProperty(name = "Alternate Key", description = "Specify key which engages alternate action (pan/roll slower, alternative mouse wheel function) while held", items = modifierKeyItems, default = "ctrl", update = updateChangedBehaviorKey)

    mouseWheelActionItems = [ \
        ("moveZ", "Move forward/backwards", "Move forward/backwards", "NONE", 0), \
        ("changeStrafeSensitivity", "Change strafe sensitivity", "Change the mouse speed multiplier for mouse strafing", "NONE", 1)]
    wheelMoveFunction: bpy.props.EnumProperty(name = "Wheel", description = "Set what the scroll wheel does", items = mouseWheelActionItems, default = "moveZ")

    altMouseWheelActionItems = [ \
        ("changeFOV", "Change Focal Length", "Change the field of view (FOV) by controlling the distance of the lens to the camera sensor", "NONE", 0), \
        ("changeHFOV", "Change Horizontal FOV", "Change the field of view (FOV) by controlling the horizontal view angle", "NONE", 1), \
        ("changeVFOV", "Change Vertical FOV", "Change the field of view (FOV) by controlling the vertical view angle", "NONE", 2)]
    altWheelMoveFunction: bpy.props.EnumProperty(name = "Wheel (Alt)", description = "Set what the scroll wheel does while holding alternate key (default is Ctrl)", items = altMouseWheelActionItems, default = "changeVFOV")

    wheelDistance: bpy.props.FloatProperty(name = "Wheel Distance", description = "Set move distance when using the scroll wheel to move", \
        default = 0.5, min = -1000.0, max = 1000.0, soft_min = -5.0, soft_max = 5.0, step = 1, precision = 4)
    useGearsWheel: bpy.props.BoolProperty(name = "Apply Gear to Wheel Distance", description = "When checked, apply gear strafe speed multiplier to scroll wheel move distance, too", default = True)
    scrollUpToZoomIn: bpy.props.BoolProperty(name = "Invert Direction", description = "When checked, inverts the scroll wheel direction such that scrolling up zooms in and scrolling down zooms out", default = False)

    showCrosshair: bpy.props.BoolProperty(name = "Show Crosshair", description = "Show crosshair during strafe actions", default = True)
    adjustPivot: bpy.props.BoolProperty(name = "Automatically Relocate Pivot", description = "Automatically relocate the 3D View's "
        "pivot point (instead of manually by pressing 'C') to the surface of whatever object you are looking at while using the operator; you can toggle this with Shift + C", default = True)
    pivotDig: bpy.props.FloatProperty(name = "Pivot Dig", description = "When relocating the pivot point, specifies how far the pivot will be moved into the surface you are looking at, based on a percentage of its distance to the 3D View camera", \
        default = 0.0, min = 0.0, max = 100.0, soft_min = 0.0, soft_max = 100.0, step = 100, precision = 0, subtype = "PERCENTAGE")

    pivotAdjustmentIgnoreBackfacesItems = [ \
        ("whenCulling", "When culling", "When adjusting the pivot, ignore backfaces if backface culling is enabled", "NONE", 0), \
        ("always", "Always", "When adjusting the pivot, always respect backfaces", "NONE", 1), \
        ("never", "Never", "When adjusting the pivot, always ignore backfaces", "NONE", 2)]
    pivotAdjustmentIgnoreBackfaces: bpy.props.EnumProperty(name = "Ignore Backfaces", description = "Set when to ignore backfaces when adjusting the view pivot", items = pivotAdjustmentIgnoreBackfacesItems, default = "whenCulling")

    debug: bpy.props.BoolProperty(name = "Debug Mode", description = "When checked, print in the console when Blender's cursor_warp glitch is detected and countered", default = False)
    toggleMode: bpy.props.BoolProperty(name = "Toggle", description = "When checked, strafe-mode will only quit when pressing the key a second time or pressing Escape", default = False)
    leaveFOV: bpy.props.BoolProperty(name = "Leave FOV", description = "When checked, loading camera states will leave the FOV as it is", default = False)

    keyForward: bpy.props.StringProperty(name = "Move Forward", description = "Press this key to move the camera forward (must be upper-case)", default = "W")
    keyBackward: bpy.props.StringProperty(name = "Move Backward", description = "Press this key to move the camera backward (must be upper-case)", default = "S")
    keyLeft: bpy.props.StringProperty(name = "Move Left", description = "Press this key to strafe the camera to the left (must be upper-case)", default = "A")
    keyRight: bpy.props.StringProperty(name = "Move Right", description = "Press this key to stafe the camera to the right (must be upper-case)", default = "D")
    keyUp: bpy.props.StringProperty(name = "Move Up", description = "Press this key to strafe the camera upwards (must be upper-case)", default = "E")
    keyDown: bpy.props.StringProperty(name = "Move Down", description = "Press this key to strafe the camera downwards (must be upper-case)", default = "Q")
    keyResetRoll: bpy.props.StringProperty(name = "Reset Roll", description = "Press this key to reset camera roll (must be upper-case)", default = "R")

    keyCycleGears: bpy.props.StringProperty(name = "Cycle Gear", description = "Press this key to cycle through strafing gears (must be upper-case)", default = "G")
    keyRelocatePivot: bpy.props.StringProperty(name = "Relocate Pivot", description = "Press this key to relocate camera pivot to the nearest surface in the center of the view. You can toggle this to happen automatically on and off with Shift + this key (must be upper-case)", default = "C")
    keyLoadCameraState: bpy.props.StringProperty(name = "Load Camera State", description = "Press this key and then one of the number keys [0-9] to load the camera state in that slot without the need to quickly press the number key twice (must be upper-case)", default = "T")

    def draw(self, context: bpy.types.Context):
        layout: bpy.types.UILayout = self.layout

        self.drawButtonBindings(layout)
        self.drawMouseMovePrefs(layout)
        self.drawActionPrefs(layout)
        self.drawPivotAdjustmentPrefs(layout)
        self.drawWasdPrefs(layout)
        self.drawMiscPrefs(layout)
        self.drawModifierKeyPrefs(layout)
        self.drawKeyBindPrefs(layout)

    def drawButtonBindings(self, layout: bpy.types.UILayout):
        box = layout.box()

        i = 0
        for binding in self.buttonBindings:
            row = box.row().split(factor = 0.25)
            buttonColumnRow = row.column().row()
            buttonColumnRow.prop(binding, "button1", text = "")
            buttonColumnRow.prop(binding, "button2", text = "")
            row = row.column().row()
            row.prop(binding, "action", text = "")
            opUpDiv = row.row()
            opUpDiv.enabled = i > 0
            opUpDiv.operator("view3d.mouse_strafing_move_button_binding_up", icon = "TRIA_UP", text = "").index = i
            upDownDiv = row.row()
            upDownDiv.enabled = i < len(self.buttonBindings) - 1
            upDownDiv.operator("view3d.mouse_strafing_move_button_binding_down", icon = "TRIA_DOWN", text = "").index = i
            row.operator("view3d.mouse_strafing_remove_button_binding", icon = "REMOVE", text = "").index = i
            i += 1
        if len(self.buttonBindings) < 20:
            row = box.row()
            row.operator("view3d.mouse_strafing_add_button_binding")

    def drawMouseMovePrefs(self, layout: bpy.types.UILayout):
        box = layout.box()

        row = box.row()
        row.prop(self, "sensitivityPan")
        row.prop(self, "sensitivityStrafe")

        row = box.row()
        row.prop(self, "increasedMagnitudeSpeedFactor")
        row.prop(self, "increasedPrecisionSpeedFactor")

        row = box.row()
        row.prop(self, "strafeGears")

        row = box.row()
        row.prop(self, "invertMouse")
        row.prop(self, "invertMouseX")

        row = box.row()
        row.prop(self, "invertStrafeX")
        row.prop(self, "invertStrafeY")
        row.prop(self, "invertStrafeZ")

    def drawActionPrefs(self, layout: bpy.types.UILayout):
        box = layout.box()

        row = box.row()
        row.prop(self, "wheelMoveFunction")
        if self.wheelMoveFunction == "moveZ":
            row = box.row()
            row.prop(self, "wheelDistance")
            row.prop(self, "useGearsWheel")

        row = box.row()
        row.prop(self, "altWheelMoveFunction")
        row.prop(self, "scrollUpToZoomIn")

    def drawPivotAdjustmentPrefs(self, layout: bpy.types.UILayout):
        box = layout.box()

        row = box.row()
        row.prop(self, "adjustPivot")
        row.prop(self, "pivotDig")

        row = box.row()
        row.prop(self, "pivotAdjustmentIgnoreBackfaces")

    def drawWasdPrefs(self, layout: bpy.types.UILayout):
        box = layout.box()

        row = box.row()
        row.prop(self, "wasdTopSpeed")
        row.prop(self, "useGearsWasd")

        row = box.row()
        row.prop(self, "wasdTime")
        row.prop(self, "wasdGlobalZ")

    def drawMiscPrefs(self, layout: bpy.types.UILayout):
        box = layout.box()

        row = box.row()
        row.prop(self, "showCrosshair")
        row.prop(self, "toggleMode")

        row = box.row()
        row.prop(self, "leaveFOV")
        row.prop(self, "debug")

    def drawModifierKeyPrefs(self, layout: bpy.types.UILayout):
        box = layout.box()

        row = box.row()
        row.prop(self, "increasedMagnitudeKey")

        row = box.row()
        row.prop(self, "increasedPrecisionKey")

        row = box.row()
        row.prop(self, "changedBehaviorKey")

    def drawKeyBindPrefs(self, layout: bpy.types.UILayout):
        box = layout.box()
        box.row().prop(self, "keyForward")
        box.row().prop(self, "keyBackward")
        box.row().prop(self, "keyLeft")
        box.row().prop(self, "keyRight")
        box.row().prop(self, "keyUp")
        box.row().prop(self, "keyDown")
        box.row().prop(self, "keyResetRoll")
        box.row().prop(self, "keyCycleGears")
        box.row().prop(self, "keyRelocatePivot")
        box.row().prop(self, "keyLoadCameraState")

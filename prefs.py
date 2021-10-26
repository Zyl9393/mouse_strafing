import bpy

class MouseStrafingPreferences(bpy.types.AddonPreferences):

    bl_idname = "mouse_strafing"

    sensitivityPan: bpy.props.FloatProperty(name = "Pan Sensitivity", description = "Mouse speed multiplier when panning the 3D View", \
        default = 1.0, min = 0.001, max = 100.0, soft_min = 0.01, soft_max = 10.0, step = 1, precision = 3)
    sensitivityStrafe: bpy.props.FloatProperty(name = "Strafe Sensitivity", description = "Mouse speed multiplier for mouse strafing", \
        default = 1.0, min = 0.001, soft_min = 0.01, max = 100.0, soft_max = 10.0, step = 1, precision = 3)
    strafeGears: bpy.props.FloatVectorProperty(name = "Gears", description = "Set additional strafe multipliers to cycle through with G/Shift-G. Entries set to 0 are ignored", size = 7, default = (0.08, 1.0, 3.0, 0, 0, 0, 0), min = 0.0, max = 100.0, soft_min = 0.0, soft_max = 10.0, step = 5, precision = 2)
    strafeGearSelected: bpy.props.FloatProperty(name = "Selected Gear", default = 1.0, options = {"HIDDEN"})
    
    invertMouseX: bpy.props.BoolProperty(name = "Invert Horizontal Panning", description = "Invert effect of horizontal mouse movement when looking around", default = False)
    invertMouse: bpy.props.BoolProperty(name = "Invert Vertical Panning", description = "Invert effect of vertical mouse movement when looking around", default = False)

    invertStrafeX: bpy.props.BoolProperty(name = "Invert Strafe X", description = "Invert direction of sideways mouse strafe movement", default = False)
    invertStrafeY: bpy.props.BoolProperty(name = "Invert Strafe Y", description = "Invert direction of upwards/downwards mouse strafe movement", default = False)
    invertStrafeZ: bpy.props.BoolProperty(name = "Invert Strafe Z", description = "Invert direction of forwards/backwards mouse strafe movement", default = False)

    mouseButtonActionItems = [ \
        ("turnXY", "Look around", "Look around", "NONE", 0), \
        ("strafeXZ", "Strafe left/right/forward/backwards", "Strafe left/right/forward/backwards", "NONE", 1), \
        ("strafeXY", "Strafe left/right/up/down", "Strafe left/right/up/down", "NONE", 2), \
        ("strafeXRappel", "Strafe left/right and rappel", "Strafe left/right and rappel (move up/down world Z-axis)", "NONE", 3), \
        ("turnXRappel", "Turn left/right and rappel", "Turn left/right and rappel (move up/down world Z-axis)", "NONE", 4), \
        ("roll", "Roll the camera", "Roll the camera (press R to reset roll)", "NONE", 5)]
    lmbAction: bpy.props.EnumProperty(name = "LMB", description = "Set navigation method to use while only Left Mouse Button (LMB) is held down", items = mouseButtonActionItems, default = "turnXY")
    rmbAction: bpy.props.EnumProperty(name = "RMB", description = "Set navigation method to use while only Right Mouse Button (RMB) is held down", items = mouseButtonActionItems, default = "strafeXY")
    bmbAction: bpy.props.EnumProperty(name = "BMB", description = "Set navigation method to use while Both (left and right) Mouse Buttons (BMB) are held down", items = mouseButtonActionItems, default = "strafeXZ")
    mmbAction: bpy.props.EnumProperty(name = "MMB", description = "Set navigation method to use while only Middle Mouse Button (MMB) is held down", items = mouseButtonActionItems, default = "roll")

    wasdTopSpeed: bpy.props.FloatProperty(name = "WASD Top Speed", description = "Top speed when using WASD keys to move", \
        default = 8.0, min = 0.001, max = 20000, soft_min = 0.01, soft_max = 4000, step = 10, precision = 2)
    wasdTime: bpy.props.FloatProperty(name = "WASD Acceleration Time", description = "Time until top speed is reached when using WASD keys to move", \
        default = 0.2, min = 0.0, max = 4.0, soft_min = 0.0, soft_max = 1000, step = 1, precision = 2)

    mouseWheelActionItems = [\
        ("moveZ", "Move forward/backwards", "Move forward/backwards", "NONE", 0), \
        ("changeStrafeSensitivity", "Change strafe sensitivity", "Change the mouse speed multiplier for mouse strafing", "NONE", 1)]
    wheelMoveFunction: bpy.props.EnumProperty(name = "Wheel", description = "Set what the scroll wheel does", items = mouseWheelActionItems, default = "moveZ")

    altMouseWheelActionItems = [\
        ("changeFOV", "Change Focal Length", "Change the field of view (FOV) by controlling the distance of the lens to the camera sensor", "NONE", 0), \
        ("changeHFOV", "Change Horizontal FOV", "Change the field of view (FOV) by controlling the horizontal view angle", "NONE", 1), \
        ("changeVFOV", "Change Vertical FOV", "Change the field of view (FOV) by controlling the vertical view angle", "NONE", 2)]
    altWheelMoveFunction: bpy.props.EnumProperty(name = "Wheel (Alt)", description = "Set what the scroll wheel does while holding Alt", items = altMouseWheelActionItems, default = "changeVFOV")

    wheelDistance: bpy.props.FloatProperty(name = "Wheel Distance", description = "Set move distance when using the scroll wheel to move", \
        default = 0.5, min = -1000.0, max = 1000.0, soft_min = -5.0, soft_max = 5.0, step = 1, precision = 4)
    applySensitivityWheel: bpy.props.BoolProperty(name = "Apply Sensitivity", description = "When checked, apply strafe sensitivity to scroll wheel move distance", default = True)
    scrollUpToZoomIn: bpy.props.BoolProperty(name = "Invert Direction", description = "When checked, inverts the scroll wheel direction such that scrolling up zooms in and scrolling down zooms out", default = False)

    showCrosshair: bpy.props.BoolProperty(name = "Show Crosshair", description = "Show crosshair during strafe actions", default = True)
    adjustPivot: bpy.props.BoolProperty(name = "Automatically Relocate Pivot", description = "Automatically relocate the 3D View's "
        "pivot point (instead of manually by pressing 'C') to the surface of whatever object you are looking at while using the operator", default = False)
    pivotDig: bpy.props.FloatProperty(name = "Pivot Dig", description = "When relocating the pivot point, specifies how far the pivot will be moved into the surface you are looking at, based on a percentage of its distance to the 3D View camera" , \
        default = 0.0, min = 0.0, max = 100.0, soft_min = 0.0, soft_max = 100.0, step = 100, precision = 0, subtype = "PERCENTAGE")
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
    keyRelocatePivot: bpy.props.StringProperty(name = "Relocate Pivot", description = "Press this key to relocate camera pivot to the nearest surface in the center of the view. You can also hold it for one second to toggle Automatically Relocate Pivot on and off (must be upper-case)", default = "C")
    keyLoadCameraState: bpy.props.StringProperty(name = "Load Camera State", description = "Press this key and then one of the number keys [0-9] to load the camera state in that slot without the need to quickly press the number key twice (must be upper-case)", default = "T")

    def draw(self, context: bpy.types.Context):
        prefs: MouseStrafingPreferences = context.preferences.addons[MouseStrafingPreferences.bl_idname].preferences

        layout: bpy.types.UILayout = self.layout

        box = layout.box()

        row = box.row()
        row.prop(self, "sensitivityPan")
        row.prop(self, "sensitivityStrafe")
        box.row().prop(self, "strafeGears")
        
        row = box.row()
        row.prop(self, "invertMouse")
        row.prop(self, "invertMouseX")

        row = box.row()
        row.prop(self, "invertStrafeX")
        row.prop(self, "invertStrafeY")
        row.prop(self, "invertStrafeZ")

        box = layout.box()

        row = box.row()
        row.prop(self, "lmbAction")
        row.prop(self, "rmbAction")

        row = box.row()
        row.prop(self, "bmbAction")
        row.prop(self, "mmbAction")

        row = box.row()
        row.prop(self, "wheelMoveFunction")
        if prefs.wheelMoveFunction == "moveZ":
            row = box.row()
            row.prop(self, "wheelDistance")
            row.prop(self, "applySensitivityWheel")

        row = box.row()
        row.prop(self, "altWheelMoveFunction")
        row.prop(self, "scrollUpToZoomIn")

        row = box.row()
        row.prop(self, "adjustPivot")
        row.prop(self, "pivotDig")

        row = box.row()
        row.prop(self, "showCrosshair")
        row.prop(self, "leaveFOV")

        row = box.row()
        row.prop(self, "toggleMode")
        row.prop(self, "debug")

        box = layout.box()

        row = box.row()
        row.prop(self, "wasdTopSpeed")
        row.prop(self, "wasdTime")


        layout.label(text = "Key Bindings:", translate = False)

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

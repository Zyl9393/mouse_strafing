import bpy

class MouseStrafingPreferences(bpy.types.AddonPreferences):
    bl_idname = "mouse_strafing"

    mousePreMultiplier: bpy.props.FloatProperty(name = "Mouse Pre Multiplier", description = "Multiply all mouse input with this value before applying dynamic sensitivity " + \
        "Should be set such that the fastest comfortable mouse movement barely maxes out dynamic sensitivity", \
        default = 0.006, min = 0.000001, soft_min = 0.000001, max = 1, soft_max = 1, step = 0.0001, precision = 6)
    minDynamicSensitivity: bpy.props.FloatProperty(name = "Minimum Dynamic Sensitivity %", description = "Allow mouse speed to be reduced to as little as this percentage during slow movements for greater control. " + \
        "E.g. Minimum Dynamic Sensitivity of 25% = quarter speed during slow movement. Set to 100% to disable", \
        default = 33.3, min = 0.0, soft_min = 10.0, max = 100.0, soft_max = 100, step = 100, precision = 1, subtype = "PERCENTAGE")
    displayDynamicSensitivityStats: bpy.props.BoolProperty(name = "Display Dynamic Sensitivity Stats", description = "Display dynamic sensitivity stats while using the addon. Useful for fine-tuning the settings above", default = False)
    
    wasdTopSpeed: bpy.props.FloatProperty(name = "WASD Top Speed", description = "Top speed when using WASD keys to move", \
        default = 8.0, min = 0.001, max = 20000, soft_min = 0.01, soft_max = 4000, step = 10, precision = 2)
    wasdTime: bpy.props.FloatProperty(name = "WASD Acceleration Time", description = "Time until top speed is reached when using WASD keys to move", \
        default = 0.2, min = 0.0, max = 4.0, soft_min = 0.0, soft_max = 1000, step = 1, precision = 2)

    sensitivityPan: bpy.props.FloatProperty(name = "Pan Sensitivity", description = "Additional mouse multiplier when panning the 3D View", \
        default = 1.0, min = 0.01, max = 100.0, soft_min = 0.1, soft_max = 10.0, step = 1, precision = 2)
    sensitivityStrafe: bpy.props.FloatProperty(name = "Strafe Sensitivity", description = "Additional mouse multiplier when mouse strafing", \
        default = 1.0, min = 0.01, max = 100.0, soft_min = 0.1, soft_max = 10.0, step = 1, precision = 2)

    invertMouse: bpy.props.BoolProperty(name = "Invert Mouse", description = "Invert effect of vertical mouse movement when looking around", default = True)
    showCrosshair: bpy.props.BoolProperty(name = "Show Crosshair", description = "Show crosshair during strafe actions.", default = True)
    wheelDistance: bpy.props.FloatProperty(name = "Wheel Distance", description = "Set how far to move when using the mouse wheel", \
        default = 0.5, min = -1000.0, max = 1000.0, soft_min = -5.0, soft_max = 5.0, step = 1, precision = 4)

    adjustPivot: bpy.props.BoolProperty(name = "Automatically Relocate Pivot", description = "Automatically relocate the 3D View's "
        "pivot point (instead of manually by pressing 'C') to the surface of whatever object you are looking at while using the operator", default = False)
    pivotDig: bpy.props.FloatProperty(name = "Pivot Dig", description = "When relocating the pivot point, specifies how far the pivot will be moved into the surface you are looking at, based on a percentage of its distance to the 3D View camera" , \
        default = 0.0, min = 0.0, max = 100.0, soft_min = 0.0, soft_max = 100.0, step = 100, precision = 0, subtype = "PERCENTAGE")

    actionItems = [ \
        ("turnXY", "Look around", "Look around", "NONE", 0), \
        ("strafeXZ", "Strafe left/right/forward/backwards", "Strafe left/right/forward/backwards", "NONE", 1), \
        ("strafeXY", "Strafe left/right/up/down", "Strafe left/right/up/down", "NONE", 2), \
        ("strafeXRappel", "Strafe left/right and rappel", "Strafe left/right and rappel (move up/down world Z-axis)", "NONE", 3), \
        ("turnXRappel", "Turn left/right and rappel", "Turn left/right and rappel (move up/down world Z-axis)", "NONE", 4), \
        ("roll", "Roll the camera", "Roll the camera (press R to reset roll)", "NONE", 5)]
    lmbAction: bpy.props.EnumProperty(name = "LMB", description = "Set navigation method to use while only Left Mouse Button (LMB) is held down", items = actionItems, default = "turnXY")
    rmbAction: bpy.props.EnumProperty(name = "RMB", description = "Set navigation method to use while only Right Mouse Button (RMB) is held down", items = actionItems, default = "strafeXY")
    bmbAction: bpy.props.EnumProperty(name = "BMB", description = "Set navigation method to use while Both (left and right) Mouse Buttons (BMB) are held down", items = actionItems, default = "strafeXZ")
    mmbAction: bpy.props.EnumProperty(name = "MMB", description = "Set navigation method to use while only Middle Mouse Button (MMB) is held down", items = actionItems, default = "roll")

    def draw(self, context: bpy.types.Context):
        prefs: MouseStrafingPreferences = context.preferences.addons["mouse_strafing"].preferences

        layout: bpy.types.UILayout = self.layout
        
        sensorRow = layout.row()
        sensorRow.prop(self, "mousePreMultiplier")

        dynamicSensitivityRow = layout.row()
        dynamicSensitivityRow.prop(self, "minDynamicSensitivity")

        debugRow = layout.row()
        debugRow.prop(self, "displayDynamicSensitivityStats")
        
        wasdRow = layout.row()
        wasdRow.prop(self, "wasdTopSpeed")
        wasdRow.prop(self, "wasdTime")

        sensitivityRow = layout.row()
        sensitivityRow.prop(self, "sensitivityPan")
        sensitivityRow.prop(self, "sensitivityStrafe")

        miscRow = layout.row()
        miscRow.prop(self, "invertMouse")
        miscRow.prop(self, "showCrosshair")
        miscRow.prop(self, "wheelDistance")

        pivotRow = layout.row()
        pivotRow.prop(self, "adjustPivot")
        pivotRow.prop(self, "pivotDig")

        lrRow = layout.row()
        lrRow.prop(self, "lmbAction")
        lrRow.prop(self, "rmbAction")

        mRow = layout.row()
        mRow.prop(self, "bmbAction")
        mRow.prop(self, "mmbAction")

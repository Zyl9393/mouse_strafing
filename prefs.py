import bpy

class MouseStrafingPreferences(bpy.types.AddonPreferences):
    bl_idname = "mouse_strafing"

    sensitivityPan: bpy.props.FloatProperty(name = "Pan Sensitivity", description = "Mouse multiplier when panning the 3D View", \
        default = 1.0, min = 0.01, max = 100.0, soft_min = 0.1, soft_max = 10.0, step = 1, precision = 2)
    sensitivityStrafe: bpy.props.FloatProperty(name = "Strafe Sensitivity", description = "Mouse multiplier when mouse strafing", \
        default = 1.0, min = 0.01, max = 100.0, soft_min = 0.1, soft_max = 10.0, step = 1, precision = 2)

    invertMouse: bpy.props.BoolProperty(name = "Invert Mouse", description = "Invert effect of vertical mouse movement when looking around", default = True)

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
        ("changeFOV", "Change FOV", "Change Field Of View (FOV)", "NONE", 1)]
    wheelMoveFunction: bpy.props.EnumProperty(name = "Scroll Wheel Function", description = "Set what the scroll wheel does", items = mouseWheelActionItems, default = "changeFOV")
    wheelDistance: bpy.props.FloatProperty(name = "Wheel Distance", description = "Set move distance when using the scroll wheel to move", \
        default = 0.5, min = -1000.0, max = 1000.0, soft_min = -5.0, soft_max = 5.0, step = 1, precision = 4)

    showCrosshair: bpy.props.BoolProperty(name = "Show Crosshair", description = "Show crosshair during strafe actions", default = True)
    adjustPivot: bpy.props.BoolProperty(name = "Automatically Relocate Pivot", description = "Automatically relocate the 3D View's "
        "pivot point (instead of manually by pressing 'C') to the surface of whatever object you are looking at while using the operator", default = False)
    pivotDig: bpy.props.FloatProperty(name = "Pivot Dig", description = "When relocating the pivot point, specifies how far the pivot will be moved into the surface you are looking at, based on a percentage of its distance to the 3D View camera" , \
        default = 0.0, min = 0.0, max = 100.0, soft_min = 0.0, soft_max = 100.0, step = 100, precision = 0, subtype = "PERCENTAGE")
    toggleMode: bpy.props.BoolProperty(name = "Toggle strafe-mode instead of hold-to-strafe", description = "When checked, strafe-mode will only quit when pressing the key a second time or pressing Escape", default = False)

    def draw(self, context: bpy.types.Context):
        prefs: MouseStrafingPreferences = context.preferences.addons["mouse_strafing"].preferences

        layout: bpy.types.UILayout = self.layout

        box = layout.box()

        row = box.row()
        row.prop(self, "sensitivityPan")
        row.prop(self, "sensitivityStrafe")
        
        row = box.row()
        row.prop(self, "invertMouse")

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

        row = box.row()
        row.prop(self, "adjustPivot")
        row.prop(self, "pivotDig")

        row = box.row()
        row.prop(self, "showCrosshair")

        row = box.row()
        row.prop(self, "toggleMode")

        box = layout.box()

        row = box.row()
        row.prop(self, "wasdTopSpeed")
        row.prop(self, "wasdTime")

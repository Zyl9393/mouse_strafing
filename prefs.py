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

import bpy

class MouseStrafingPreferences(bpy.types.AddonPreferences):
    bl_idname = "mouse_strafing"

    strafingDistance: bpy.props.FloatProperty(name = "Moderate Strafing Distance", description = "The distance to travel during an average mouse cursor movement of 1000 pixels over 20 frames. Drives the multiplier of the speed curve", \
        default = 40, min = 0.1, max = 5000, soft_min = 1, soft_max = 1000, step = 10, precision = 2)
    strafingPotential: bpy.props.FloatProperty(name = "Strafing Potential", description = "Increase this value to have to move the mouse less for large speeds, but more for slow speeds. Higher values are more difficult to control", \
        default = 1.2, min = 1.0, max = 2.0, soft_min = 1.0, soft_max = 1.6, step = 1, precision = 2)
    
    wasdTopSpeed: bpy.props.FloatProperty(name = "WASD Top Speed", description = "Top speed when using WASD keys to move", \
        default = 8.0, min = 0.001, max = 20000, soft_min = 0.01, soft_max = 4000, step = 10, precision = 2)
    wasdTime: bpy.props.FloatProperty(name = "WASD Acceleration Time", description = "Time until top speed is reached when using WASD keys to move", \
        default = 0.2, min = 0.0, max = 4.0, soft_min = 0.0, soft_max = 1000, step = 1, precision = 2)

    sensitivityDefault: bpy.props.FloatProperty(name = "Sensitivity", description = "Default mouse sensitivity when panning the 3D View", \
        default = 0.25, min = 0.01, max = 2.0, soft_min = 0.01, soft_max = 2.0, step = 1, precision = 2)
    sensitivityWasd: bpy.props.FloatProperty(name = "WASD Sensitivity", description = "Mouse sensitivity when panning in the 3D View while using WASD keys to move. Lower values feel better when using a high WASD Top Speed", \
        default = 0.15, min = 0.01, max = 2.0, soft_min = 0.01, soft_max = 2.0, step = 1, precision = 2)
    sensitivityRappel: bpy.props.FloatProperty(name = "Rappel Sensitivity", description = "Mouse sensitivity when panning in the 3D View while using the rappel function, during which panning the desired amount is usually more difficult", \
        default = 0.15, min = 0.0, max = 2.0, soft_min = 0.01, soft_max = 2.0, step = 1, precision = 2)

    invertMouse: bpy.props.BoolProperty(name = "Invert Mouse", description = "Invert effect of vertical mouse movement when looking around", default = True)
    showCrosshair: bpy.props.BoolProperty(name = "Show Crosshair", description = "Show crosshair during strafe actions.", default = True)
    wheelDistance: bpy.props.FloatProperty(name = "Wheel Distance", description = "Set how far to move when using the mouse wheel", \
        default = 0.5, min = -128.0, max = 128.0, soft_min = -5.0, soft_max = 5.0, step = 1, precision = 4)

    adjustPivot: bpy.props.BoolProperty(name = "Automatically Relocate Pivot", description = "Automatically relocate the 3D View's "
        "pivot point (instead of manually by pressing 'C') to the surface of whatever object you are looking at while using the operator", default = False)
    pivotDig: bpy.props.FloatProperty(name = "Pivot Dig", description = "When relocating the pivot point, specifies how far the pivot will be moved into the surface you are looking at, based on a percentage of its distance to you (the origin of the 3D View)" , \
        default = 5.0, min = 0.0, max = 100.0, soft_min = 0.0, soft_max = 100.0, step = 100, precision = 0, subtype = "PERCENTAGE")

    actionItems = [ \
        ("turnXY", "Look around", "Look around", "NONE", 0), \
        ("strafeXZ", "Strafe left/right/forward/backwards", "Strafe left/right/forward/backwards", "NONE", 1), \
        ("strafeXY", "Strafe left/right/up/down", "Strafe left/right/up/down", "NONE", 2), \
        ("strafeXRappel", "Strafe left/right and rappel", "Strafe left/right and rappel (move up/down world Z-axis)", "NONE", 3), \
        ("turnXRappel", "Turn left/right and rappel", "Turn left/right and rappel (move up/down world Z-axis)", "NONE", 4)]
    lmbAction: bpy.props.EnumProperty(name = "LMB", description = "Set navigation method to use while only Left Mouse Button (LMB) is held down", items = actionItems, default = "turnXY")
    rmbAction: bpy.props.EnumProperty(name = "RMB", description = "Set navigation method to use while only Right Mouse Button (RMB) is held down", items = actionItems, default = "strafeXY")
    bmbAction: bpy.props.EnumProperty(name = "BMB", description = "Set navigation method to use while Both (left and right) Mouse Buttons (BMB) are held down", items = actionItems, default = "strafeXZ")
    mmbAction: bpy.props.EnumProperty(name = "MMB", description = "Set navigation method to use while only Middle Mouse Button (MMB) is held down", items = actionItems, default = "strafeXRappel")

    def draw(self, context: bpy.types.Context):
        prefs: MouseStrafingPreferences = context.preferences.addons["mouse_strafing"].preferences

        layout: bpy.types.UILayout = self.layout
        
        sensorRow = layout.row()
        sensorRow.prop(self, "strafingDistance")
        sensorRow.prop(self, "strafingPotential")
        
        wasdRow = layout.row()
        wasdRow.prop(self, "wasdTopSpeed")
        wasdRow.prop(self, "wasdTime")

        sensitivityRow = layout.row()
        sensitivityRow.prop(self, "sensitivityDefault")
        sensitivityRow.prop(self, "sensitivityWasd")
        sensitivityRow.prop(self, "sensitivityRappel")

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

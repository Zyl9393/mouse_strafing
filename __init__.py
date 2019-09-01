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

bl_info = {
    "name": "Mouse Strafing",
    "description": "Strafe in the 3D View using the mouse.",
    "author": "Zyl",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "category": "3D View"
}

import bpy
from . import mouse_strafing
from . import prefs

def unregister():
    mouse_strafing.unregister_keymaps()
    bpy.utils.unregister_class(prefs.MouseStrafingPreferences)
    bpy.utils.unregister_class(mouse_strafing.MouseStrafingOperator)

def register():
    bpy.utils.register_class(mouse_strafing.MouseStrafingOperator)
    bpy.utils.register_class(prefs.MouseStrafingPreferences)
    mouse_strafing.register_keymaps()

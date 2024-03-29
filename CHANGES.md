# 2.6 (2023-01-18)
* Fix time-dependent effects (text fade-out, WASD acceleration) becoming jerky on Windows when the system has been running for more than two days.
* Can now specify additional speed multiplier that is used for all movement operations when the scene's unit system is set to 'None'.

# 2.5 (2022-07-17)
* Fix regression issue preventing camera panning when camera locked to view.
* Can now specify which modifier key performs which action.
	* This introduces a new default behavior where now `Alt` increases precision (i.e. causes speed decrease) while `Ctrl` engages alternative behavior (i.e. FOV-change using mouse wheel) in accordance with how it works everywhere else in Blender.
* Can now specify modifier key effect strength (speed increase/decrease).
* Pan sensitivity is now decreased automatically depending on focal length when it is greater than 50mm.
* Removed some confusing modifier key combinations.
* Added undo support.

# 2.4 (2022-03-06)
* Fixed movement option "Strafe left/right and rappel".
* Improve support for using a mouse button as addon shortcut.
	* Interpret bindings even when too many buttons are pressed.
		* Bindings with two buttons are chosen over bindings with a single button.
		* Thereafter, bindings further up the list are chosen over bindings further down the list.
		* Added up/down buttons to change order of bindings.
* Automatic pivot relocation now defaults to being enabled.
* Minimum supported Blender version increased from 2.92 to 2.93.

# 2.3 (2021-12-18)
* Added option to invert X/Y/Z mouse strafing directions.
* Added option to align WASD up/down movement direction with global Z-axis instead of the view's Z-axis.
* Added option to apply gear multiplier to WASD move speed.
* Added option to apply gear multiplier to scroll wheel move distance.
* Added option to configure when pivot adjustment ignores backfaces.
* Added support for operator key binding to coincide with mouse buttons.
* Added support for binding any combination of two mouse buttons.
* Changed toggling of automatic pivot relocation to be triggered with `Shift + C` instead of by holding `C` for a second. (Usability)
* Loading camera state now highlights the crosshair while the key is held.
* Rolling the camera now respects holding `Ctrl` and `Alt` for reduced sensitivity.
* Fixed angle display. (Blender uses 72mm sensor width for the 3D View instead of the standard 36mm used in Cameras for unknown reasons.)
* Fixed behavior for cameras with Axis-Angle and non-XYZ Euler rotation modes.
* Operator will now clean up its draw handler on error.

# 2.2 (2021-09-26)
* Camera save states now also save and load 3D View projection mode (perspective/orthographic).
* Fixed a typo which broke panning when the invert mouse option was disabled.
* Changing view angle with the mouse wheel now displays change on screen for a moment.
	* Allow to set which aspect of view angle to control, i.e. horizontal view angle, vertical view angle or focal length in the addon preferences.
	* Works for cameras, too.
* Changing view angle with mouse wheel is now on Alt + mouse wheel to be in line with Alt reducing pan sensitivity being an interest in high zoom situations.
	* Using Alt to lower pan speed will now lower the pan angle further depending on zoom level.
	* Just mouse wheel can now change mouse strafe speed if set instead of moving the camera in addon preferences.
* Can now configure up to 7 mouse strafe speed multipliers which can be cycled through by pressing G or Shift+G.
* Holding the Relocate Pivot key to disable automatic pivot relocation will no longer cause a pivot relocation.
* Fixed toggling automic pivot relocation by holding the Relocate Pivot key not being saved in the addon preferences when closing Blender.
* Added option to load camera state after pressing a key instead of having to quickly tap a number key twice.
* Added option to prevent the loading of camera states from changing the FOV.
* Added option to invert mouse horizontal movement.
* Addon now correctly registers under `view3d` category of addons (instead of `view_3d`).

# 2.1 (2021-06-12)
* Changed compatible Blender version to 2.92.0.
* Updated ray casting to work with Blender 2.91 and later.
* Removed some confusing, needlessly complicated settings.
* Fixed occasional sudden jerky mouse movement. (Caused by Blender's `cursor_warp` glitch)
* Fixed stuttery movement caused by missing `INBETWEEN_MOUSEMOVE` events.
* Fixed unrelated key-presses passing through.
* Added option to customize keys.
* Added save states. (See README)
* Crosshair now draws in yellow when trying to manually relocate pivot while automatic pivot relocation is enabled.
* Holding relocate pivot key for one second now toggles automatic pivot relocation.

# 2.0 (2020-12-22)
* Pressing C to adjust pivot distance now ignores backfaces when backface culling is enabled in viewport settings.
* Added camera roll mouse action. Can press R to reset roll.
* Mouse strafing now remains active while at least one mouse button is still pressed, regardless of whether strafing key was released.
* Addon now cooperates with "Lock camera to view" and "Local camera" settings.
* Improved ergonomics of mouse acceleration.
* `package.bat` now creates Linux-compatible archives.
* Ctrl and Alt now affect strafe speed and pan sensitivity, respectively. Hold both to greatly reduce strafe speed.
* Quad views are now somewhat supported. Blender seems to have a slew of its own bugs with them.
* The scroll wheel can now be configured to change the field of view.
* Can now set strafe-mode to be toggleable instead of hold-to-strafe.

# 1.0 (2019-10-01)
* Initial release

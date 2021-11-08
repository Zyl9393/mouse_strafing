# 2.3 (TBD)
* Added option to invert X/Y/Z mouse strafing directions.
* Added option to align WASD up/down movement direction with global Z-axis instead of the view's Z-axis.
* Added option to apply gear multiplier to WASD move speed.
* Added option to apply gear multiplier to scroll wheel move distance.
* Rolling the camera now respects holding `Ctrl` and `Alt` for reduced sensitivity.
* Fixed angle display. (Blender uses 72mm sensor width for the 3D View instead of the standard 36mm used in Cameras for unknown reasons.)

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

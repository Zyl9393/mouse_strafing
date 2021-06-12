# 2.1 (2021-06-03)
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

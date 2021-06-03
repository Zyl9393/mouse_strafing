# 2.1 (2021-06-03)
* Change compatible Blender version to 2.92.0.
* Update ray casting to work with Blender 2.91 and later.
* Fix occasional sudden jerky mouse movement.
* Removed confusing settings: highly configurable mouse acceleration was faulty because Blender batches mouse movement events anyway.

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

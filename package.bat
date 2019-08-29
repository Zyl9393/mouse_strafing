mkdir mouse_strafing
copy *.py mouse_strafing
powershell Compress-Archive -Path mouse_strafing -DestinationPath mouse_strafing.zip -Force
rmdir /S /Q mouse_strafing

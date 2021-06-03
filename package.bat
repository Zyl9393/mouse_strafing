@mkdir mouse_strafing
@copy *.py mouse_strafing
@where justzip
@if %ERRORLEVEL% NEQ 0 go install github.com/Zyl9393/justzip@v1
@justzip -i mouse_strafing -o mouse_strafing.zip
@rmdir /S /Q mouse_strafing

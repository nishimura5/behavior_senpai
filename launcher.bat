@echo off

where rye.exe > nul 2>&1
if %errorlevel% == 0 (
    echo rye.exe found
    rye run launcher
) else (
    echo rye.exe not found
    python ./src/launcher.py
)

pause

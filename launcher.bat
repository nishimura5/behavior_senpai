@echo off

where rye.exe > nul 2>&1
if %errorlevel% == 0 (
    rye run launcher
) else (
    echo rye.exe was not found in PATH
    python .\src\launcher.py
)

pause

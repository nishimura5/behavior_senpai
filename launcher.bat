@echo off

where rye.exe > nul 2>&1
if %errorlevel% NEQ 0 (
    echo rye.exe was not found in PATH
    pause
    exit
)
if not exist ".\.venv\" (
    echo .venv folder was not found
    pause
    exit
)

rye run launcher

pause

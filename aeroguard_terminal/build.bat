@echo off
echo ================================================================
echo   AeroGuard ZTNA Terminal — Build Script
echo ================================================================
echo.

echo [1/3] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ and add to PATH.
    pause & exit /b 1
)

echo [2/3] Installing PyInstaller...
pip install pyinstaller --quiet

echo [3/3] Building AeroGuard_Terminal.exe ...
pyinstaller aeroguard_terminal.spec --noconfirm --clean

echo.
echo ================================================================
echo   BUILD COMPLETE
echo   Output: dist\AeroGuard_Terminal.exe
echo ================================================================
echo.
echo DEPLOYMENT STEPS:
echo   1. Copy dist\AeroGuard_Terminal.exe to operator workstation
echo   2. Copy airport_system.db to the SAME folder as the .exe
echo   3. Add .exe to Windows Startup so it auto-runs on boot
echo   4. In your gateway main.py, call:
echo        from gateway_notifier import notify_terminal
echo        notify_terminal(client_ip=operator_ip, username=username)
echo   5. After knock verified, terminal pops up automatically
echo.
echo TEST WITHOUT GATEWAY:
echo   dist\AeroGuard_Terminal.exe --direct
echo.
pause

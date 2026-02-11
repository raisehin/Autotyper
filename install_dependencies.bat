@echo off
setlocal
echo ==========================================
echo AutoTyper Lite Dependency Installer
echo ==========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [INFO] Python detected.
echo [INFO] Installing requirements...
echo.

:: Install requirements
python -m pip install --upgrade pip
python -m pip install -r source\requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed. Please check your internet connection or permissions.
) else (
    echo.
    echo [SUCCESS] All dependencies installed successfully!
    echo You can now run the application using 'run_app.bat' or the EXE.
)

echo.
pause
exit /b 0

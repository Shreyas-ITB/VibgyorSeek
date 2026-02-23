@echo off
REM Build script for VibgyorSeek Employee Monitoring Client
REM This script builds the executable using PyInstaller

echo ========================================
echo VibgyorSeek Monitoring Client Builder
echo ========================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Error: Virtual environment not activated
    echo Please run: venv\Scripts\activate
    echo.
    pause
    exit /b 1
)

echo Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

echo Building executable with PyInstaller...
echo This may take a few minutes...
echo.

pyinstaller --clean monitoring_client.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Build failed!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\VibgyorSeekMonitoring.exe
echo.
echo Next steps:
echo 1. Copy the executable to the target machine
echo 2. Copy .env.example to .env and configure it
echo 3. Run: VibgyorSeekMonitoring.exe --setup
echo 4. Run: VibgyorSeekMonitoring.exe --install
echo 5. Run: VibgyorSeekMonitoring.exe --start
echo.
pause

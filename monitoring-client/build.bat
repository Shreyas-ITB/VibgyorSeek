@echo off
REM Build script for VibgyorSeek Employee Monitoring Client
REM This script builds the executable using PyInstaller

echo ========================================
echo VibgyorSeek Monitoring Client Builder
echo ========================================
echo.
echo Building WINDOWLESS (background) version
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
echo Mode: Windowless (console=False)
echo This may take a few minutes...
echo.

python -m PyInstaller --clean monitoring_client.spec

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
echo Executable: dist\VibgyorSeekMonitoring.exe
echo Mode: Windowless (runs in background)
echo.
echo Testing executable...
cd dist
start /B VibgyorSeekMonitoring.exe --show-id
timeout /t 3 >nul
tasklist | findstr VibgyorSeekMonitoring
if %ERRORLEVEL% EQU 0 (
    echo [OK] Executable is running in background
    echo Stopping test process...
    taskkill /IM VibgyorSeekMonitoring.exe /F >nul 2>&1
) else (
    echo [WARNING] Could not verify process
)
cd ..
echo.
echo Next steps:
echo 1. Copy dist\VibgyorSeekMonitoring.exe to deployment folder
echo 2. Copy .env file (configured) to same folder
echo 3. Build installer: iscc VibgyorSeekMonitoring_TaskScheduler.iss
echo 4. Deploy VibgyorSeekSetup.exe to users
echo.
echo Or test manually:
echo   cd dist
echo   copy ..\\.env .
echo   VibgyorSeekMonitoring.exe
echo   (Check Task Manager to see it running)
echo   (Check logs\logs YYYY-MM-DD.txt for output)
echo.
pause

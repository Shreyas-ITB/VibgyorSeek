@echo off
echo ========================================
echo REBUILDING WINDOWLESS EXECUTABLE
echo ========================================
echo.
echo This will rebuild VibgyorSeekMonitoring.exe
echo with console=False (no window mode)
echo.
pause

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create it first: python -m venv venv
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building windowless executable...
echo (This will take 2-3 minutes)
echo.

python -m PyInstaller --clean monitoring_client.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo.
echo The new windowless executable is at:
echo   dist\VibgyorSeekMonitoring.exe
echo.
echo IMPORTANT: This is a NEW file!
echo You must use THIS file, not the old one.
echo.
echo Next steps:
echo 1. Copy dist\VibgyorSeekMonitoring.exe to your deployment folder
echo 2. Copy .env file to same folder
echo 3. Rebuild the installer: iscc VibgyorSeekMonitoring_TaskScheduler.iss
echo 4. Run the NEW installer
echo.
pause

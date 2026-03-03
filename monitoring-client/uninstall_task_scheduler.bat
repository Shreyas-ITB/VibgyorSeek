@echo off
REM VibgyorSeek Monitoring Client - Task Scheduler Uninstallation

echo ==========================================
echo VibgyorSeek Monitoring Client Uninstaller
echo ==========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires administrator privileges.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Stopping monitoring client...
schtasks /end /tn "VibgyorSeek Monitoring" >nul 2>&1

echo Removing scheduled task...
schtasks /delete /tn "VibgyorSeek Monitoring" /f

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: Task removed successfully!
    echo ========================================
) else (
    echo.
    echo ERROR: Failed to remove scheduled task
    echo Error code: %errorLevel%
)

echo.
pause

@echo off
REM VibgyorSeek Monitoring Client - NSSM Service Uninstallation Script

echo ========================================
echo VibgyorSeek Monitoring Service Uninstaller
echo ========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

set "SERVICE_NAME=VibgyorSeekMonitoring"

REM Check if NSSM is available
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: NSSM not found in PATH!
    echo.
    echo Please download NSSM from https://nssm.cc/download
    pause
    exit /b 1
)

REM Check if service exists
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo Service "%SERVICE_NAME%" is not installed.
    pause
    exit /b 0
)

echo Stopping service...
nssm stop "%SERVICE_NAME%"
timeout /t 3 /nobreak >nul

echo Removing service...
nssm remove "%SERVICE_NAME%" confirm

if %errorLevel% equ 0 (
    echo Service removed successfully!
) else (
    echo ERROR: Failed to remove service!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Uninstallation Complete!
echo ========================================
pause

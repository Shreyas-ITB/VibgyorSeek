@echo off
REM VibgyorSeek Monitoring Client - NSSM Service Installation Script
REM This script installs the monitoring client as a Windows service using NSSM

echo ========================================
echo VibgyorSeek Monitoring Service Installer
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

REM Set paths
set "SCRIPT_DIR=%~dp0"
set "EXE_PATH=%SCRIPT_DIR%dist\VibgyorSeekMonitoring.exe"
set "SERVICE_NAME=VibgyorSeekMonitoring"
set "DISPLAY_NAME=VibgyorSeek Employee Monitoring"
set "DESCRIPTION=Monitors employee activity and transmits data to the central server"

REM Check if NSSM is available
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: NSSM not found in PATH!
    echo.
    echo Please download NSSM from https://nssm.cc/download
    echo Extract it and either:
    echo   1. Add nssm.exe to your PATH, or
    echo   2. Place nssm.exe in the same folder as this script
    pause
    exit /b 1
)

REM Check if executable exists
if not exist "%EXE_PATH%" (
    echo ERROR: VibgyorSeekMonitoring.exe not found!
    echo Expected location: %EXE_PATH%
    echo.
    echo Please build the executable first using: pyinstaller monitoring_client.spec
    pause
    exit /b 1
)

REM Check if service already exists
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo Service already exists. Removing old service...
    nssm stop "%SERVICE_NAME%"
    timeout /t 2 /nobreak >nul
    nssm remove "%SERVICE_NAME%" confirm
    timeout /t 2 /nobreak >nul
)

echo Installing service...
nssm install "%SERVICE_NAME%" "%EXE_PATH%"

if %errorLevel% neq 0 (
    echo ERROR: Failed to install service!
    pause
    exit /b 1
)

echo Configuring service...
nssm set "%SERVICE_NAME%" DisplayName "%DISPLAY_NAME%"
nssm set "%SERVICE_NAME%" Description "%DESCRIPTION%"
nssm set "%SERVICE_NAME%" Start SERVICE_AUTO_START
nssm set "%SERVICE_NAME%" AppDirectory "%SCRIPT_DIR%"
nssm set "%SERVICE_NAME%" AppStdout "%SCRIPT_DIR%logs\service_stdout.log"
nssm set "%SERVICE_NAME%" AppStderr "%SCRIPT_DIR%logs\service_stderr.log"
nssm set "%SERVICE_NAME%" AppRotateFiles 1
nssm set "%SERVICE_NAME%" AppRotateOnline 1
nssm set "%SERVICE_NAME%" AppRotateBytes 10485760

echo.
echo Service installed successfully!
echo.
echo Starting service...
nssm start "%SERVICE_NAME%"

if %errorLevel% equ 0 (
    echo Service started successfully!
) else (
    echo WARNING: Service installed but failed to start.
    echo You can start it manually using: nssm start %SERVICE_NAME%
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Service Name: %SERVICE_NAME%
echo Display Name: %DISPLAY_NAME%
echo.
echo Useful commands:
echo   Start:   nssm start %SERVICE_NAME%
echo   Stop:    nssm stop %SERVICE_NAME%
echo   Restart: nssm restart %SERVICE_NAME%
echo   Status:  nssm status %SERVICE_NAME%
echo   Remove:  nssm remove %SERVICE_NAME% confirm
echo.
pause

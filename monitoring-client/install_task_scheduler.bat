@echo off
REM VibgyorSeek Monitoring Client - Task Scheduler Installation
REM This script installs the monitoring client as a scheduled task that runs at user login

echo ========================================
echo VibgyorSeek Monitoring Client Installer
echo ========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires administrator privileges.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "EXE_PATH=%SCRIPT_DIR%VibgyorSeekMonitoring.exe"
set "XML_PATH=%TEMP%\VibgyorSeekTask.xml"

REM Check if executable exists
if not exist "%EXE_PATH%" (
    echo ERROR: VibgyorSeekMonitoring.exe not found in current directory
    echo Expected location: %EXE_PATH%
    pause
    exit /b 1
)

echo Found executable: %EXE_PATH%
echo Working directory: %SCRIPT_DIR%
echo.

REM Stop and remove existing task if it exists
echo Removing existing task (if any)...
schtasks /end /tn "VibgyorSeek Monitoring" >nul 2>&1
schtasks /delete /tn "VibgyorSeek Monitoring" /f >nul 2>&1
echo.

REM Create XML file for task with working directory
echo Creating task XML configuration...
(
echo ^<?xml version="1.0" encoding="UTF-16"?^>
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
echo   ^<RegistrationInfo^>
echo     ^<Description^>VibgyorSeek Employee Monitoring Client^</Description^>
echo     ^<Author^>VibgyorSeek^</Author^>
echo   ^</RegistrationInfo^>
echo   ^<Triggers^>
echo     ^<LogonTrigger^>
echo       ^<Enabled^>true^</Enabled^>
echo     ^</LogonTrigger^>
echo   ^</Triggers^>
echo   ^<Principals^>
echo     ^<Principal id="Author"^>
echo       ^<LogonType^>InteractiveToken^</LogonType^>
echo       ^<RunLevel^>HighestAvailable^</RunLevel^>
echo     ^</Principal^>
echo   ^</Principals^>
echo   ^<Settings^>
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^>
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^>
echo     ^<AllowHardTerminate^>true^</AllowHardTerminate^>
echo     ^<StartWhenAvailable^>true^</StartWhenAvailable^>
echo     ^<RunOnlyIfNetworkAvailable^>false^</RunOnlyIfNetworkAvailable^>
echo     ^<IdleSettings^>
echo       ^<StopOnIdleEnd^>false^</StopOnIdleEnd^>
echo       ^<RestartOnIdle^>false^</RestartOnIdle^>
echo     ^</IdleSettings^>
echo     ^<AllowStartOnDemand^>true^</AllowStartOnDemand^>
echo     ^<Enabled^>true^</Enabled^>
echo     ^<Hidden^>false^</Hidden^>
echo     ^<RunOnlyIfIdle^>false^</RunOnlyIfIdle^>
echo     ^<WakeToRun^>false^</WakeToRun^>
echo     ^<ExecutionTimeLimit^>PT0S^</ExecutionTimeLimit^>
echo     ^<Priority^>7^</Priority^>
echo   ^</Settings^>
echo   ^<Actions Context="Author"^>
echo     ^<Exec^>
echo       ^<Command^>%EXE_PATH%^</Command^>
echo       ^<WorkingDirectory^>%SCRIPT_DIR%^</WorkingDirectory^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%XML_PATH%"

REM Create scheduled task from XML
echo Creating scheduled task...
schtasks /create /tn "VibgyorSeek Monitoring" /xml "%XML_PATH%" /f

REM Clean up XML file
del "%XML_PATH%" >nul 2>&1

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: Task created successfully!
    echo ========================================
    echo.
    echo The monitoring client will start automatically when you log in.
    echo Working directory is set to: %SCRIPT_DIR%
    echo.
    echo To start it now without logging out:
    echo   schtasks /run /tn "VibgyorSeek Monitoring"
    echo.
    echo To check status:
    echo   schtasks /query /tn "VibgyorSeek Monitoring"
    echo.
    echo To stop it:
    echo   schtasks /end /tn "VibgyorSeek Monitoring"
    echo.
    
    REM Ask if user wants to start it now
    set /p START_NOW="Start monitoring client now? (Y/N): "
    if /i "%START_NOW%"=="Y" (
        echo.
        echo Starting monitoring client...
        schtasks /run /tn "VibgyorSeek Monitoring"
        timeout /t 2 >nul
        echo.
        echo Client started! Check Task Manager to verify it's running.
        echo Check logs in: %SCRIPT_DIR%logs\
    )
) else (
    echo.
    echo ERROR: Failed to create scheduled task
    echo Error code: %errorLevel%
)

echo.
pause

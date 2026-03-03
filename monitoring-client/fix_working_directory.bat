@echo off
REM Fix Working Directory for Existing Task
REM This script recreates the scheduled task with the correct working directory

echo ========================================
echo Fix VibgyorSeek Monitoring Working Dir
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

REM Set paths
set "INSTALL_DIR=C:\Program Files\VibgyorSeekMonitoring"
set "EXE_PATH=%INSTALL_DIR%\VibgyorSeekMonitoring.exe"
set "XML_PATH=%TEMP%\VibgyorSeekTask.xml"

REM Check if executable exists
if not exist "%EXE_PATH%" (
    echo ERROR: VibgyorSeekMonitoring.exe not found
    echo Expected location: %EXE_PATH%
    echo.
    echo Please enter the correct installation path:
    set /p INSTALL_DIR="Path: "
    set "EXE_PATH=%INSTALL_DIR%\VibgyorSeekMonitoring.exe"
    
    if not exist "%EXE_PATH%" (
        echo ERROR: Still not found. Exiting.
        pause
        exit /b 1
    )
)

echo Found executable: %EXE_PATH%
echo Working directory will be set to: %INSTALL_DIR%
echo.

REM Stop and remove existing task
echo Stopping and removing existing task...
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
echo       ^<WorkingDirectory^>%INSTALL_DIR%^</WorkingDirectory^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%XML_PATH%"

REM Create scheduled task from XML
echo Creating scheduled task with working directory...
schtasks /create /tn "VibgyorSeek Monitoring" /xml "%XML_PATH%" /f

REM Clean up XML file
del "%XML_PATH%" >nul 2>&1

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: Task fixed successfully!
    echo ========================================
    echo.
    echo The task now has the correct working directory set.
    echo.
    echo Verifying task configuration...
    schtasks /query /tn "VibgyorSeek Monitoring" /v /fo list | findstr /C:"Task To Run" /C:"Start In"
    echo.
    
    set /p START_NOW="Start monitoring client now? (Y/N): "
    if /i "%START_NOW%"=="Y" (
        echo.
        echo Starting monitoring client...
        schtasks /run /tn "VibgyorSeek Monitoring"
        timeout /t 3 >nul
        echo.
        echo Checking if process is running...
        tasklist | findstr /i "VibgyorSeekMonitoring.exe"
        if %errorLevel% equ 0 (
            echo.
            echo [OK] Client is running!
            echo Check logs at: %INSTALL_DIR%\logs\
        ) else (
            echo.
            echo [WARNING] Process not found. Check logs for errors.
        )
    )
) else (
    echo.
    echo ERROR: Failed to create scheduled task
    echo Error code: %errorLevel%
)

echo.
pause

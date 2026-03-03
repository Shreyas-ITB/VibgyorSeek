@echo off
echo ========================================
echo VibgyorSeek Monitoring - Status Check
echo ========================================
echo.

REM Check if task exists
echo Checking for scheduled task...
schtasks /query /tn "VibgyorSeek Monitoring" >nul 2>&1

if %errorLevel% equ 0 (
    echo [OK] Task exists!
    echo.
    echo Task Details:
    echo ----------------------------------------
    schtasks /query /tn "VibgyorSeek Monitoring" /fo list
    echo ----------------------------------------
    echo.
    
    REM Check if process is running
    echo Checking if process is running...
    tasklist | findstr /i "VibgyorSeekMonitoring.exe" >nul 2>&1
    
    if %errorLevel% equ 0 (
        echo [OK] Process is RUNNING!
        echo.
        tasklist | findstr /i "VibgyorSeekMonitoring.exe"
    ) else (
        echo [WARNING] Process is NOT running!
        echo.
        set /p START_NOW="Start the monitoring client now? (Y/N): "
        if /i "!START_NOW!"=="Y" (
            echo.
            echo Starting monitoring client...
            schtasks /run /tn "VibgyorSeek Monitoring"
            timeout /t 2 >nul
            echo.
            echo Checking if it started...
            tasklist | findstr /i "VibgyorSeekMonitoring.exe"
            if %errorLevel% equ 0 (
                echo [OK] Client started successfully!
            ) else (
                echo [ERROR] Client failed to start. Check logs for errors.
            )
        )
    )
) else (
    echo [ERROR] Task does NOT exist!
    echo.
    echo The scheduled task was not created during installation.
    echo.
    echo Would you like to create it now?
    set /p CREATE_NOW="Create task now? (Y/N): "
    if /i "!CREATE_NOW!"=="Y" (
        echo.
        echo Please enter the full path to VibgyorSeekMonitoring.exe
        echo Example: C:\Program Files\VibgyorSeekMonitoring\VibgyorSeekMonitoring.exe
        echo.
        set /p EXE_PATH="Path: "
        
        if exist "!EXE_PATH!" (
            echo.
            echo Creating scheduled task...
            schtasks /create /tn "VibgyorSeek Monitoring" /tr "\"!EXE_PATH!\"" /sc onlogon /rl highest /f
            
            if %errorLevel% equ 0 (
                echo [OK] Task created successfully!
                echo.
                set /p START_NOW="Start it now? (Y/N): "
                if /i "!START_NOW!"=="Y" (
                    schtasks /run /tn "VibgyorSeek Monitoring"
                    echo [OK] Client started!
                )
            ) else (
                echo [ERROR] Failed to create task. Run this script as Administrator.
            )
        ) else (
            echo [ERROR] File not found: !EXE_PATH!
        )
    )
)

echo.
echo ========================================
echo.
echo Useful commands:
echo   Start:  schtasks /run /tn "VibgyorSeek Monitoring"
echo   Stop:   schtasks /end /tn "VibgyorSeek Monitoring"
echo   Status: schtasks /query /tn "VibgyorSeek Monitoring"
echo   GUI:    taskschd.msc
echo.
pause

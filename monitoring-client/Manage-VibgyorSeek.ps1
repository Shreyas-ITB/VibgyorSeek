# VibgyorSeek Monitoring Client - Management Script
# Run this script as Administrator

param(
    [Parameter(Position=0)]
    [ValidateSet('status', 'start', 'stop', 'restart', 'install', 'uninstall', 'logs')]
    [string]$Action = 'status'
)

$TaskName = "VibgyorSeek Monitoring"
$InstallPath = "C:\Program Files\VibgyorSeekMonitoring"
$ExePath = Join-Path $InstallPath "VibgyorSeekMonitoring.exe"

function Show-Header {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "VibgyorSeek Monitoring Client Manager" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-TaskExists {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    return $null -ne $task
}

function Test-ProcessRunning {
    $process = Get-Process -Name "VibgyorSeekMonitoring" -ErrorAction SilentlyContinue
    return $null -ne $process
}

function Show-Status {
    Show-Header
    
    Write-Host "Checking scheduled task..." -ForegroundColor Yellow
    if (Test-TaskExists) {
        Write-Host "[OK] Task exists" -ForegroundColor Green
        
        $task = Get-ScheduledTask -TaskName $TaskName
        Write-Host "  State: $($task.State)" -ForegroundColor Gray
        Write-Host "  Last Run: $($task.LastRunTime)" -ForegroundColor Gray
        Write-Host "  Next Run: $($task.NextRunTime)" -ForegroundColor Gray
    } else {
        Write-Host "[ERROR] Task does NOT exist" -ForegroundColor Red
        Write-Host "  Run: .\Manage-VibgyorSeek.ps1 install" -ForegroundColor Yellow
        return
    }
    
    Write-Host ""
    Write-Host "Checking process..." -ForegroundColor Yellow
    if (Test-ProcessRunning) {
        $process = Get-Process -Name "VibgyorSeekMonitoring"
        Write-Host "[OK] Process is RUNNING" -ForegroundColor Green
        Write-Host "  PID: $($process.Id)" -ForegroundColor Gray
        Write-Host "  Memory: $([math]::Round($process.WorkingSet64/1MB, 2)) MB" -ForegroundColor Gray
        Write-Host "  Start Time: $($process.StartTime)" -ForegroundColor Gray
    } else {
        Write-Host "[WARNING] Process is NOT running" -ForegroundColor Yellow
        Write-Host "  Run: .\Manage-VibgyorSeek.ps1 start" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Checking logs..." -ForegroundColor Yellow
    $logsPath = Join-Path $InstallPath "logs"
    if (Test-Path $logsPath) {
        $todayLog = Join-Path $logsPath "logs $(Get-Date -Format 'yyyy-MM-dd').txt"
        if (Test-Path $todayLog) {
            $logSize = (Get-Item $todayLog).Length
            Write-Host "[OK] Today's log file exists" -ForegroundColor Green
            Write-Host "  Path: $todayLog" -ForegroundColor Gray
            Write-Host "  Size: $([math]::Round($logSize/1KB, 2)) KB" -ForegroundColor Gray
        } else {
            Write-Host "[WARNING] Today's log file not found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARNING] Logs folder not found" -ForegroundColor Yellow
    }
}

function Start-Client {
    Show-Header
    
    if (-not (Test-TaskExists)) {
        Write-Host "[ERROR] Task does not exist. Run 'install' first." -ForegroundColor Red
        return
    }
    
    if (Test-ProcessRunning) {
        Write-Host "[INFO] Client is already running" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Starting monitoring client..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2
    
    if (Test-ProcessRunning) {
        Write-Host "[OK] Client started successfully!" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Client failed to start. Check logs for errors." -ForegroundColor Red
    }
}

function Stop-Client {
    Show-Header
    
    if (-not (Test-ProcessRunning)) {
        Write-Host "[INFO] Client is not running" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Stopping monitoring client..." -ForegroundColor Yellow
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    Start-Sleep -Seconds 2
    
    if (-not (Test-ProcessRunning)) {
        Write-Host "[OK] Client stopped successfully!" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Forcing process termination..." -ForegroundColor Yellow
        Stop-Process -Name "VibgyorSeekMonitoring" -Force
        Write-Host "[OK] Client stopped" -ForegroundColor Green
    }
}

function Restart-Client {
    Show-Header
    Write-Host "Restarting monitoring client..." -ForegroundColor Yellow
    Stop-Client
    Start-Sleep -Seconds 1
    Start-Client
}

function Install-Task {
    Show-Header
    
    if (-not (Test-Path $ExePath)) {
        Write-Host "[ERROR] Executable not found: $ExePath" -ForegroundColor Red
        Write-Host "Please install the application first." -ForegroundColor Yellow
        return
    }
    
    if (Test-TaskExists) {
        Write-Host "[INFO] Task already exists. Removing old task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    Write-Host "Creating scheduled task..." -ForegroundColor Yellow
    Write-Host "  Executable: $ExePath" -ForegroundColor Gray
    Write-Host "  Working Directory: $InstallPath" -ForegroundColor Gray
    
    $action = New-ScheduledTaskAction -Execute $ExePath -WorkingDirectory $InstallPath
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Seconds 0)
    
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
    
    if (Test-TaskExists) {
        Write-Host "[OK] Task created successfully!" -ForegroundColor Green
        Write-Host ""
        $start = Read-Host "Start the client now? (Y/N)"
        if ($start -eq 'Y' -or $start -eq 'y') {
            Start-Client
        }
    } else {
        Write-Host "[ERROR] Failed to create task" -ForegroundColor Red
    }
}

function Uninstall-Task {
    Show-Header
    
    if (-not (Test-TaskExists)) {
        Write-Host "[INFO] Task does not exist" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Stopping client..." -ForegroundColor Yellow
    Stop-Client
    
    Write-Host "Removing scheduled task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    
    if (-not (Test-TaskExists)) {
        Write-Host "[OK] Task removed successfully!" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to remove task" -ForegroundColor Red
    }
}

function Show-Logs {
    Show-Header
    
    $logsPath = Join-Path $InstallPath "logs"
    if (-not (Test-Path $logsPath)) {
        Write-Host "[ERROR] Logs folder not found: $logsPath" -ForegroundColor Red
        return
    }
    
    $todayLog = Join-Path $logsPath "logs $(Get-Date -Format 'yyyy-MM-dd').txt"
    
    if (Test-Path $todayLog) {
        Write-Host "Opening today's log file..." -ForegroundColor Yellow
        Write-Host "Path: $todayLog" -ForegroundColor Gray
        Write-Host ""
        notepad $todayLog
    } else {
        Write-Host "[WARNING] Today's log file not found" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Available log files:" -ForegroundColor Yellow
        Get-ChildItem $logsPath -Filter "*.txt" | ForEach-Object {
            Write-Host "  $($_.Name)" -ForegroundColor Gray
        }
    }
}

# Main execution
switch ($Action) {
    'status' { Show-Status }
    'start' { Start-Client }
    'stop' { Stop-Client }
    'restart' { Restart-Client }
    'install' { Install-Task }
    'uninstall' { Uninstall-Task }
    'logs' { Show-Logs }
}

Write-Host ""
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  .\Manage-VibgyorSeek.ps1 status     - Show current status" -ForegroundColor Gray
Write-Host "  .\Manage-VibgyorSeek.ps1 start      - Start the client" -ForegroundColor Gray
Write-Host "  .\Manage-VibgyorSeek.ps1 stop       - Stop the client" -ForegroundColor Gray
Write-Host "  .\Manage-VibgyorSeek.ps1 restart    - Restart the client" -ForegroundColor Gray
Write-Host "  .\Manage-VibgyorSeek.ps1 install    - Install scheduled task" -ForegroundColor Gray
Write-Host "  .\Manage-VibgyorSeek.ps1 uninstall  - Remove scheduled task" -ForegroundColor Gray
Write-Host "  .\Manage-VibgyorSeek.ps1 logs       - View logs" -ForegroundColor Gray
Write-Host ""

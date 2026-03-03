# VibgyorSeek Monitoring Client - Deployment Guide

## The Problem You're Experiencing

Your monitoring client is tracking work/idle time but NOT tracking:
- ❌ Foreground applications
- ❌ Browser tabs
- ❌ Application usage details

### Root Cause: Windows Session 0 Isolation

When running as a Windows service via NSSM, the client runs in **Session 0** (system session), which cannot access user desktop windows due to Windows security restrictions. This is why:

- ✅ **Mouse/keyboard activity works** - Uses global system hooks
- ❌ **Application tracking doesn't work** - Requires access to user windows
- ❌ **Browser tab tracking doesn't work** - Requires access to browser windows

## Solution: Use Task Scheduler Instead of NSSM

The monitoring client must run **in the user's session** to access desktop windows.

---

## Quick Fix (Recommended)

### Step 1: Uninstall Current NSSM Service

Run as Administrator:

```batch
nssm stop VibgyorSeekMonitoring
nssm remove VibgyorSeekMonitoring confirm
```

### Step 2: Install as Scheduled Task

Navigate to your installation directory and run:

```batch
install_task_scheduler.bat
```

Or manually:

```batch
schtasks /create /tn "VibgyorSeek Monitoring" /tr "C:\Program Files\VibgyorSeekMonitoring\VibgyorSeekMonitoring.exe" /sc onlogon /rl highest /f
schtasks /run /tn "VibgyorSeek Monitoring"
```

### Step 3: Verify It's Working

Check the logs at `C:\Program Files\VibgyorSeekMonitoring\logs\logs YYYY-MM-DD.txt`:

You should now see:
```
🎯 [Poll 1] Foreground: Chrome.exe
⏱️  Added 10.0s to Chrome.exe → Total: 10.0s
🌐 [Poll 1] Updated browser tab usage
```

---

## For New Deployments

### Option 1: Use Updated Inno Setup Script (Recommended)

Use the new `VibgyorSeekMonitoring_TaskScheduler.iss` script instead of the NSSM version:

```batch
iscc VibgyorSeekMonitoring_TaskScheduler.iss
```

This will create an installer that:
- Installs the executable to `C:\Program Files\VibgyorSeekMonitoring\`
- Creates a scheduled task that runs at user login
- Starts the client immediately after installation
- Properly uninstalls when removed

### Option 2: Manual Deployment

1. Copy `VibgyorSeekMonitoring.exe` and `.env` to target directory
2. Run `install_task_scheduler.bat` as Administrator
3. Verify it's running in Task Manager

---

## Comparison: NSSM vs Task Scheduler

| Feature | NSSM Service | Task Scheduler |
|---------|-------------|----------------|
| Runs in user session | ❌ No (Session 0) | ✅ Yes |
| Can track applications | ❌ No | ✅ Yes |
| Can track browser tabs | ❌ No | ✅ Yes |
| Starts at boot | ✅ Yes | ❌ No (at login) |
| Runs without user login | ✅ Yes | ❌ No |
| Requires admin | ✅ Yes | ✅ Yes |
| Easy to manage | ✅ Yes | ✅ Yes |

**Verdict**: For monitoring client, Task Scheduler is the correct choice.

---

## Troubleshooting

### Check if Task is Running

```batch
schtasks /query /tn "VibgyorSeek Monitoring"
```

### Check if Process is Running

Open Task Manager and look for `VibgyorSeekMonitoring.exe`

### View Logs

Navigate to installation directory and open:
```
logs\logs YYYY-MM-DD.txt
```

Look for these indicators of success:
- `🎯 [Poll X] Foreground: AppName.exe` - Application tracking working
- `🌐 [Poll X] Updated browser tab usage` - Browser tracking working
- `⏱️  Added X.Xs to AppName.exe` - Time tracking working

### Common Issues

**Issue**: Task shows as "Running" but no logs appear
- **Solution**: Check if `.env` file is in the same directory as the executable

**Issue**: Task fails to start
- **Solution**: Verify the executable path in the task:
  ```batch
  schtasks /query /tn "VibgyorSeek Monitoring" /v /fo list
  ```

**Issue**: Application tracking still not working
- **Solution**: Ensure the task is running with "highest" privileges:
  ```batch
  schtasks /delete /tn "VibgyorSeek Monitoring" /f
  schtasks /create /tn "VibgyorSeek Monitoring" /tr "C:\Path\To\VibgyorSeekMonitoring.exe" /sc onlogon /rl highest /f
  ```

---

## Management Commands

### Start the Client
```batch
schtasks /run /tn "VibgyorSeek Monitoring"
```

### Stop the Client
```batch
schtasks /end /tn "VibgyorSeek Monitoring"
```

### Remove the Task
```batch
schtasks /delete /tn "VibgyorSeek Monitoring" /f
```

### Check Status
```batch
schtasks /query /tn "VibgyorSeek Monitoring"
```

---

## For System Administrators

### Silent Installation Script

```batch
@echo off
set "INSTALL_DIR=C:\Program Files\VibgyorSeekMonitoring"
set "EXE_PATH=%INSTALL_DIR%\VibgyorSeekMonitoring.exe"

REM Create directory
mkdir "%INSTALL_DIR%" 2>nul

REM Copy files (adjust source paths as needed)
copy /Y "VibgyorSeekMonitoring.exe" "%INSTALL_DIR%\"
copy /Y ".env" "%INSTALL_DIR%\"

REM Remove old task if exists
schtasks /end /tn "VibgyorSeek Monitoring" >nul 2>&1
schtasks /delete /tn "VibgyorSeek Monitoring" /f >nul 2>&1

REM Create new task
schtasks /create /tn "VibgyorSeek Monitoring" /tr "\"%EXE_PATH%\"" /sc onlogon /rl highest /f

REM Start immediately
schtasks /run /tn "VibgyorSeek Monitoring"

echo Installation complete
```

### Group Policy Deployment

You can deploy via GPO using:
1. Create a startup script that runs the installation
2. Or use Task Scheduler GPO preferences to create the task

---

## Why This Happens (Technical Details)

### Windows Session 0 Isolation

Since Windows Vista, Microsoft enforces Session 0 Isolation:

- **Session 0**: System services, no UI, no user interaction
- **Session 1+**: User sessions with desktop and UI access

### What This Means for Monitoring

| Function | Requires | Works in Session 0? |
|----------|----------|---------------------|
| Mouse/Keyboard hooks | System-level API | ✅ Yes |
| Get foreground window | User desktop access | ❌ No |
| Read window titles | User desktop access | ❌ No |
| Access browser tabs | User desktop access | ❌ No |

### The Fix

Running as a scheduled task at user logon ensures the client runs in the user's session (Session 1+), giving it full access to desktop windows and applications.

---

## Next Steps

1. **Uninstall NSSM service** (if currently installed)
2. **Install using Task Scheduler** method
3. **Verify logs** show application tracking
4. **Update your deployment process** to use the new Inno Setup script

The monitoring client will now properly track all user activity!

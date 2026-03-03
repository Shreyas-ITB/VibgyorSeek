# Rebuild Instructions - Windowless Background Mode

## What Changed

The executable now runs **without a console window** (in the background), making it perfect for scheduled task deployment.

### Changes Made:

1. **PyInstaller Spec File** (`monitoring_client.spec`)
   - Changed `console=True` to `console=False`
   - Application now runs as a windowless background process

2. **Task Scheduler Deployment** (`VibgyorSeekMonitoring_TaskScheduler.iss`)
   - Sets working directory to installation folder
   - Ensures `.env` file is found
   - Runs in user session for proper app tracking

## How to Rebuild

### Step 1: Activate Virtual Environment

```batch
cd monitoring-client
venv\Scripts\activate
```

### Step 2: Clean Previous Build

```batch
rmdir /s /q build dist
del /q *.spec~
```

### Step 3: Rebuild Executable

```batch
python -m PyInstaller --clean monitoring_client.spec
```

Or use the build script:

```batch
build.bat
```

### Step 4: Test the Executable

```batch
cd dist
VibgyorSeekMonitoring.exe --show-id
```

**Note**: You won't see a console window! Check Task Manager to verify it's running, then check the logs.

### Step 5: Stop the Test Process

Since there's no console window to close:

```batch
taskkill /IM VibgyorSeekMonitoring.exe /F
```

### Step 6: Build Installer

```batch
iscc VibgyorSeekMonitoring_TaskScheduler.iss
```

This creates `VibgyorSeekSetup.exe` with:
- The windowless executable
- Proper working directory configuration
- Automatic task scheduler setup

## Verification

### Check if Running in Background

1. **Task Manager**: Look for `VibgyorSeekMonitoring.exe` (no console window)
2. **Task Scheduler**: Check "VibgyorSeek Monitoring" task status
3. **Logs**: Check `C:\Program Files\VibgyorSeekMonitoring\logs\logs YYYY-MM-DD.txt`

### Expected Behavior

✅ No console window appears
✅ Process runs in background
✅ Logs are written to file
✅ Application tracking works
✅ Browser tracking works
✅ Can only be stopped via Task Manager or Task Scheduler

## Troubleshooting

### Can't See If It's Running

**Check Task Manager**:
- Press `Ctrl+Shift+Esc`
- Look for `VibgyorSeekMonitoring.exe` in Processes tab

**Check Logs**:
```batch
cd "C:\Program Files\VibgyorSeekMonitoring\logs"
type "logs 2026-03-04.txt"
```

### Need to Stop It

**Via Task Scheduler**:
```batch
schtasks /end /tn "VibgyorSeek Monitoring"
```

**Via Task Manager**:
- Find `VibgyorSeekMonitoring.exe`
- Right-click → End Task

**Via Command Line**:
```batch
taskkill /IM VibgyorSeekMonitoring.exe /F
```

### Want Console Mode for Debugging

If you need to see console output for debugging:

1. Edit `monitoring_client.spec`
2. Change `console=False` back to `console=True`
3. Rebuild
4. Run the executable - you'll see the console window

## Deployment Checklist

Before deploying to users:

- [ ] Rebuilt with `console=False`
- [ ] Tested executable runs without console window
- [ ] Verified logs are being written
- [ ] Compiled Inno Setup installer
- [ ] Tested installer creates task correctly
- [ ] Verified working directory is set
- [ ] Confirmed application tracking works
- [ ] Checked browser tracking works
- [ ] Tested on clean Windows machine

## Files to Deploy

After rebuilding, you need:

1. **VibgyorSeekSetup.exe** - The installer (from Inno Setup)
2. **Or manually**:
   - `dist\VibgyorSeekMonitoring.exe`
   - `.env` file (configured)
   - `install_task_scheduler.bat`

## Advantages of Windowless Mode

✅ **Silent Operation**: No visible windows
✅ **Professional**: Looks like a proper background service
✅ **User-Friendly**: Users don't see technical details
✅ **Clean**: No accidental window closures
✅ **Reliable**: Can't be closed by clicking X

## Disadvantages

❌ **Harder to Debug**: Can't see console output
❌ **Must Check Logs**: All output goes to log files
❌ **Task Manager Required**: To stop the process

## Best Practices

1. **Always check logs** after deployment
2. **Test on a clean machine** before rolling out
3. **Provide users with management scripts** (Manage-VibgyorSeek.ps1)
4. **Document how to check status** (QUICK_START.md)
5. **Include uninstall instructions** (uninstall_task_scheduler.bat)

## Quick Commands Reference

```batch
# Rebuild
python -m PyInstaller --clean monitoring_client.spec

# Build installer
iscc VibgyorSeekMonitoring_TaskScheduler.iss

# Check if running
tasklist | findstr VibgyorSeekMonitoring

# Stop process
taskkill /IM VibgyorSeekMonitoring.exe /F

# View logs
type "C:\Program Files\VibgyorSeekMonitoring\logs\logs 2026-03-04.txt"

# Check task status
schtasks /query /tn "VibgyorSeek Monitoring"

# Start task
schtasks /run /tn "VibgyorSeek Monitoring"

# Stop task
schtasks /end /tn "VibgyorSeek Monitoring"
```

## Support

If users report issues:

1. Ask them to check Task Manager for the process
2. Request the log file from `logs\logs YYYY-MM-DD.txt`
3. Verify the task exists in Task Scheduler
4. Check working directory is set correctly
5. Confirm `.env` file exists in installation folder

## Version History

- **v1.2** (Mar 4, 2026)
  - Changed to windowless background mode
  - Updated for Task Scheduler deployment
  - Fixed working directory configuration
  - Improved user experience

- **v1.1** (Mar 3, 2026)
  - Added date-based logging system
  - Fixed PyInstaller module detection
  - Improved build process reliability

- **v1.0** (Feb 27, 2026)
  - Initial standalone executable build
  - NSSM service deployment support

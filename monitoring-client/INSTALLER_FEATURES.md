# Installer Features - VibgyorSeek Monitoring Client

## Automatic Windows Defender Exclusions

Both installers now automatically add Windows Defender exclusions during installation!

### What Gets Excluded

1. **Installation Folder**: `C:\Program Files\VibgyorSeekMonitoring`
2. **Executable Process**: `VibgyorSeekMonitoring.exe`

### How It Works

During installation, the installer runs these PowerShell commands:

```powershell
Add-MpPreference -ExclusionPath 'C:\Program Files\VibgyorSeekMonitoring' -Force
Add-MpPreference -ExclusionProcess 'VibgyorSeekMonitoring.exe' -Force
```

This happens BEFORE the scheduled task is created, ensuring the application won't be blocked.

### During Uninstallation

The exclusions are automatically removed:

```powershell
Remove-MpPreference -ExclusionPath 'C:\Program Files\VibgyorSeekMonitoring' -Force
Remove-MpPreference -ExclusionProcess 'VibgyorSeekMonitoring.exe' -Force
```

## Available Installers

### 1. VibgyorSeekMonitoring_TaskScheduler.iss (Standard)

**Features:**
- ✅ Automatic Windows Defender exclusions
- ✅ Task Scheduler deployment
- ✅ Working directory configuration
- ✅ Runs in user session
- ⚠️ Requires rebuilt executable with `console=False`

**Use when:**
- You've rebuilt the executable with windowless mode
- You want the simplest deployment

**Build command:**
```batch
iscc VibgyorSeekMonitoring_TaskScheduler.iss
```

### 2. VibgyorSeekMonitoring_TaskScheduler_VBS.iss (Guaranteed Hidden)

**Features:**
- ✅ Automatic Windows Defender exclusions
- ✅ Task Scheduler deployment
- ✅ Working directory configuration
- ✅ VBS wrapper for guaranteed hidden execution
- ✅ Works even if executable has `console=True`

**Use when:**
- You want guaranteed no-window execution
- You haven't rebuilt the executable yet
- You want maximum compatibility

**Build command:**
```batch
iscc VibgyorSeekMonitoring_TaskScheduler_VBS.iss
```

## Installation Process

### What Happens During Install

1. **Copy Files**
   - VibgyorSeekMonitoring.exe → C:\Program Files\VibgyorSeekMonitoring\
   - .env → C:\Program Files\VibgyorSeekMonitoring\
   - VibgyorSeekMonitoring_Hidden.vbs → (VBS version only)

2. **Add Defender Exclusions**
   - Excludes installation folder
   - Excludes executable process
   - Prevents antivirus blocking

3. **Create Scheduled Task**
   - Task name: "VibgyorSeek Monitoring"
   - Trigger: At user logon
   - Runs with highest privileges
   - Working directory set correctly

4. **Start Client**
   - Runs the task immediately
   - No need to wait for next logon

### What Happens During Uninstall

1. **Stop Client**
   - Ends the scheduled task
   - Terminates the process

2. **Remove Task**
   - Deletes scheduled task

3. **Remove Exclusions**
   - Removes folder exclusion
   - Removes process exclusion

4. **Delete Files**
   - Removes installation folder
   - Cleans up completely

## Requirements

### System Requirements

- Windows 10 or later
- Administrator privileges (for installation)
- PowerShell (for Defender exclusions)
- Task Scheduler (built-in)

### Files Needed for Build

**Standard Installer:**
- VibgyorSeekMonitoring.exe (rebuilt with console=False)
- .env (configured)
- VibgyorSeekMonitoring_TaskScheduler.iss

**VBS Installer:**
- VibgyorSeekMonitoring.exe (any version)
- VibgyorSeekMonitoring_Hidden.vbs
- .env (configured)
- VibgyorSeekMonitoring_TaskScheduler_VBS.iss

## Building the Installer

### Step 1: Prepare Files

```batch
cd monitoring-client

# Make sure you have:
# - dist\VibgyorSeekMonitoring.exe
# - .env (configured)
# - VibgyorSeekMonitoring_Hidden.vbs (for VBS version)
```

### Step 2: Build Installer

**Standard version:**
```batch
iscc VibgyorSeekMonitoring_TaskScheduler.iss
```

**VBS version (recommended):**
```batch
iscc VibgyorSeekMonitoring_TaskScheduler_VBS.iss
```

### Step 3: Test Installer

```batch
# Run the installer
VibgyorSeekSetup.exe

# Verify installation
schtasks /query /tn "VibgyorSeek Monitoring"
tasklist | findstr VibgyorSeekMonitoring

# Check exclusions
powershell -Command "Get-MpPreference | Select-Object -ExpandProperty ExclusionPath"
```

## Verification

### Check Defender Exclusions

**PowerShell:**
```powershell
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess
```

You should see:
- `C:\Program Files\VibgyorSeekMonitoring`
- `VibgyorSeekMonitoring.exe`

### Check Task Scheduler

```batch
schtasks /query /tn "VibgyorSeek Monitoring" /v /fo list
```

Look for:
- Status: Running
- Task To Run: (should show wscript.exe for VBS version)
- Start In: C:\Program Files\VibgyorSeekMonitoring

### Check Process

```batch
tasklist | findstr VibgyorSeekMonitoring
```

Should show the process running.

### Check Logs

```batch
type "C:\Program Files\VibgyorSeekMonitoring\logs\logs 2026-03-04.txt"
```

Should show recent log entries.

## Troubleshooting

### "Exclusions not added"

**Check if PowerShell is available:**
```batch
powershell -Command "Write-Host 'PowerShell works'"
```

**Manually add exclusions:**
```powershell
Add-MpPreference -ExclusionPath "C:\Program Files\VibgyorSeekMonitoring" -Force
Add-MpPreference -ExclusionProcess "VibgyorSeekMonitoring.exe" -Force
```

### "Task not created"

**Check if schtasks works:**
```batch
schtasks /query
```

**Manually create task:**
```batch
cd "C:\Program Files\VibgyorSeekMonitoring"
install_task_scheduler.bat
```

### "Still shows console window"

**Use VBS installer:**
```batch
iscc VibgyorSeekMonitoring_TaskScheduler_VBS.iss
```

The VBS wrapper guarantees no window will show.

## Deployment Tips

### For IT Administrators

1. **Test on clean VM first**
2. **Deploy via Group Policy** if possible
3. **Provide users with documentation**
4. **Monitor first few deployments**
5. **Have rollback plan ready**

### For Silent Installation

```batch
VibgyorSeekSetup.exe /VERYSILENT /NORESTART
```

### For Unattended Installation

```batch
VibgyorSeekSetup.exe /SILENT /SUPPRESSMSGBOXES /NORESTART
```

## Security Notes

### Exclusions Are Safe

The exclusions only apply to:
- The specific installation folder
- The specific executable name

They don't weaken overall system security.

### Why Exclusions Are Needed

PyInstaller executables are commonly flagged as false positives because:
- Self-extracting behavior
- Bundled Python interpreter
- Monitoring keyboard/mouse (legitimate for this app)

### For Production

Consider:
- Code signing certificate ($100-400/year)
- Submit to Microsoft for whitelisting
- Enterprise deployment via SCCM/Intune

## Summary

Both installers now automatically:
- ✅ Add Windows Defender exclusions
- ✅ Create scheduled task with proper configuration
- ✅ Set working directory correctly
- ✅ Start the client immediately
- ✅ Clean up completely on uninstall

The VBS version additionally:
- ✅ Guarantees no console window
- ✅ Works with any executable version
- ✅ Maximum compatibility

**Recommended**: Use the VBS installer for most reliable deployment!

# Quick Fix Guide - Console Window & Antivirus Issues

## Problem 1: Console Window Still Showing

### Why This Happens
You're running the OLD executable that was built with `console=True`. The spec file was updated, but you haven't rebuilt the executable yet.

### Solution: Rebuild the Executable

**Step 1: Run the rebuild script**
```batch
cd monitoring-client
REBUILD_NOW.bat
```

**Step 2: Verify the new executable**
```batch
cd dist
dir VibgyorSeekMonitoring.exe
```
Check the date/time - it should be recent (just now).

**Step 3: Test it**
```batch
VibgyorSeekMonitoring.exe --show-id
```
You should NOT see a console window. Check Task Manager to verify it's running.

**Step 4: Stop the test**
```batch
taskkill /IM VibgyorSeekMonitoring.exe /F
```

**Step 5: Rebuild the installer**
```batch
cd ..
iscc VibgyorSeekMonitoring_TaskScheduler_VBS.iss
```

**Step 6: Uninstall old version and install new one**
```batch
# Uninstall old
schtasks /end /tn "VibgyorSeek Monitoring"
schtasks /delete /tn "VibgyorSeek Monitoring" /f

# Install new
VibgyorSeekSetup.exe
```

---

## Problem 2: Antivirus Blocking

### Quick Fix: Whitelist in Windows Defender

**Method 1: Via PowerShell (Fastest)**

Run PowerShell as Administrator:
```powershell
Add-MpPreference -ExclusionPath "C:\Program Files\VibgyorSeekMonitoring"
Add-MpPreference -ExclusionProcess "VibgyorSeekMonitoring.exe"
```

**Method 2: Via Windows Security**

1. Open Windows Security
2. Virus & threat protection → Manage settings
3. Exclusions → Add or remove exclusions
4. Add folder: `C:\Program Files\VibgyorSeekMonitoring`

**Method 3: During Installation**

Before running the installer:
1. Add exclusion for the folder
2. Then run the installer
3. Antivirus won't block it

### Long-term Fix: Code Signing

For production deployment, get a code signing certificate:
- Cost: $100-400/year
- Eliminates false positives
- Professional appearance
- See ANTIVIRUS_WHITELIST.md for details

---

## Alternative: Use VBS Wrapper (Guaranteed Hidden)

If rebuilding doesn't work, use the VBS wrapper:

**Step 1: Copy the VBS file**
```batch
copy VibgyorSeekMonitoring_Hidden.vbs "C:\Program Files\VibgyorSeekMonitoring\"
```

**Step 2: Test it**
```batch
cd "C:\Program Files\VibgyorSeekMonitoring"
wscript VibgyorSeekMonitoring_Hidden.vbs
```

No window should appear! Check Task Manager.

**Step 3: Update the task to use VBS**
```batch
schtasks /delete /tn "VibgyorSeek Monitoring" /f

schtasks /create /tn "VibgyorSeek Monitoring" ^
  /tr "wscript.exe \"C:\Program Files\VibgyorSeekMonitoring\VibgyorSeekMonitoring_Hidden.vbs\"" ^
  /sc onlogon /rl highest /f

schtasks /run /tn "VibgyorSeek Monitoring"
```

**Or use the VBS installer:**
```batch
iscc VibgyorSeekMonitoring_TaskScheduler_VBS.iss
```

---

## Verification Checklist

After fixing:

- [ ] No console window appears when running
- [ ] Process shows in Task Manager
- [ ] Logs are being written (`logs\logs YYYY-MM-DD.txt`)
- [ ] Application tracking works (check logs for "🎯 [Poll X] Foreground:")
- [ ] Antivirus doesn't block it
- [ ] Task Scheduler shows it running

---

## Troubleshooting

### "I rebuilt but still see console window"

**Check you're using the NEW executable:**
```batch
cd "C:\Program Files\VibgyorSeekMonitoring"
dir VibgyorSeekMonitoring.exe
```

If the date is old, you're using the old file. Copy the new one:
```batch
copy /Y "D:\path\to\monitoring-client\dist\VibgyorSeekMonitoring.exe" "C:\Program Files\VibgyorSeekMonitoring\"
```

### "Antivirus keeps blocking it"

**Whitelist BEFORE running:**
```powershell
Add-MpPreference -ExclusionPath "C:\Program Files\VibgyorSeekMonitoring"
Add-MpPreference -ExclusionPath "D:\path\to\monitoring-client\dist"
```

Then rebuild and install.

### "VBS wrapper doesn't work"

**Check if VBS is blocked:**
```batch
wscript /?
```

If you see help, VBS works. If not, VBS might be disabled by policy.

**Alternative: Use PowerShell wrapper:**
```powershell
Start-Process -FilePath "C:\Program Files\VibgyorSeekMonitoring\VibgyorSeekMonitoring.exe" -WindowStyle Hidden
```

---

## Quick Commands

```batch
# Rebuild executable
cd monitoring-client
REBUILD_NOW.bat

# Whitelist in Defender
powershell -Command "Add-MpPreference -ExclusionPath 'C:\Program Files\VibgyorSeekMonitoring'"

# Build VBS installer
iscc VibgyorSeekMonitoring_TaskScheduler_VBS.iss

# Check if running
tasklist | findstr VibgyorSeekMonitoring

# Stop process
taskkill /IM VibgyorSeekMonitoring.exe /F

# View logs
type "C:\Program Files\VibgyorSeekMonitoring\logs\logs 2026-03-04.txt"
```

---

## Summary

1. **Console window issue**: Rebuild with updated spec file
2. **Antivirus issue**: Whitelist the folder before installing
3. **Backup solution**: Use VBS wrapper for guaranteed hidden execution

Follow the steps above and you'll have a fully hidden, working monitoring client!

# Quick Start Guide - VibgyorSeek Monitoring Client

## After Installation - How to Check and Start

### Step 1: Check if Task Was Created

Open Command Prompt or PowerShell **as Administrator** and run:

```batch
schtasks /query /tn "VibgyorSeek Monitoring"
```

**Expected Output:**
```
Folder: \
TaskName                                 Next Run Time          Status
======================================== ====================== ===============
VibgyorSeek Monitoring                   N/A                    Ready
```

### Step 2: Check if It's Running

```batch
tasklist | findstr VibgyorSeekMonitoring
```

**Expected Output:**
```
VibgyorSeekMonitoring.exe    12345 Console                 1     45,678 K
```

If you see this, the client is running! ✅

### Step 3: Start It Manually (if not running)

```batch
schtasks /run /tn "VibgyorSeek Monitoring"
```

### Step 4: Verify It's Working

Check the logs at:
```
C:\Program Files\VibgyorSeekMonitoring\logs\logs YYYY-MM-DD.txt
```

Look for these lines (they should appear every 10 seconds):
```
🎯 [Poll 1] Foreground: Chrome.exe
⏱️  Added 10.0s to Chrome.exe → Total: 10.0s
🌐 [Poll 1] Updated browser tab usage
```

---

## If Task Doesn't Exist

The installation might have failed. Run this script to create it manually:

**Option 1: Use the Fix Script (Recommended)**

Navigate to installation directory and run:
```batch
fix_working_directory.bat
```

This creates the task with the correct working directory so the exe can find the `.env` file.

**Option 2: Use the Helper Script**

Navigate to installation directory and run:
```batch
check_and_start.bat
```

**Option 3: Use Install Script**

```batch
cd "C:\Program Files\VibgyorSeekMonitoring"
install_task_scheduler.bat
```

## If Task Exists But Not Working

The task might not have the working directory set correctly. This is critical because the exe needs to find the `.env` file.

**Fix it by running:**

```batch
cd "C:\Program Files\VibgyorSeekMonitoring"
fix_working_directory.bat
```

This will recreate the task with the proper working directory.

---

## Using Task Scheduler GUI

1. Press `Win + R`
2. Type `taskschd.msc` and press Enter
3. Click "Task Scheduler Library" in the left panel
4. Find "VibgyorSeek Monitoring" in the list
5. Right-click to:
   - **Run** - Start the client now
   - **End** - Stop the client
   - **Properties** - View/edit settings
   - **Delete** - Remove the task

---

## Common Commands

### Start the Client
```batch
schtasks /run /tn "VibgyorSeek Monitoring"
```

### Stop the Client
```batch
schtasks /end /tn "VibgyorSeek Monitoring"
```

### Check Status
```batch
schtasks /query /tn "VibgyorSeek Monitoring"
```

### View Detailed Info
```batch
schtasks /query /tn "VibgyorSeek Monitoring" /v /fo list
```

### Check if Process is Running
```batch
tasklist | findstr VibgyorSeekMonitoring
```

### View Logs
```batch
cd "C:\Program Files\VibgyorSeekMonitoring\logs"
dir
notepad "logs 2026-03-04.txt"
```

---

## Troubleshooting

### Task exists but won't start

**Check the executable path:**
```batch
schtasks /query /tn "VibgyorSeek Monitoring" /v /fo list | findstr "Task To Run"
```

Make sure it points to the correct location.

**Recreate the task:**
```batch
schtasks /delete /tn "VibgyorSeek Monitoring" /f
schtasks /create /tn "VibgyorSeek Monitoring" /tr "\"C:\Program Files\VibgyorSeekMonitoring\VibgyorSeekMonitoring.exe\"" /sc onlogon /rl highest /f
schtasks /run /tn "VibgyorSeek Monitoring"
```

### Process starts but immediately stops

**Check the logs for errors:**
```batch
cd "C:\Program Files\VibgyorSeekMonitoring\logs"
type "logs 2026-03-04.txt"
```

**Common issues:**
- Missing `.env` file
- Invalid configuration in `.env`
- Missing dependencies

### No logs are created

**Check if the logs folder exists:**
```batch
cd "C:\Program Files\VibgyorSeekMonitoring"
dir logs
```

If it doesn't exist, the client will create it automatically when it runs.

---

## Verification Checklist

After installation, verify:

- [ ] Task exists: `schtasks /query /tn "VibgyorSeek Monitoring"`
- [ ] Process is running: `tasklist | findstr VibgyorSeekMonitoring`
- [ ] Logs folder exists: `C:\Program Files\VibgyorSeekMonitoring\logs`
- [ ] Today's log file exists: `logs\logs YYYY-MM-DD.txt`
- [ ] Log shows polling: Look for "🎯 [Poll X] Foreground:" messages
- [ ] Dashboard shows data: Check the web dashboard

---

## Need Help?

Run the diagnostic script:
```batch
cd "C:\Program Files\VibgyorSeekMonitoring"
check_and_start.bat
```

This will:
- Check if the task exists
- Check if the process is running
- Offer to create/start the task if needed
- Show you the current status

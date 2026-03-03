# Windows Service Session 0 Isolation Fix

## Problem

When the monitoring client runs as a Windows service, it cannot track foreground applications or browser tabs because:

1. **Session 0 Isolation**: Windows services run in Session 0 (system session)
2. **User Desktop**: User applications run in Session 1+ (user sessions)
3. **Security Restriction**: Services in Session 0 cannot access user desktop windows

This is why you see:
- ✅ Work/Idle time tracking works (uses global mouse/keyboard hooks)
- ❌ Application tracking doesn't work (needs window access)
- ❌ Browser tab tracking doesn't work (needs window access)

## Solution

The service must run **in the user's session** instead of Session 0.

### Option 1: Run as User Login Application (Recommended)

Instead of running as a system service, run the client as a startup application:

1. **Create a startup shortcut**:
   - Press `Win + R`, type `shell:startup`, press Enter
   - Create a shortcut to `VibgyorSeekMonitoring.exe`
   - The client will start automatically when the user logs in

2. **Advantages**:
   - Full access to user desktop and applications
   - No Session 0 isolation issues
   - Simpler deployment

3. **Disadvantages**:
   - User can see and close the application
   - Doesn't start until user logs in

### Option 2: NSSM with Interactive Service (Not Recommended)

Configure NSSM to run the service interactively:

```batch
nssm set VibgyorSeekMonitoring Type SERVICE_INTERACTIVE_PROCESS
```

**Warning**: This is deprecated in modern Windows and may not work reliably.

### Option 3: Run as Scheduled Task (Recommended for Enterprise)

Use Windows Task Scheduler to run the client at user login:

1. **Create a scheduled task**:
   ```batch
   schtasks /create /tn "VibgyorSeek Monitoring" /tr "C:\Program Files\VibgyorSeekMonitoring\VibgyorSeekMonitoring.exe" /sc onlogon /rl highest /f
   ```

2. **Configure the task**:
   - Trigger: At log on of any user
   - Run with highest privileges
   - Run whether user is logged on or not: NO (must be logged on)

3. **Advantages**:
   - Runs in user session
   - Starts automatically at login
   - Can run with elevated privileges
   - More reliable than interactive service

4. **Disadvantages**:
   - Slightly more complex setup
   - Requires user to be logged in

## Recommended Deployment Method

For the monitoring client, **use Windows Task Scheduler** (Option 3):

### Updated Inno Setup Script

```iss
[Setup]
AppName=VibgyorSeek Monitoring
AppVersion=1.0
DefaultDirName={commonpf}\VibgyorSeekMonitoring
DefaultGroupName=VibgyorSeek Monitoring
OutputDir=.
OutputBaseFilename=VibgyorSeekSetup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "VibgyorSeekMonitoring.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion

[Run]
; Create scheduled task to run at user login
Filename: "schtasks.exe"; Parameters: "/create /tn ""VibgyorSeek Monitoring"" /tr ""\""{app}\VibgyorSeekMonitoring.exe\"""" /sc onlogon /rl highest /f"; Flags: runhidden

[UninstallRun]
; Remove scheduled task
Filename: "schtasks.exe"; Parameters: "/delete /tn ""VibgyorSeek Monitoring"" /f"; Flags: runhidden; RunOnceId: "RemoveTask"
```

### Manual Setup (Alternative)

If you want to keep using NSSM but need it to work, you'll need to:

1. **Stop the current service**:
   ```batch
   nssm stop VibgyorSeekMonitoring
   nssm remove VibgyorSeekMonitoring confirm
   ```

2. **Create a scheduled task instead**:
   ```batch
   schtasks /create /tn "VibgyorSeek Monitoring" /tr "C:\Program Files\VibgyorSeekMonitoring\VibgyorSeekMonitoring.exe" /sc onlogon /rl highest /f
   ```

3. **Verify it's running**:
   ```batch
   schtasks /query /tn "VibgyorSeek Monitoring"
   ```

## Testing

After switching to scheduled task:

1. Log out and log back in
2. Check Task Manager - you should see `VibgyorSeekMonitoring.exe` running
3. Check the logs - you should now see:
   ```
   🎯 [Poll 1] Foreground: Chrome.exe
   ⏱️  Added 10.0s to Chrome.exe → Total: 10.0s
   🌐 [Poll 1] Updated browser tab usage
   ```

## Why This Happens

Windows Vista and later enforce **Session 0 Isolation** for security:
- Session 0: System services (no UI access)
- Session 1+: User sessions (with UI access)

Services cannot interact with user desktops, so they can't:
- Get foreground window information
- Access browser tabs
- See what applications are running in the user's context

The monitoring client MUST run in the user's session to track applications.

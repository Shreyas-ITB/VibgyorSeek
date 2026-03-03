# VibgyorSeek Monitoring Client - NSSM Deployment Guide

This guide explains how to deploy the monitoring client as a Windows service using NSSM (Non-Sucking Service Manager).

## Prerequisites

1. **NSSM (Non-Sucking Service Manager)**
   - Download from: https://nssm.cc/download
   - Extract the appropriate version (32-bit or 64-bit)
   - Either add `nssm.exe` to your system PATH or place it in the monitoring-client folder

2. **Built Executable**
   - The `VibgyorSeekMonitoring.exe` file should be in the `dist` folder
   - If not built yet, run: `pyinstaller monitoring_client.spec`

3. **Administrator Privileges**
   - Service installation requires administrator rights

## Quick Installation

### Option 1: Using the Installation Script (Recommended)

1. Right-click `install_service_nssm.bat`
2. Select "Run as administrator"
3. Follow the on-screen prompts

The script will:
- Check for NSSM availability
- Verify the executable exists
- Remove any existing service with the same name
- Install and configure the service
- Start the service automatically

### Option 2: Manual Installation

Open Command Prompt or PowerShell as Administrator and run:

```cmd
# Install the service
nssm install VibgyorSeekMonitoring "C:\path\to\monitoring-client\dist\VibgyorSeekMonitoring.exe"

# Configure the service
nssm set VibgyorSeekMonitoring DisplayName "VibgyorSeek Employee Monitoring"
nssm set VibgyorSeekMonitoring Description "Monitors employee activity and transmits data to the central server"
nssm set VibgyorSeekMonitoring Start SERVICE_AUTO_START
nssm set VibgyorSeekMonitoring AppDirectory "C:\path\to\monitoring-client"

# Configure logging
nssm set VibgyorSeekMonitoring AppStdout "C:\path\to\monitoring-client\logs\service_stdout.log"
nssm set VibgyorSeekMonitoring AppStderr "C:\path\to\monitoring-client\logs\service_stderr.log"
nssm set VibgyorSeekMonitoring AppRotateFiles 1
nssm set VibgyorSeekMonitoring AppRotateOnline 1
nssm set VibgyorSeekMonitoring AppRotateBytes 10485760

# Start the service
nssm start VibgyorSeekMonitoring
```

## Service Management

### Start the Service
```cmd
nssm start VibgyorSeekMonitoring
```

### Stop the Service
```cmd
nssm stop VibgyorSeekMonitoring
```

### Restart the Service
```cmd
nssm restart VibgyorSeekMonitoring
```

### Check Service Status
```cmd
nssm status VibgyorSeekMonitoring
```

### View Service Configuration
```cmd
nssm edit VibgyorSeekMonitoring
```
This opens a GUI where you can modify service settings.

### Uninstall the Service

#### Option 1: Using the Uninstallation Script
1. Right-click `uninstall_service_nssm.bat`
2. Select "Run as administrator"

#### Option 2: Manual Uninstallation
```cmd
nssm stop VibgyorSeekMonitoring
nssm remove VibgyorSeekMonitoring confirm
```

## Configuration

### Environment Variables
The service will use the `.env` file in the monitoring-client directory. Make sure to configure it before starting the service:

```env
SERVER_URL=http://your-server:3000
DATA_SEND_INTERVAL_MINUTES=5
SCREENSHOT_INTERVAL_MINUTES=10
IDLE_THRESHOLD_SECONDS=300
```

### Logs
Service logs are stored in:
- `logs/service_stdout.log` - Standard output
- `logs/service_stderr.log` - Error output
- `logs/monitoring.log` - Application logs

Logs are automatically rotated when they reach 10MB.

## Troubleshooting

### Service Won't Start
1. Check if the executable exists: `dist\VibgyorSeekMonitoring.exe`
2. Verify the `.env` file is configured correctly
3. Check service logs in the `logs` folder
4. Run the executable manually to see if there are any errors:
   ```cmd
   cd dist
   VibgyorSeekMonitoring.exe
   ```

### Service Crashes or Stops
1. Check `logs/service_stderr.log` for error messages
2. Check `logs/monitoring.log` for application errors
3. Verify server connectivity
4. Ensure all required files are present

### NSSM Not Found
- Download NSSM from https://nssm.cc/download
- Extract and add to PATH, or place `nssm.exe` in the monitoring-client folder

### Permission Denied
- Ensure you're running commands as Administrator
- Check that the service account has access to the monitoring-client folder

## Advanced Configuration

### Failure Recovery
NSSM automatically configures the service to restart on failure. To customize:

```cmd
nssm set VibgyorSeekMonitoring AppExit Default Restart
nssm set VibgyorSeekMonitoring AppRestartDelay 60000
```

### Service Dependencies
If the service depends on network or other services:

```cmd
nssm set VibgyorSeekMonitoring DependOnService LanmanWorkstation
```

### Run as Different User
By default, the service runs as Local System. To run as a different user:

```cmd
nssm set VibgyorSeekMonitoring ObjectName DOMAIN\Username Password
```

## Deployment to Multiple Machines

For deploying to multiple machines:

1. Build the executable once
2. Copy the entire `monitoring-client` folder to target machines
3. Configure the `.env` file on each machine
4. Run `install_service_nssm.bat` as Administrator on each machine

Alternatively, create a deployment package:
- Include `dist\VibgyorSeekMonitoring.exe`
- Include `install_service_nssm.bat`
- Include `nssm.exe` (for convenience)
- Include `.env.example` (to be renamed and configured)

## Benefits of Using NSSM

- **Simple**: No complex service wrapper code needed
- **Reliable**: Battle-tested service manager used by thousands
- **Flexible**: Easy to configure and manage
- **Logging**: Built-in log rotation and management
- **Recovery**: Automatic restart on failure
- **GUI**: Optional GUI for configuration
- **No Dependencies**: No need for pywin32 or other service libraries

## Support

For issues or questions:
- Check the logs in the `logs` folder
- Review the NSSM documentation: https://nssm.cc/usage
- Contact your system administrator

# VibgyorSeek Monitoring Client - Installation Guide

This guide covers building, deploying, and installing the VibgyorSeek Employee Monitoring Client as a Windows service.

## Requirements

- Windows 7 or later (64-bit recommended)
- Administrator privileges for service installation
- Network access to the monitoring server

## Building the Executable

### Prerequisites for Building

1. Python 3.8 or later
2. Virtual environment with all dependencies installed
3. PyInstaller 6.3.0 or later

### Build Steps

1. **Activate the virtual environment:**
   ```cmd
   venv\Scripts\activate
   ```

2. **Run the build script:**
   ```cmd
   build.bat
   ```

   Or manually:
   ```cmd
   pyinstaller --clean monitoring_client.spec
   ```

3. **Locate the executable:**
   - The executable will be created in: `dist\VibgyorSeekMonitoring.exe`
   - This is a standalone executable that includes all dependencies

### Build Output

The build process creates:
- `dist\VibgyorSeekMonitoring.exe` - The standalone executable (~50-80 MB)
- `build\` - Temporary build files (can be deleted)

## Deploying to Target Machines

### Files to Deploy

1. **VibgyorSeekMonitoring.exe** - The main executable
2. **.env** - Configuration file (create from .env.example)

### Deployment Steps

1. **Copy the executable to the target machine:**
   ```
   C:\Program Files\VibgyorSeek\VibgyorSeekMonitoring.exe
   ```

2. **Create the configuration file:**
   - Copy `.env.example` to the same directory as the executable
   - Rename it to `.env`
   - Edit the configuration values:
     ```
     SERVER_URL=https://your-server.com/api/monitoring/data
     AUTH_TOKEN=your-auth-token-here
     SCREENSHOT_INTERVAL_MINUTES=10
     DATA_SEND_INTERVAL_MINUTES=10
     IDLE_THRESHOLD_SECONDS=300
     SCREENSHOT_QUALITY=75
     LOG_LEVEL=INFO
     ```

## Installing as a Windows Service

### Installation Steps

1. **Open Command Prompt as Administrator**

2. **Navigate to the installation directory:**
   ```cmd
   cd "C:\Program Files\VibgyorSeek"
   ```

3. **Run first-time setup (configure employee name):**
   ```cmd
   VibgyorSeekMonitoring.exe --setup
   ```
   - A dialog will appear asking for the employee name
   - Enter the employee name and click OK
   - This only needs to be done once per machine

4. **Install the service:**
   ```cmd
   VibgyorSeekMonitoring.exe --install
   ```
   - This registers the service with Windows
   - The service is configured to start automatically on boot
   - The service is configured to restart on failure

5. **Start the service:**
   ```cmd
   VibgyorSeekMonitoring.exe --start
   ```

6. **Verify the service is running:**
   ```cmd
   VibgyorSeekMonitoring.exe --status
   ```

### Service Management Commands

- **Check status:**
  ```cmd
  VibgyorSeekMonitoring.exe --status
  ```

- **Stop the service:**
  ```cmd
  VibgyorSeekMonitoring.exe --stop
  ```

- **Start the service:**
  ```cmd
  VibgyorSeekMonitoring.exe --start
  ```

- **Remove the service:**
  ```cmd
  VibgyorSeekMonitoring.exe --remove
  ```

### Using Windows Services Manager

You can also manage the service through Windows Services:

1. Press `Win + R` and type `services.msc`
2. Find "VBSeek"
3. Right-click to Start, Stop, or configure the service

## Testing the Installation

### Console Mode Testing

Before installing as a service, you can test the client in console mode:

```cmd
VibgyorSeekMonitoring.exe --console
```

This runs the monitoring client in the foreground, showing real-time status updates. Press Ctrl+C to stop.

### Verify Data Transmission

1. Check the log file:
   - Location: `logs\monitoring_client.log` (in the same directory as the executable)
   - Look for "Data transmitted successfully" messages

2. Check the server:
   - Verify that data is being received by the monitoring server
   - Check the dashboard for the employee's data

### Common Issues

**Issue: "Employee name not configured"**
- Solution: Run `VibgyorSeekMonitoring.exe --setup` first

**Issue: "Failed to connect to server"**
- Check the SERVER_URL in the .env file
- Verify network connectivity to the server
- Check firewall settings

**Issue: "Service failed to start"**
- Check the Windows Event Log for error details
- Verify the .env file is in the same directory as the executable
- Ensure the configuration is valid

**Issue: "Access denied" when installing service**
- Run Command Prompt as Administrator
- Ensure you have administrative privileges

## Uninstallation

1. **Stop the service:**
   ```cmd
   VibgyorSeekMonitoring.exe --stop
   ```

2. **Remove the service:**
   ```cmd
   VibgyorSeekMonitoring.exe --remove
   ```

3. **Delete the installation directory:**
   ```cmd
   rmdir /s "C:\Program Files\VibgyorSeek"
   ```

4. **Clean up configuration (optional):**
   - Employee configuration is stored in: `%APPDATA%\VibgyorSeek\config.json`
   - Delete this file to remove the employee name

## Security Considerations

- The service runs with SYSTEM privileges by default
- Only administrators can stop or modify the service
- Regular users cannot terminate the monitoring process
- All data is transmitted over HTTPS
- Authentication tokens should be kept secure

## Troubleshooting

### Enable Debug Logging

Edit the .env file and set:
```
LOG_LEVEL=DEBUG
```

Then restart the service to get more detailed logs.

### Check Windows Event Log

1. Open Event Viewer (eventvwr.msc)
2. Navigate to: Windows Logs > Application
3. Look for events from "VibgyorSeekMonitoring"

### Test Network Connectivity

```cmd
curl -X POST %SERVER_URL% -H "Authorization: Bearer %AUTH_TOKEN%"
```

## Support

For issues or questions, contact your system administrator or refer to the main project documentation.

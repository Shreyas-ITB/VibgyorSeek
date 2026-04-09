# Monitoring Client - Rust Implementation Requirements

## Overview
This document outlines the requirements for building a Rust-based employee monitoring client that replicates the functionality of the existing Python implementation. The client monitors user activity, captures screenshots, tracks application usage, and transmits data to a central server.

## 1. Core Functionality Requirements

### 1.1 Activity Tracking
- **REQ-1.1**: Monitor keyboard and mouse input events to determine user activity state
- **REQ-1.2**: Maintain two states: WORK (active) and IDLE (inactive)
- **REQ-1.3**: Track cumulative work seconds and idle seconds per interval
- **REQ-1.4**: Configurable idle threshold (default: 300 seconds)
- **REQ-1.5**: Thread-safe state management for concurrent access

### 1.2 Application Monitoring
- **REQ-2.1**: Enumerate all running user-facing applications
- **REQ-2.2**: Identify the foreground (active) application
- **REQ-2.3**: Filter out system processes and background services
- **REQ-2.4**: Cross-platform support (Windows primary, Linux/macOS secondary)
- **REQ-2.5**: Track cumulative usage time per application

### 1.3 Browser Monitoring
- **REQ-3.1**: Detect running browsers (Chrome, Firefox, Edge)
- **REQ-3.2**: Extract open tab information (title, URL)
- **REQ-3.3**: Track cumulative time per browser tab
- **REQ-3.4**: Support multiple browser profiles
- **REQ-3.5**: Handle browser-specific data formats (SQLite, JSON, LZ4)

### 1.4 Screenshot Capture
- **REQ-4.1**: Capture full desktop screenshots including all monitors
- **REQ-4.2**: Compress screenshots to JPEG format
- **REQ-4.3**: Configurable JPEG quality (1-100, default: 75)
- **REQ-4.4**: Base64 encode screenshot data for transmission
- **REQ-4.5**: Configurable screenshot interval (default: 10 minutes)

### 1.5 Location Tracking
- **REQ-5.1**: Determine geographic location via IP-based geolocation
- **REQ-5.2**: Cache location data to minimize API calls
- **REQ-5.3**: Provide city, state, and country information
- **REQ-5.4**: Configurable location update interval (default: 30 minutes)
- **REQ-5.5**: Graceful fallback when location unavailable

## 2. Data Management Requirements

### 2.1 Configuration Management
- **REQ-6.1**: Load configuration from .env file
- **REQ-6.2**: Support environment variable overrides
- **REQ-6.3**: Hot-reload configuration without restart
- **REQ-6.4**: Validate configuration values with sensible defaults
- **REQ-6.5**: Store persistent client ID and employee name

### 2.2 Payload Construction
- **REQ-7.1**: Aggregate data from all monitoring modules
- **REQ-7.2**: Build JSON payload with timestamp and interval information
- **REQ-7.3**: Include activity data (work/idle seconds)
- **REQ-7.4**: Include application list with usage durations
- **REQ-7.5**: Include browser tabs with usage durations
- **REQ-7.6**: Include screenshot data (base64 encoded)
- **REQ-7.7**: Include location data when available

### 2.3 Queue Management
- **REQ-8.1**: Persist failed payloads to SQLite database
- **REQ-8.2**: FIFO queue processing
- **REQ-8.3**: Maximum queue size limit (1000 payloads)
- **REQ-8.4**: Track retry count per payload
- **REQ-8.5**: Remove payloads exceeding max retry attempts

## 3. Network Communication Requirements

### 3.1 HTTP Transmission
- **REQ-9.1**: Send payloads via HTTPS POST requests
- **REQ-9.2**: Include authentication token in headers
- **REQ-9.3**: Handle HTTP response codes appropriately
- **REQ-9.4**: Configurable request timeout (default: 30 seconds)
- **REQ-9.5**: Retry failed transmissions with exponential backoff

### 3.2 Retry Logic
- **REQ-10.1**: Exponential backoff starting at 1 second
- **REQ-10.2**: Maximum backoff of 300 seconds (5 minutes)
- **REQ-10.3**: Backoff multiplier of 2
- **REQ-10.4**: Maximum 10 retry attempts per payload
- **REQ-10.5**: Queue payloads on transmission failure

### 3.3 Server Configuration Sync
- **REQ-11.1**: Poll server for configuration updates
- **REQ-11.2**: Check for updates every 60 seconds
- **REQ-11.3**: Apply configuration changes via hot-reload
- **REQ-11.4**: Watch .env file for external changes
- **REQ-11.5**: Merge server and local configuration

## 4. File Synchronization Requirements

### 4.1 OTA File Transfer
- **REQ-12.1**: Poll server for pending file downloads
- **REQ-12.2**: Download files to configurable directory
- **REQ-12.3**: Support parallel downloads (max 5 concurrent)
- **REQ-12.4**: Track download status (pending, downloading, completed, failed)
- **REQ-12.5**: Update server with download status

### 4.2 File Deletion Sync
- **REQ-13.1**: Detect files deleted on server
- **REQ-13.2**: Remove corresponding local files
- **REQ-13.3**: Maintain file ID to filename mapping
- **REQ-13.4**: Handle orphaned files (exist locally but not on server)

## 5. Logging and Monitoring Requirements

### 5.1 Logging
- **REQ-14.1**: Daily rotating log files with timestamps
- **REQ-14.2**: UTF-8 encoding for emoji and Unicode support
- **REQ-14.3**: Configurable log levels (DEBUG, INFO, WARN, ERROR)
- **REQ-14.4**: Real-time log flushing for immediate visibility
- **REQ-14.5**: Log rotation at 10MB with 5 backup files

### 5.2 Error Handling
- **REQ-15.1**: Graceful error handling without crashes
- **REQ-15.2**: Continue operation on non-critical errors
- **REQ-15.3**: Log detailed error information with context
- **REQ-15.4**: Retry transient errors automatically
- **REQ-15.5**: Report persistent errors to server

## 6. Performance Requirements

### 6.1 Resource Usage
- **REQ-16.1**: Minimal CPU usage during idle periods
- **REQ-16.2**: Efficient memory management with bounded buffers
- **REQ-16.3**: Configurable polling intervals to balance accuracy and performance
- **REQ-16.4**: Async I/O for network operations
- **REQ-16.5**: Lazy loading of browser data

### 6.2 Timing
- **REQ-17.1**: Application usage polling every 10 seconds (configurable)
- **REQ-17.2**: Data transmission every 10 minutes (configurable)
- **REQ-17.3**: Screenshot capture every 10 minutes (configurable)
- **REQ-17.4**: Location update every 30 minutes (configurable)
- **REQ-17.5**: Configuration check every 60 seconds

## 7. Security Requirements

### 7.1 Data Protection
- **REQ-18.1**: Use HTTPS for all server communication
- **REQ-18.2**: Secure storage of authentication tokens
- **REQ-18.3**: No plaintext passwords in configuration
- **REQ-18.4**: Validate server certificates
- **REQ-18.5**: Sanitize sensitive data in logs

### 7.2 Client Identification
- **REQ-19.1**: Generate unique client ID on first run
- **REQ-19.2**: Persist client ID across restarts
- **REQ-19.3**: Use UUID v4 for client ID generation
- **REQ-19.4**: Store client ID in platform-specific config directory

## 8. Platform-Specific Requirements

### 8.1 Windows
- **REQ-20.1**: Use Win32 API for foreground window detection
- **REQ-20.2**: Support Windows service deployment
- **REQ-20.3**: Handle Windows-specific process names
- **REQ-20.4**: Use Windows UI Automation for browser tabs
- **REQ-20.5**: Store config in %APPDATA%\VibgyorSeek

### 8.2 Linux (Secondary)
- **REQ-21.1**: Use X11/Wayland for window detection
- **REQ-21.2**: Support systemd service deployment
- **REQ-21.3**: Handle Linux-specific process names
- **REQ-21.4**: Store config in ~/.config/VibgyorSeek

### 8.3 macOS (Secondary)
- **REQ-22.1**: Use AppKit for window detection
- **REQ-22.2**: Support launchd service deployment
- **REQ-22.3**: Handle macOS-specific process names
- **REQ-22.4**: Store config in ~/Library/Application Support/VibgyorSeek

## 9. Deployment Requirements

### 9.1 Packaging
- **REQ-23.1**: Single executable binary
- **REQ-23.2**: Minimal external dependencies
- **REQ-23.3**: Embedded default configuration
- **REQ-23.4**: Version information in binary
- **REQ-23.5**: Cross-compilation support

### 9.2 Installation
- **REQ-24.1**: Command-line interface for setup
- **REQ-24.2**: Service installation scripts
- **REQ-24.3**: Configuration wizard for first run
- **REQ-24.4**: Uninstall cleanup scripts
- **REQ-24.5**: Update mechanism

## 10. Testing Requirements

### 10.1 Unit Tests
- **REQ-25.1**: Test coverage for all core modules
- **REQ-25.2**: Mock external dependencies
- **REQ-25.3**: Property-based testing for state machines
- **REQ-25.4**: Test error handling paths
- **REQ-25.5**: Test configuration validation

### 10.2 Integration Tests
- **REQ-26.1**: Test end-to-end data flow
- **REQ-26.2**: Test server communication
- **REQ-26.3**: Test queue persistence
- **REQ-26.4**: Test hot-reload functionality
- **REQ-26.5**: Test file synchronization

## 11. Documentation Requirements

### 11.1 Code Documentation
- **REQ-27.1**: Rustdoc comments for all public APIs
- **REQ-27.2**: Module-level documentation
- **REQ-27.3**: Example usage in documentation
- **REQ-27.4**: Architecture decision records
- **REQ-27.5**: Inline comments for complex logic

### 11.2 User Documentation
- **REQ-28.1**: Installation guide
- **REQ-28.2**: Configuration reference
- **REQ-28.3**: Troubleshooting guide
- **REQ-28.4**: Service deployment guide
- **REQ-28.5**: FAQ document

## Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| SERVER_URL | String | Required | Server endpoint URL |
| AUTH_TOKEN | String | Required | Authentication token |
| SCREENSHOT_INTERVAL_MINUTES | u32 | 10 | Screenshot capture interval |
| DATA_SEND_INTERVAL_MINUTES | u32 | 10 | Data transmission interval |
| LOCATION_UPDATE_INTERVAL_MINUTES | u32 | 30 | Location update interval |
| IDLE_THRESHOLD_SECONDS | u32 | 300 | Idle timeout threshold |
| SCREENSHOT_QUALITY | u8 | 75 | JPEG quality (1-100) |
| LOG_LEVEL | String | INFO | Logging level |
| APP_USAGE_POLL_INTERVAL_SECONDS | f64 | 10.0 | App polling interval |
| FILE_DOWNLOAD_PATH | String | C:\Downloads\CompanyFiles | File download directory |
| FILE_SYNC_INTERVAL | u32 | 30 | File sync check interval |

## Success Criteria

1. **Functional Parity**: All features from Python client implemented
2. **Performance**: Lower CPU and memory usage than Python version
3. **Reliability**: No crashes during 24-hour continuous operation
4. **Accuracy**: Data collection accuracy within 1% of Python version
5. **Maintainability**: Clean, idiomatic Rust code with >80% test coverage

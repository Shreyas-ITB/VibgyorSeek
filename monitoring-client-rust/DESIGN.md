# Monitoring Client - Rust Implementation Design

## Architecture Overview

The Rust monitoring client follows a modular, async-first architecture with clear separation of concerns. The design emphasizes type safety, performance, and maintainability while maintaining functional parity with the Python implementation.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Main Loop                            │
│  (Tokio Runtime - Async Coordination & Scheduling)          │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─────────────────────────────────────────────────┐
             │                                                 │
    ┌────────▼────────┐                              ┌────────▼────────┐
    │  Data Collection │                              │  Data Transmission│
    │     Modules      │                              │     Modules      │
    └────────┬────────┘                              └────────┬────────┘
             │                                                 │
    ┌────────┴────────────────────────────┐         ┌────────┴────────┐
    │                                     │         │                 │
┌───▼───────┐  ┌──────────┐  ┌─────────▼──┐   ┌───▼──────┐  ┌──────▼─────┐
│ Activity  │  │   App    │  │  Browser   │   │   HTTP   │  │   Queue    │
│ Tracker   │  │ Monitor  │  │  Monitor   │   │Transmitter│  │  Manager   │
└───────────┘  └──────────┘  └────────────┘   └──────────┘  └────────────┘
┌───────────┐  ┌──────────┐  ┌────────────┐   ┌──────────┐  ┌────────────┐
│Screenshot │  │ Location │  │    File    │   │  Retry   │  │   Config   │
│ Capture   │  │ Tracker  │  │    Sync    │   │ Manager  │  │  Watcher   │
└───────────┘  └──────────┘  └────────────┘   └──────────┘  └────────────┘
```

## Module Design

### 1. Core Modules

#### 1.1 Main Loop (`main.rs`)
**Purpose**: Application entry point and coordination

**Responsibilities**:
- Initialize Tokio async runtime
- Set up logging infrastructure
- Load configuration
- Spawn monitoring tasks
- Handle graceful shutdown (Ctrl+C)
- Coordinate interval-based operations

**Key Types**:
```rust
struct MonitoringClient {
    config: Arc<RwLock<Config>>,
    activity_tracker: Arc<ActivityTracker>,
    app_monitor: Arc<AppMonitor>,
    browser_monitor: Arc<BrowserMonitor>,
    screenshot_capture: Arc<ScreenshotCapture>,
    location_tracker: Arc<LocationTracker>,
    file_sync_manager: Arc<FileSyncManager>,
    http_transmitter: Arc<HttpTransmitter>,
    queue_manager: Arc<QueueManager>,
    retry_manager: Arc<RetryManager>,
    shutdown_tx: broadcast::Sender<()>,
}
```

**Async Tasks**:
- Activity tracking loop
- Application usage polling loop
- Screenshot capture timer
- Data transmission timer
- Location update timer
- Configuration watcher
- File sync manager
- Queue processor

#### 1.2 Configuration (`config.rs`)
**Purpose**: Configuration management with hot-reload support

**Responsibilities**:
- Load configuration from .env file
- Provide type-safe configuration access
- Watch for configuration changes
- Validate configuration values
- Manage client ID persistence

**Key Types**:
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
struct Config {
    server_url: String,
    auth_token: String,
    screenshot_interval_minutes: u32,
    data_send_interval_minutes: u32,
    location_update_interval_minutes: u32,
    idle_threshold_seconds: u32,
    screenshot_quality: u8,
    log_level: String,
    app_usage_poll_interval_seconds: f64,
    file_download_path: PathBuf,
    file_sync_interval: u32,
}

struct ConfigWatcher {
    config: Arc<RwLock<Config>>,
    watcher: RecommendedWatcher,
    reload_tx: broadcast::Sender<Config>,
}
```

**Dependencies**:
- `dotenv` - Environment variable loading
- `serde` - Serialization/deserialization
- `notify` - File system watching

### 2. Data Collection Modules

#### 2.1 Activity Tracker (`activity_tracker.rs`)
**Purpose**: Monitor keyboard and mouse activity

**Responsibilities**:
- Listen for input events
- Maintain activity state (WORK/IDLE)
- Track cumulative work and idle time
- Thread-safe state access

**Key Types**:
```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ActivityState {
    Work,
    Idle,
}

struct ActivityTracker {
    state: Arc<RwLock<ActivityState>>,
    last_activity: Arc<RwLock<Instant>>,
    work_seconds: Arc<AtomicU64>,
    idle_seconds: Arc<AtomicU64>,
    idle_threshold: Duration,
    interval_start: Arc<RwLock<Instant>>,
}
```

**Dependencies**:
- `rdev` - Cross-platform input event listening
- `tokio` - Async runtime

**Platform-Specific**:
- Windows: Uses Windows hooks
- Linux: Uses X11/evdev
- macOS: Uses CGEvent

#### 2.2 Application Monitor (`app_monitor.rs`)
**Purpose**: Monitor running applications and foreground app

**Responsibilities**:
- Enumerate running processes
- Identify foreground application
- Filter system processes
- Track application usage time

**Key Types**:
```rust
struct AppMonitor {
    platform: Platform,
    system_processes: HashSet<String>,
}

#[derive(Debug, Clone)]
struct Application {
    name: String,
    pid: u32,
    is_foreground: bool,
}

struct AppUsageTracker {
    app_monitor: Arc<AppMonitor>,
    durations: Arc<RwLock<HashMap<String, Duration>>>,
    current_app: Arc<RwLock<Option<String>>>,
    last_check: Arc<RwLock<Instant>>,
}
```

**Dependencies**:
- `sysinfo` - Process enumeration
- Windows: `windows-rs` - Win32 API for foreground window
- Linux: `x11rb` - X11 window detection
- macOS: `cocoa` - AppKit for active application

#### 2.3 Browser Monitor (`browser_monitor.rs`)
**Purpose**: Monitor browser tabs across Chrome, Firefox, Edge

**Responsibilities**:
- Detect running browsers
- Extract tab information
- Parse browser-specific data formats
- Track tab usage time

**Key Types**:
```rust
#[derive(Debug, Clone)]
enum Browser {
    Chrome,
    Firefox,
    Edge,
}

#[derive(Debug, Clone)]
struct BrowserTab {
    browser: Browser,
    title: String,
    url: String,
    duration: Duration,
}

struct BrowserMonitor {
    platform: Platform,
}

struct BrowserTabUsageTracker {
    browser_monitor: Arc<BrowserMonitor>,
    tab_durations: Arc<RwLock<HashMap<String, Duration>>>,
    current_tabs: Arc<RwLock<Vec<BrowserTab>>>,
    last_update: Arc<RwLock<Instant>>,
}
```

**Dependencies**:
- `rusqlite` - SQLite database access (Chrome/Edge history)
- `serde_json` - JSON parsing (Firefox session)
- `lz4` - LZ4 decompression (Firefox)
- Windows: `windows-rs` - UI Automation for tab titles

#### 2.4 Screenshot Capture (`screenshot.rs`)
**Purpose**: Capture and compress desktop screenshots

**Responsibilities**:
- Capture full desktop (all monitors)
- Compress to JPEG format
- Base64 encode for transmission
- Configurable quality

**Key Types**:
```rust
struct ScreenshotCapture {
    jpeg_quality: u8,
}

struct Screenshot {
    data: Vec<u8>,
    width: u32,
    height: u32,
    timestamp: DateTime<Utc>,
}
```

**Dependencies**:
- `screenshots` - Cross-platform screenshot capture
- `image` - Image processing and JPEG compression
- `base64` - Base64 encoding

#### 2.5 Location Tracker (`location_tracker.rs`)
**Purpose**: IP-based geolocation

**Responsibilities**:
- Query geolocation API
- Cache location data
- Provide city, state, country

**Key Types**:
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
struct Location {
    city: String,
    state: String,
    country: String,
}

struct LocationTracker {
    cached_location: Arc<RwLock<Option<Location>>>,
    client: reqwest::Client,
}
```

**Dependencies**:
- `reqwest` - HTTP client
- `serde_json` - JSON parsing

### 3. Data Management Modules

#### 3.1 Payload Builder (`payload_builder.rs`)
**Purpose**: Aggregate data and construct JSON payloads

**Responsibilities**:
- Collect data from all monitors
- Build structured JSON payload
- Include timestamps and intervals
- Handle optional fields

**Key Types**:
```rust
#[derive(Debug, Serialize)]
struct Payload {
    client_id: String,
    employee_name: String,
    timestamp: DateTime<Utc>,
    interval_start: DateTime<Utc>,
    interval_end: DateTime<Utc>,
    activity: ActivityData,
    applications: Vec<ApplicationData>,
    browser_tabs: Vec<BrowserTabData>,
    screenshot: String,
    location: Option<Location>,
}

struct PayloadBuilder {
    activity_tracker: Arc<ActivityTracker>,
    app_usage_tracker: Arc<AppUsageTracker>,
    browser_tab_tracker: Arc<BrowserTabUsageTracker>,
    location_tracker: Arc<LocationTracker>,
    screenshot_data: Arc<RwLock<Option<String>>>,
    interval_start: Arc<RwLock<DateTime<Utc>>>,
}
```

**Dependencies**:
- `serde` - Serialization
- `serde_json` - JSON formatting
- `chrono` - Date/time handling

#### 3.2 Queue Manager (`queue_manager.rs`)
**Purpose**: Persist failed payloads to SQLite

**Responsibilities**:
- Store payloads in SQLite database
- FIFO queue operations
- Track retry counts
- Enforce queue size limits

**Key Types**:
```rust
struct QueueManager {
    db_path: PathBuf,
    max_queue_size: usize,
}

#[derive(Debug)]
struct QueuedPayload {
    id: i64,
    payload_json: String,
    timestamp: DateTime<Utc>,
    retry_count: u32,
    created_at: DateTime<Utc>,
}
```

**Dependencies**:
- `rusqlite` - SQLite database
- `serde_json` - JSON serialization

**Database Schema**:
```sql
CREATE TABLE payload_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payload_json TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    retry_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_timestamp ON payload_queue(timestamp);
```

### 4. Network Communication Modules

#### 4.1 HTTP Transmitter (`http_transmitter.rs`)
**Purpose**: Send payloads to server via HTTPS

**Responsibilities**:
- POST payloads to server
- Handle authentication
- Process HTTP responses
- Timeout management

**Key Types**:
```rust
struct HttpTransmitter {
    server_url: String,
    auth_token: String,
    client: reqwest::Client,
    timeout: Duration,
}

#[derive(Debug)]
enum TransmissionError {
    Network(reqwest::Error),
    Authentication,
    ServerError(u16, String),
    Timeout,
}
```

**Dependencies**:
- `reqwest` - HTTP client with TLS support
- `tokio` - Async runtime

#### 4.2 Retry Manager (`retry_manager.rs`)
**Purpose**: Implement retry logic with exponential backoff

**Responsibilities**:
- Queue failed transmissions
- Exponential backoff calculation
- Process queued payloads
- Track retry attempts

**Key Types**:
```rust
struct RetryManager {
    queue_manager: Arc<QueueManager>,
    http_transmitter: Arc<HttpTransmitter>,
    initial_backoff: Duration,
    max_backoff: Duration,
    backoff_multiplier: u32,
    max_retry_attempts: u32,
}

struct BackoffState {
    current_backoff: Duration,
    last_retry_time: Instant,
}
```

**Dependencies**:
- `tokio::time` - Async delays

### 5. File Synchronization Module

#### 5.1 File Sync Manager (`file_sync_manager.rs`)
**Purpose**: OTA file transfer from server

**Responsibilities**:
- Poll server for pending files
- Download files in parallel
- Track download status
- Sync file deletions
- Update server with status

**Key Types**:
```rust
struct FileSyncManager {
    config: Arc<RwLock<Config>>,
    employee_name: String,
    client_id: String,
    download_path: PathBuf,
    max_parallel: usize,
    downloaded_files: Arc<RwLock<HashSet<String>>>,
    file_id_to_name: Arc<RwLock<HashMap<String, String>>>,
    client: reqwest::Client,
}

#[derive(Debug, Serialize, Deserialize)]
struct FileInfo {
    id: String,
    filename: String,
    file_size: u64,
}

#[derive(Debug, Serialize, Deserialize)]
enum DownloadStatus {
    Pending,
    Downloading,
    Completed,
    Failed,
}
```

**Dependencies**:
- `reqwest` - HTTP client for downloads
- `tokio::fs` - Async file I/O
- `futures` - Stream processing for parallel downloads

### 6. Logging Module

#### 6.1 Logger (`logger.rs`)
**Purpose**: Structured logging with rotation

**Responsibilities**:
- Daily rotating log files
- UTF-8 encoding support
- Configurable log levels
- Real-time flushing
- Size-based rotation

**Key Types**:
```rust
struct LogConfig {
    log_dir: PathBuf,
    log_level: LevelFilter,
    max_file_size: u64,
    max_backups: usize,
}
```

**Dependencies**:
- `tracing` - Structured logging framework
- `tracing-subscriber` - Log formatting and filtering
- `tracing-appender` - File rotation

## Data Flow

### 1. Monitoring Loop Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Start Interval                                            │
│    - Reset counters                                          │
│    - Record start time                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 2. Continuous Monitoring (Async Tasks)                      │
│    - Activity Tracker: Listen for input events              │
│    - App Usage Tracker: Poll every 10s                      │
│    - Browser Tab Tracker: Update with app tracker           │
│    - File Sync: Check on app tracker poll                   │
│    - Config Watcher: Check every 60s                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 3. Interval Events (Timer-based)                            │
│    - Screenshot: Every 10 min (configurable)                │
│    - Location: Every 30 min (configurable)                  │
│    - Data Send: Every 10 min (configurable)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 4. Data Transmission                                         │
│    - Build payload from all sources                          │
│    - Attempt HTTP POST to server                            │
│    - On success: Reset interval                             │
│    - On failure: Queue for retry                            │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 5. Queue Processing                                          │
│    - Check queue size                                        │
│    - Process queued payloads with backoff                   │
│    - Update retry counts                                     │
│    - Remove after max retries                               │
└─────────────────────────────────────────────────────────────┘
```

### 2. Configuration Hot-Reload Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Configuration Change Detected                            │
│    - File watcher detects .env change                       │
│    - OR server config version incremented                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 2. Load New Configuration                                    │
│    - Parse .env file                                         │
│    - Validate values                                         │
│    - Apply defaults for missing values                      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 3. Broadcast Configuration Update                           │
│    - Send new config via broadcast channel                  │
│    - All modules receive update notification                │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 4. Apply Configuration Changes                              │
│    - Update interval timers                                  │
│    - Update quality settings                                 │
│    - Update thresholds                                       │
│    - No restart required                                     │
└─────────────────────────────────────────────────────────────┘
```

## Concurrency Model

### Async Task Architecture

The application uses Tokio's async runtime with the following task structure:

1. **Main Task**: Coordinates all other tasks and handles shutdown
2. **Activity Tracker Task**: Runs input event listener
3. **App Usage Poller Task**: Polls foreground app every 10s
4. **Screenshot Timer Task**: Captures screenshots at intervals
5. **Data Transmission Timer Task**: Sends data at intervals
6. **Location Timer Task**: Updates location at intervals
7. **Config Watcher Task**: Monitors configuration changes
8. **File Sync Task**: Manages file downloads
9. **Queue Processor Task**: Processes failed payloads

### Synchronization Primitives

- **Arc<RwLock<T>>**: Shared state with read-write access
- **Arc<Mutex<T>>**: Exclusive access to mutable state
- **Arc<AtomicU64>**: Lock-free counters
- **broadcast::channel**: Configuration updates
- **mpsc::channel**: Task communication
- **oneshot::channel**: Single-value responses

## Error Handling Strategy

### Error Types

```rust
#[derive(Debug, thiserror::Error)]
enum MonitoringError {
    #[error("Configuration error: {0}")]
    Config(String),
    
    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),
    
    #[error("Database error: {0}")]
    Database(#[from] rusqlite::Error),
    
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    #[error("Platform error: {0}")]
    Platform(String),
}

type Result<T> = std::result::Result<T, MonitoringError>;
```

### Error Handling Principles

1. **Non-Fatal Errors**: Log and continue operation
2. **Fatal Errors**: Log, attempt cleanup, exit gracefully
3. **Transient Errors**: Retry with backoff
4. **User Errors**: Provide clear error messages
5. **System Errors**: Log detailed context for debugging

## Performance Optimizations

### 1. Memory Management
- Use `Arc` for shared ownership without cloning large data
- Use `Cow` for strings that may or may not need cloning
- Reuse buffers for screenshot compression
- Bounded channels to prevent unbounded memory growth

### 2. CPU Optimization
- Async I/O to avoid blocking threads
- Lazy evaluation for expensive operations
- Efficient polling intervals (10s default)
- Batch database operations

### 3. Network Optimization
- Connection pooling via `reqwest::Client`
- Compression for large payloads
- Parallel file downloads with semaphore limiting
- Keep-alive connections

## Testing Strategy

### Unit Tests
- Test each module in isolation
- Mock external dependencies
- Property-based testing for state machines
- Test error handling paths

### Integration Tests
- Test end-to-end data flow
- Test with real SQLite database
- Test configuration hot-reload
- Test queue persistence across restarts

### Platform-Specific Tests
- Conditional compilation for platform tests
- Test Windows-specific APIs
- Test Linux-specific APIs
- Test macOS-specific APIs

## Build and Deployment

### Cargo Configuration

```toml
[package]
name = "monitoring-client"
version = "1.0.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
reqwest = { version = "0.11", features = ["json", "rustls-tls"] }
rusqlite = { version = "0.30", features = ["bundled"] }
tracing = "0.1"
tracing-subscriber = "0.3"
dotenv = "0.15"
chrono = { version = "0.4", features = ["serde"] }
uuid = { version = "1", features = ["v4", "serde"] }
base64 = "0.21"
image = "0.24"
screenshots = "0.7"
rdev = "0.5"
sysinfo = "0.30"
notify = "6"
lz4 = "1"
thiserror = "1"
anyhow = "1"

[target.'cfg(windows)'.dependencies]
windows = { version = "0.52", features = ["Win32_UI_WindowsAndMessaging", "Win32_Foundation"] }

[target.'cfg(target_os = "linux")'.dependencies]
x11rb = "0.12"

[target.'cfg(target_os = "macos")'.dependencies]
cocoa = "0.25"

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true
```

### Cross-Compilation
- Use `cross` for building Windows binaries on Linux
- Use GitHub Actions for multi-platform builds
- Produce static binaries where possible

## Security Considerations

1. **TLS/SSL**: Use `rustls` for secure HTTPS communication
2. **Token Storage**: Store auth tokens securely in platform keychain (future enhancement)
3. **Input Validation**: Validate all configuration inputs
4. **SQL Injection**: Use parameterized queries with rusqlite
5. **Path Traversal**: Validate file paths for downloads
6. **Logging**: Sanitize sensitive data before logging

## Migration from Python

### Compatibility
- Maintain same JSON payload structure
- Use same SQLite schema for queue
- Use same configuration file format
- Use same server API endpoints

### Differences
- Rust uses async/await instead of threading
- Rust has stronger type safety
- Rust has better performance characteristics
- Rust requires explicit error handling

## Future Enhancements

1. **WebSocket Support**: Real-time communication with server
2. **Metrics Collection**: Prometheus-style metrics
3. **Plugin System**: Dynamic module loading
4. **GUI**: Optional system tray application
5. **Auto-Update**: Self-updating mechanism
6. **Encryption**: End-to-end encryption for sensitive data

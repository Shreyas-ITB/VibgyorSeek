//! VibgyorSeek Employee Monitoring Client - Rust Implementation
//!
//! This is the main entry point for the monitoring client application.
//! The client monitors user activity, captures screenshots, tracks application usage,
//! and transmits data to a central server.
//!
//! # Architecture
//!
//! The application uses Tokio's async runtime to coordinate multiple concurrent tasks:
//! - Activity tracking (input event monitoring)
//! - Application usage polling
//! - Screenshot capture (interval-based)
//! - Data transmission (interval-based)
//! - Location updates (interval-based)
//! - Configuration watching
//! - File synchronization
//! - Queue processing
//!
//! All tasks communicate via shared state protected by Arc<RwLock<T>>.

// Hide console window on Windows
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod modules;

use modules::activity_tracker::ActivityTracker;
use modules::app_monitor::{AppMonitor, AppUsageTracker};
use modules::browser_monitor::BrowserTabUsageTracker;
use modules::config::{Config, retrieve_client_id};
use modules::config_watcher::ConfigWatcher;
use modules::error::{MonitoringError, Result};
use modules::file_sync_manager::FileSyncManager;
use modules::http_transmitter::HttpTransmitter;
use modules::location_tracker::LocationTracker;
use modules::logger;
use modules::payload_builder::PayloadBuilder;
use modules::queue_manager::QueueManager;
use modules::retry_manager::RetryManager;
use modules::screenshot::ScreenshotCapture;
use parking_lot::RwLock;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::signal;
use tokio::sync::broadcast;
use tokio::time::{interval, sleep};
use tracing::{debug, error, info, warn};

/// Main monitoring client that coordinates all monitoring modules
struct MonitoringClient {
    /// Shared configuration
    config: Arc<RwLock<Config>>,
    
    /// Client ID (UUID)
    client_id: String,
    
    /// Shutdown signal broadcaster
    shutdown_tx: broadcast::Sender<()>,
    
    /// Running flag
    running: Arc<RwLock<bool>>,
    
    /// Activity tracker
    activity_tracker: Arc<ActivityTracker>,
    
    /// Application monitor
    app_monitor: Arc<AppMonitor>,
    
    /// Browser monitor
    browser_monitor: Arc<modules::browser_monitor::BrowserMonitor>,
    
    /// Application usage tracker
    app_usage_tracker: Arc<AppUsageTracker>,
    
    /// Browser tab usage tracker
    browser_tab_tracker: Arc<BrowserTabUsageTracker>,
    
    /// Screenshot capture
    screenshot_capture: Arc<ScreenshotCapture>,
    
    /// Location tracker
    location_tracker: Arc<LocationTracker>,
    
    /// Payload builder
    payload_builder: Arc<PayloadBuilder>,
    
    /// HTTP transmitter
    http_transmitter: Arc<HttpTransmitter>,
    
    /// Queue manager
    queue_manager: Arc<QueueManager>,
    
    /// Retry manager
    retry_manager: Arc<RetryManager>,
    
    /// File sync manager
    file_sync_manager: Arc<FileSyncManager>,
    
    /// Configuration watcher
    config_watcher: Arc<ConfigWatcher>,
    
    /// Last data send time
    last_data_send: Arc<RwLock<Instant>>,
    
    /// Last screenshot time
    last_screenshot: Arc<RwLock<Instant>>,
    
    /// Last location update time
    last_location_update: Arc<RwLock<Instant>>,
}

impl MonitoringClient {
    /// Create a new monitoring client
    ///
    /// # Arguments
    /// * `config` - Configuration instance
    /// * `client_id` - Unique client identifier
    ///
    /// # Returns
    /// A new MonitoringClient instance
    fn new(config: Arc<RwLock<Config>>, client_id: String) -> Result<Self> {
        let (shutdown_tx, _) = broadcast::channel(16);
        
        info!("🔧 Initializing monitoring modules...");
        
        // Initialize activity tracker
        let idle_threshold = config.read().idle_threshold_seconds;
        let activity_tracker = Arc::new(ActivityTracker::new(idle_threshold)?);
        info!("✅ Activity tracker initialized");
        
        // Initialize application monitor
        let app_monitor = Arc::new(AppMonitor::new());
        info!("✅ Application monitor initialized");
        
        // Initialize browser monitor
        let browser_monitor = Arc::new(modules::browser_monitor::BrowserMonitor::new());
        info!("✅ Browser monitor initialized");
        
        // Initialize application usage tracker
        let poll_interval = config.read().app_usage_poll_interval_seconds;
        let app_usage_tracker = Arc::new(AppUsageTracker::new(
            Arc::clone(&app_monitor),
            poll_interval,
        ));
        info!("✅ Application usage tracker initialized");
        
        // Initialize browser tab usage tracker
        let browser_tab_tracker = Arc::new(BrowserTabUsageTracker::new(Arc::clone(&browser_monitor)));
        info!("✅ Browser tab usage tracker initialized");
        
        // Initialize screenshot capture
        let screenshot_quality = config.read().screenshot_quality;
        let screenshot_capture = Arc::new(ScreenshotCapture::new(Some(screenshot_quality)));
        info!("✅ Screenshot capture initialized");
        
        // Initialize location tracker
        let location_tracker = Arc::new(LocationTracker::new());
        info!("✅ Location tracker initialized");
        
        // Initialize payload builder
        let payload_builder = Arc::new(PayloadBuilder::new(
            Arc::clone(&activity_tracker),
            Arc::clone(&app_usage_tracker),
            Some(Arc::clone(&browser_tab_tracker)),
            Some(Arc::clone(&location_tracker)),
        ));
        info!("✅ Payload builder initialized");
        
        // Initialize HTTP transmitter
        let (server_url, auth_token) = {
            let cfg = config.read();
            (cfg.server_url.clone(), cfg.auth_token.clone())
        };
        let http_transmitter = Arc::new(HttpTransmitter::new(
            server_url,
            auth_token,
            None, // Use default 30s timeout
        )?);
        info!("✅ HTTP transmitter initialized");
        
        // Initialize queue manager
        let queue_manager = Arc::new(QueueManager::new(None::<PathBuf>)?);
        info!("✅ Queue manager initialized");
        
        // Initialize retry manager
        let retry_manager = Arc::new(RetryManager::new(
            Arc::clone(&queue_manager),
            Arc::clone(&http_transmitter),
        ));
        info!("✅ Retry manager initialized");
        
        // Initialize file sync manager
        let file_sync_manager = Arc::new(FileSyncManager::new(
            Arc::clone(&config),
            client_id.clone(),
            client_id.clone(),
        )?);
        info!("✅ File sync manager initialized");
        
        // Initialize configuration watcher
        let config_watcher = Arc::new(ConfigWatcher::new(Arc::clone(&config), None)?);
        info!("✅ Configuration watcher initialized");
        
        info!("✅ All monitoring modules initialized successfully");
        
        Ok(Self {
            config,
            client_id,
            shutdown_tx,
            running: Arc::new(RwLock::new(false)),
            activity_tracker,
            app_monitor,
            browser_monitor,
            app_usage_tracker,
            browser_tab_tracker,
            screenshot_capture,
            location_tracker,
            payload_builder,
            http_transmitter,
            queue_manager,
            retry_manager,
            file_sync_manager,
            config_watcher,
            last_data_send: Arc::new(RwLock::new(Instant::now())),
            last_screenshot: Arc::new(RwLock::new(Instant::now())),
            last_location_update: Arc::new(RwLock::new(Instant::now())),
        })
    }
    
    /// Start the monitoring client
    ///
    /// Spawns all monitoring tasks and begins data collection
    async fn start(&self) -> Result<()> {
        *self.running.write() = true;
        
        info!("🚀 Starting monitoring client...");
        info!("🆔 Client ID: {}", self.client_id);
        
        // Display configuration
        {
            let cfg = self.config.read();
            info!("");
            info!("📊 Monitoring Configuration:");
            info!("  ├─ Data Send Interval:     {} minutes", cfg.data_send_interval_minutes);
            info!("  ├─ Screenshot Interval:    {} minutes", cfg.screenshot_interval_minutes);
            info!("  ├─ Location Update:        {} minutes", cfg.location_update_interval_minutes);
            info!("  ├─ Idle Threshold:         {} seconds", cfg.idle_threshold_seconds);
            info!("  ├─ Screenshot Quality:     {}%", cfg.screenshot_quality);
            info!("  └─ App Poll Interval:      {} seconds", cfg.app_usage_poll_interval_seconds);
            info!("");
        }
        
        // Start activity tracker
        self.activity_tracker.start()?;
        info!("✅ Activity tracker started");
        
        // Start application usage tracker
        self.app_usage_tracker.start()?;
        info!("✅ Application usage tracker started");
        
        // Start file sync manager
        self.file_sync_manager.start().await?;
        info!("✅ File sync manager started");
        
        // Start configuration watcher
        let config_watcher = Arc::clone(&self.config_watcher);
        let config_watcher_clone = Arc::clone(&config_watcher);
        tokio::spawn(async move {
            if let Err(e) = config_watcher_clone.start().await {
                error!("Configuration watcher error: {}", e);
            }
        });
        info!("✅ Configuration watcher started");
        
        // Subscribe to config updates and log changes
        let mut config_rx = config_watcher.subscribe();
        let config_ref = Arc::clone(&self.config);
        tokio::spawn(async move {
            while let Ok(new_config) = config_rx.recv().await {
                info!("🔄 Configuration update received!");
                info!("  ├─ Data Send Interval:     {} minutes", new_config.data_send_interval_minutes);
                info!("  ├─ Screenshot Interval:    {} minutes", new_config.screenshot_interval_minutes);
                info!("  ├─ Location Update:        {} minutes", new_config.location_update_interval_minutes);
                info!("  ├─ Idle Threshold:         {} seconds", new_config.idle_threshold_seconds);
                info!("  ├─ Screenshot Quality:     {}%", new_config.screenshot_quality);
                info!("  └─ App Poll Interval:      {} seconds", new_config.app_usage_poll_interval_seconds);
                
                // Force update the shared config
                *config_ref.write() = new_config;
                info!("✅ Configuration applied - intervals will update on next tick");
            }
        });
        
        // Get initial location
        info!("🌍 Getting initial location...");
        match self.location_tracker.get_location().await {
            Ok(Some(location)) => {
                info!("✅ Initial location: {}, {}, {}", location.city, location.state, location.country);
            }
            Ok(None) => {
                warn!("⚠️ Failed to get initial location");
            }
            Err(e) => {
                warn!("⚠️ Error getting initial location: {}", e);
            }
        }
        
        // Start interval for payload builder
        self.payload_builder.start_interval();
        
        // Spawn monitoring tasks
        self.spawn_monitoring_tasks().await?;
        
        info!("✅ All monitoring tasks started successfully");
        
        Ok(())
    }
    
    /// Spawn all monitoring tasks
    async fn spawn_monitoring_tasks(&self) -> Result<()> {
        // Task 1: Screenshot capture timer
        {
            let config = Arc::clone(&self.config);
            let screenshot_capture = Arc::clone(&self.screenshot_capture);
            let payload_builder = Arc::clone(&self.payload_builder);
            let last_screenshot = Arc::clone(&self.last_screenshot);
            let mut shutdown_rx = self.shutdown_tx.subscribe();
            
            tokio::spawn(async move {
                info!("📸 Screenshot capture task started");
                
                let mut current_interval = {
                    let cfg = config.read();
                    Duration::from_secs(cfg.screenshot_interval_minutes as u64 * 60)
                };
                let mut ticker = interval(current_interval);
                ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                info!("📸 Screenshot interval: {:?}", current_interval);
                
                loop {
                    tokio::select! {
                        _ = shutdown_rx.recv() => {
                            info!("🛑 Screenshot capture shutting down");
                            break;
                        }
                        _ = ticker.tick() => {
                            // Check if interval changed
                            let new_interval = {
                                let cfg = config.read();
                                Duration::from_secs(cfg.screenshot_interval_minutes as u64 * 60)
                            };
                            
                            if new_interval != current_interval {
                                info!("🔄 Screenshot interval changed: {:?} -> {:?}", current_interval, new_interval);
                                current_interval = new_interval;
                                ticker = interval(current_interval);
                                ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                                continue; // Skip this tick and start with new interval
                            }
                            
                            info!("📸 Capturing screenshot...");
                            match screenshot_capture.capture_screenshot() {
                                Ok(screenshot_data) => {
                                    payload_builder.set_screenshot(screenshot_data);
                                    *last_screenshot.write() = Instant::now();
                                    info!("✅ Screenshot captured and stored");
                                }
                                Err(e) => {
                                    error!("❌ Screenshot capture failed: {}", e);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Task 2: Data transmission timer
        {
            let config = Arc::clone(&self.config);
            let payload_builder = Arc::clone(&self.payload_builder);
            let http_transmitter = Arc::clone(&self.http_transmitter);
            let queue_manager = Arc::clone(&self.queue_manager);
            let activity_tracker = Arc::clone(&self.activity_tracker);
            let app_usage_tracker = Arc::clone(&self.app_usage_tracker);
            let browser_tab_tracker = Arc::clone(&self.browser_tab_tracker);
            let client_id = self.client_id.clone();
            let last_data_send = Arc::clone(&self.last_data_send);
            let mut shutdown_rx = self.shutdown_tx.subscribe();
            
            tokio::spawn(async move {
                info!("📤 Data transmission task started");
                
                let mut current_interval = {
                    let cfg = config.read();
                    Duration::from_secs(cfg.data_send_interval_minutes as u64 * 60)
                };
                let mut ticker = interval(current_interval);
                ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                info!("📤 Data send interval: {:?}", current_interval);
                
                loop {
                    tokio::select! {
                        _ = shutdown_rx.recv() => {
                            info!("🛑 Data transmission shutting down");
                            break;
                        }
                        _ = ticker.tick() => {
                            // Check if interval changed
                            let new_interval = {
                                let cfg = config.read();
                                Duration::from_secs(cfg.data_send_interval_minutes as u64 * 60)
                            };
                            
                            if new_interval != current_interval {
                                info!("🔄 Data send interval changed: {:?} -> {:?}", current_interval, new_interval);
                                current_interval = new_interval;
                                ticker = interval(current_interval);
                                ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                                continue; // Skip this tick and start with new interval
                            }
                            
                            info!("📤 Building and transmitting data payload...");
                            
                            // Build payload
                            match payload_builder.build_payload(&client_id, &client_id).await {
                                Ok(payload) => {
                                    // Serialize to JSON
                                    match serde_json::to_value(&payload) {
                                        Ok(json_payload) => {
                                            // Send payload
                                            match http_transmitter.send_payload(&json_payload).await {
                                                Ok(_) => {
                                                    info!("✅ Data transmitted successfully");
                                                }
                                                Err(e) => {
                                                    warn!("⚠️ Transmission failed: {}. Queuing for retry.", e);
                                                    
                                                    // Queue the payload using spawn_blocking
                                                    let queue_manager_clone = Arc::clone(&queue_manager);
                                                    let json_payload_clone = json_payload.clone();
                                                    tokio::task::spawn_blocking(move || {
                                                        if let Err(e) = queue_manager_clone.add(json_payload_clone) {
                                                            error!("❌ Failed to queue payload: {}", e);
                                                        } else {
                                                            info!("✅ Payload queued for retry");
                                                        }
                                                    }).await.ok();
                                                }
                                            }
                                        }
                                        Err(e) => {
                                            error!("❌ Failed to serialize payload: {}", e);
                                        }
                                    }
                                }
                                Err(e) => {
                                    error!("❌ Failed to build payload: {}", e);
                                }
                            }
                            
                            // Reset intervals
                            payload_builder.start_interval();
                            activity_tracker.reset_interval();
                            app_usage_tracker.reset_interval();
                            browser_tab_tracker.reset_interval();
                            
                            *last_data_send.write() = Instant::now();
                        }
                    }
                }
            });
        }
        
        // Task 2.5: Browser tab tracker update (polls every 10 seconds like app usage)
        {
            let browser_tab_tracker = Arc::clone(&self.browser_tab_tracker);
            let config = Arc::clone(&self.config);
            let mut shutdown_rx = self.shutdown_tx.subscribe();
            
            tokio::spawn(async move {
                let poll_interval = {
                    let cfg = config.read();
                    Duration::from_secs_f64(cfg.app_usage_poll_interval_seconds)
                };
                
                let mut ticker = interval(poll_interval);
                ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                info!("🌐 Browser tab tracker task started (interval: {:?})", poll_interval);
                
                loop {
                    tokio::select! {
                        _ = shutdown_rx.recv() => {
                            info!("🛑 Browser tab tracker shutting down");
                            break;
                        }
                        _ = ticker.tick() => {
                            debug!("🌐 Updating browser tab usage...");
                            if let Err(e) = browser_tab_tracker.update() {
                                error!("❌ Browser tab tracker error: {}", e);
                            }
                        }
                    }
                }
            });
        }
        
        // Task 3: Location update timer
        {
            let config = Arc::clone(&self.config);
            let location_tracker = Arc::clone(&self.location_tracker);
            let last_location_update = Arc::clone(&self.last_location_update);
            let mut shutdown_rx = self.shutdown_tx.subscribe();
            
            tokio::spawn(async move {
                info!("🌍 Location tracker task started");
                
                let mut current_interval = {
                    let cfg = config.read();
                    Duration::from_secs(cfg.location_update_interval_minutes as u64 * 60)
                };
                let mut ticker = interval(current_interval);
                ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                info!("🌍 Location update interval: {:?}", current_interval);
                
                loop {
                    tokio::select! {
                        _ = shutdown_rx.recv() => {
                            info!("🛑 Location tracker shutting down");
                            break;
                        }
                        _ = ticker.tick() => {
                            // Check if interval changed
                            let new_interval = {
                                let cfg = config.read();
                                Duration::from_secs(cfg.location_update_interval_minutes as u64 * 60)
                            };
                            
                            if new_interval != current_interval {
                                info!("🔄 Location update interval changed: {:?} -> {:?}", current_interval, new_interval);
                                current_interval = new_interval;
                                ticker = interval(current_interval);
                                ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                                continue; // Skip this tick and start with new interval
                            }
                            
                            info!("🌍 Updating location...");
                            match location_tracker.get_location().await {
                                Ok(Some(location)) => {
                                    info!("✅ Location updated: {}, {}, {}", 
                                          location.city, location.state, location.country);
                                    *last_location_update.write() = Instant::now();
                                }
                                Ok(None) => {
                                    warn!("⚠️ Location update returned None");
                                }
                                Err(e) => {
                                    error!("❌ Location update failed: {}", e);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Task 4: File sync manager
        {
            let file_sync_manager = Arc::clone(&self.file_sync_manager);
            let mut shutdown_rx = self.shutdown_tx.subscribe();
            
            tokio::spawn(async move {
                let check_interval = Duration::from_secs(30);
                let mut ticker = interval(check_interval);
                ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                info!("📁 File sync manager task started (interval: {:?})", check_interval);
                
                loop {
                    tokio::select! {
                        _ = shutdown_rx.recv() => {
                            info!("🛑 File sync manager shutting down");
                            break;
                        }
                        _ = ticker.tick() => {
                            debug!("📁 Checking for file updates...");
                            if let Err(e) = file_sync_manager.update().await {
                                error!("❌ File sync error: {}", e);
                            }
                        }
                    }
                }
            });
        }
        
        // Task 5: Queue processor
        {
            let queue_manager = Arc::clone(&self.queue_manager);
            let http_transmitter = Arc::clone(&self.http_transmitter);
            let mut shutdown_rx = self.shutdown_tx.subscribe();
            
            tokio::spawn(async move {
                let process_interval = Duration::from_secs(60);
                let mut ticker = interval(process_interval);
                ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                info!("🔄 Queue processor task started (interval: {:?})", process_interval);
                
                loop {
                    tokio::select! {
                        _ = shutdown_rx.recv() => {
                            info!("🛑 Queue processor shutting down");
                            break;
                        }
                        _ = ticker.tick() => {
                            // Check queue size using spawn_blocking
                            let queue_manager_clone = Arc::clone(&queue_manager);
                            let size_result = tokio::task::spawn_blocking(move || {
                                queue_manager_clone.size()
                            }).await;
                            
                            match size_result {
                                Ok(Ok(size)) if size > 0 => {
                                    info!("🔄 Processing {} queued payload(s)...", size);
                                    
                                    // Retrieve and process payloads
                                    let queue_manager_clone = Arc::clone(&queue_manager);
                                    let payloads_result = tokio::task::spawn_blocking(move || {
                                        queue_manager_clone.retrieve(10)
                                    }).await;
                                    
                                    if let Ok(Ok(payloads)) = payloads_result {
                                        let mut successful = 0;
                                        let mut failed = 0;
                                        
                                        for (payload_id, payload) in payloads {
                                            // Try to send payload
                                            match http_transmitter.send_payload(&payload).await {
                                                Ok(_) => {
                                                    info!("✅ Queued payload {} sent successfully", payload_id);
                                                    
                                                    // Delete from queue
                                                    let queue_manager_clone = Arc::clone(&queue_manager);
                                                    tokio::task::spawn_blocking(move || {
                                                        let _ = queue_manager_clone.delete(payload_id);
                                                    }).await.ok();
                                                    
                                                    successful += 1;
                                                }
                                                Err(e) => {
                                                    warn!("⚠️ Retry failed for payload {}: {}", payload_id, e);
                                                    
                                                    // Increment retry count
                                                    let queue_manager_clone = Arc::clone(&queue_manager);
                                                    tokio::task::spawn_blocking(move || {
                                                        let _ = queue_manager_clone.increment_retry_count(payload_id);
                                                    }).await.ok();
                                                    
                                                    failed += 1;
                                                    // Stop processing on first failure
                                                    break;
                                                }
                                            }
                                        }
                                        
                                        info!("✅ Queue processed: {} successful, {} failed", successful, failed);
                                    }
                                }
                                Ok(Ok(_)) => {
                                    debug!("Queue is empty");
                                }
                                Ok(Err(e)) => {
                                    error!("❌ Error checking queue size: {}", e);
                                }
                                Err(e) => {
                                    error!("❌ Task error: {}", e);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Task 6: Periodic config check (force check every 5 seconds)
        {
            let config_watcher = Arc::clone(&self.config_watcher);
            let mut shutdown_rx = self.shutdown_tx.subscribe();
            
            tokio::spawn(async move {
                let check_interval = Duration::from_secs(5);
                let mut ticker = interval(check_interval);
                ticker.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                info!("🔍 Config force-check task started (interval: {:?})", check_interval);
                
                loop {
                    tokio::select! {
                        _ = shutdown_rx.recv() => {
                            info!("🛑 Config force-check shutting down");
                            break;
                        }
                        _ = ticker.tick() => {
                            debug!("🔍 Force-checking configuration...");
                            if let Err(e) = config_watcher.check_once().await {
                                debug!("Config check error (non-critical): {}", e);
                            }
                        }
                    }
                }
            });
        }
        
        Ok(())
    }
    
    /// Stop the monitoring client
    ///
    /// Sends shutdown signal to all tasks and waits for graceful shutdown
    async fn stop(&self) -> Result<()> {
        info!("🛑 Stopping monitoring client...");
        
        *self.running.write() = false;
        
        // Stop all monitoring modules
        self.activity_tracker.stop();
        self.app_usage_tracker.stop();
        self.file_sync_manager.stop();
        
        // Send shutdown signal to all tasks
        if let Err(e) = self.shutdown_tx.send(()) {
            warn!("Failed to send shutdown signal: {}", e);
        }
        
        // Give tasks time to shut down gracefully
        sleep(Duration::from_secs(2)).await;
        
        info!("✅ Monitoring client stopped");
        
        Ok(())
    }
    
    /// Check if the client is running
    fn is_running(&self) -> bool {
        *self.running.read()
    }
    
    /// Get current status
    fn get_status(&self) -> String {
        let running = self.is_running();
        let cfg = self.config.read();
        
        format!(
            "Status: {} | Client ID: {} | Data Interval: {}min | Screenshot Interval: {}min",
            if running { "RUNNING" } else { "STOPPED" },
            self.client_id,
            cfg.data_send_interval_minutes,
            cfg.screenshot_interval_minutes
        )
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging with enhanced features
    let log_dir = PathBuf::from("logs");
    logger::init_logging(log_dir, "INFO")
        .map_err(|e| MonitoringError::Config(e.to_string()))?;

    // Display startup banner
    info!("╔════════════════════════════════════════════════════════════╗");
    info!("║  VibgyorSeek Employee Monitoring Client - Rust Edition    ║");
    info!("╚════════════════════════════════════════════════════════════╝");
    info!("");
    info!("📦 Version: {}", env!("CARGO_PKG_VERSION"));
    info!("💻 Platform: {}", std::env::consts::OS);
    info!("🏗️  Architecture: {}", std::env::consts::ARCH);
    info!("");

    // Load configuration
    info!("⚙️  Loading configuration...");
    let config = match Config::load(None) {
        Ok(cfg) => {
            info!("✅ Configuration loaded successfully");
            Arc::new(RwLock::new(cfg))
        }
        Err(e) => {
            error!("❌ Failed to load configuration: {}", e);
            return Err(e);
        }
    };

    // Get or generate client ID
    info!("🆔 Retrieving client ID...");
    let client_id = match retrieve_client_id() {
        Ok(id) => {
            info!("✅ Client ID: {}", id);
            id
        }
        Err(e) => {
            error!("❌ Failed to retrieve client ID: {}", e);
            return Err(e);
        }
    };

    // Create monitoring client
    let client = MonitoringClient::new(config, client_id)?;

    // Start monitoring
    if let Err(e) = client.start().await {
        error!("❌ Failed to start monitoring: {}", e);
        return Err(e);
    }

    info!("");
    info!("⌨️  Press Ctrl+C to stop monitoring");
    info!("");

    // Wait for Ctrl+C
    match signal::ctrl_c().await {
        Ok(()) => {
            info!("");
            info!("🛑 Received shutdown signal (Ctrl+C)");
        }
        Err(e) => {
            error!("❌ Error waiting for Ctrl+C: {}", e);
            return Err(MonitoringError::Io(e));
        }
    }

    // Stop monitoring
    if let Err(e) = client.stop().await {
        error!("❌ Error during shutdown: {}", e);
        return Err(e);
    }

    info!("");
    info!("👋 Goodbye!");
    Ok(())
}

// Module declarations for the monitoring client
// Each module will be implemented in separate files

// Core monitoring modules
pub mod activity_tracker;
pub mod app_monitor;
pub mod browser_monitor;
pub mod screenshot;
pub mod location_tracker;

// Data management modules
pub mod config;
pub mod payload_builder;
pub mod queue_manager;

// Network communication modules
pub mod http_transmitter;
pub mod retry_manager;
pub mod config_watcher;

// File synchronization
pub mod file_sync_manager;

// Logging
pub mod logger;

// Utilities
pub mod error;
pub mod types;

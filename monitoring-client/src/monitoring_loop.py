"""
Main Monitoring Loop Module

This module implements the main monitoring loop that coordinates all monitor modules,
collects data at configured intervals, and handles errors gracefully.

Requirements: 6.1, 6.2, 7.5
"""

import logging
import time
import threading
from typing import Optional
from datetime import datetime, timezone

from .config import Config, retrieve_client_id
from .activity_tracker import ActivityTracker
from .app_monitor import ApplicationMonitor
from .browser_monitor import BrowserMonitor
from .screenshot import ScreenshotCapture
from .payload_builder import PayloadBuilder
from .http_transmitter import HTTPTransmitter
from .queue_manager import QueueManager
from .retry_manager import RetryManager
from .app_usage_tracker import ApplicationUsageTracker
from .browser_tab_usage_tracker import BrowserTabUsageTracker
from .location_tracker import LocationTracker
from .file_sync_manager import FileSyncManager
from .config_watcher import ConfigWatcher
from .server_env_watcher import ServerEnvWatcher
from .logger import get_logger


logger = get_logger()


class MonitoringLoop:
    """
    Main monitoring loop that coordinates all monitoring modules.
    
    Runs continuously, collecting data at configured intervals and handling
    errors gracefully to ensure uninterrupted operation.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the monitoring loop with configuration.
        
        Args:
            config: Configuration instance. If None, creates a new Config.
        
        Requirements: 6.1, 8.1
        """
        self.config = config or Config()
        self._running = False
        self._stop_event = threading.Event()
        
        # Get client ID
        self.client_id = retrieve_client_id()
        if not self.client_id:
            raise RuntimeError(
                "Client ID not configured. This should not happen."
            )
        
        logger.info(f"Initializing monitoring loop for client: {self.client_id}")
        
        # Initialize all monitor modules
        try:
            self._initialize_modules()
            logger.info("All monitoring modules initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize monitoring modules: {e}", exc_info=True)
            raise
    
    def _initialize_modules(self) -> None:
        """Initialize all monitoring modules."""
        # Activity tracker
        self.activity_tracker = ActivityTracker(
            idle_threshold_seconds=self.config.idle_threshold_seconds
        )
        
        # Application monitor
        self.app_monitor = ApplicationMonitor()
        
        # Browser monitor
        self.browser_monitor = BrowserMonitor()
        
        # Browser tab usage tracker
        self.browser_tab_tracker = BrowserTabUsageTracker(
            browser_monitor=self.browser_monitor
        )
        
        # File sync manager (initialize before app usage tracker)
        self.file_sync_manager = FileSyncManager(
            config=self.config,
            employee_name=self.client_id  # Use client_id for file sync
        )
        
        # Server env watcher (checks server for config changes every 10s)
        self.server_env_watcher = ServerEnvWatcher(
            config=self.config
        )
        print(f"✅ SERVER ENV WATCHER: Created and ready")
        logger.info("Server env watcher created")
        
        # Configuration watcher (checks every 60 seconds)
        self.config_watcher = ConfigWatcher(
            config=self.config,
            check_interval_seconds=60,
            server_env_watcher=self.server_env_watcher
        )
        
        # Register hot-reload callback
        self.config_watcher.set_reload_callback(self._reload_configuration)
        
        # Register server env change callback
        self.server_env_watcher.set_on_change_callback(self.config_watcher.write_server_config_to_env)
        print(f"✅ SERVER ENV WATCHER: Callback registered to write config on changes")
        logger.info("Server env watcher callback registered")
        
        # Application usage tracker (with browser tab tracker, file sync manager, and server env watcher for concurrent updates)
        self.app_usage_tracker = ApplicationUsageTracker(
            app_monitor=self.app_monitor,
            poll_interval=self.config.app_usage_poll_interval_seconds,
            browser_tab_tracker=self.browser_tab_tracker,
            file_sync_manager=self.file_sync_manager,
            server_env_watcher=self.server_env_watcher
        )
        
        # Location tracker
        self.location_tracker = LocationTracker()
        
        # Screenshot capture
        self.screenshot_capture = ScreenshotCapture(
            jpeg_quality=self.config.screenshot_quality
        )
        
        # Payload builder
        self.payload_builder = PayloadBuilder(
            activity_tracker=self.activity_tracker,
            app_monitor=self.app_monitor,
            browser_monitor=self.browser_monitor,
            screenshot_capture=self.screenshot_capture,
            app_usage_tracker=self.app_usage_tracker,
            browser_tab_tracker=self.browser_tab_tracker,
            location_tracker=self.location_tracker
        )
        
        # HTTP transmitter
        self.http_transmitter = HTTPTransmitter(
            server_url=self.config.server_url,
            auth_token=self.config.auth_token
        )
        
        # Queue manager
        self.queue_manager = QueueManager()
        
        # Retry manager
        self.retry_manager = RetryManager(
            queue_manager=self.queue_manager,
            http_transmitter=self.http_transmitter
        )

    
    def _reload_configuration(self):
        """
        Hot-reload configuration without restarting the application.
        This is called when the .env file changes.
        """
        try:
            logger.info("🔄 Hot-reloading configuration...")
            
            # Reload the configuration
            old_config = self.config
            self.config = Config()
            
            # Recalculate interval seconds (these are used by _run_loop)
            self.data_interval_seconds = self.config.data_send_interval_minutes * 60
            self.screenshot_interval_seconds = self.config.screenshot_interval_minutes * 60
            self.location_interval_seconds = self.config.location_update_interval_minutes * 60
            
            # Log what changed
            if old_config.screenshot_interval_minutes != self.config.screenshot_interval_minutes:
                logger.info(f"📸 Screenshot interval: {old_config.screenshot_interval_minutes} → {self.config.screenshot_interval_minutes} min")
            
            if old_config.data_send_interval_minutes != self.config.data_send_interval_minutes:
                logger.info(f"📊 Data send interval: {old_config.data_send_interval_minutes} → {self.config.data_send_interval_minutes} min")
            
            if old_config.location_update_interval_minutes != self.config.location_update_interval_minutes:
                logger.info(f"🌍 Location update interval: {old_config.location_update_interval_minutes} → {self.config.location_update_interval_minutes} min")
            
            if old_config.idle_threshold_seconds != self.config.idle_threshold_seconds:
                logger.info(f"⏱️  Idle threshold: {old_config.idle_threshold_seconds} → {self.config.idle_threshold_seconds} sec")
            
            if old_config.screenshot_quality != self.config.screenshot_quality:
                logger.info(f"🎨 Screenshot quality: {old_config.screenshot_quality} → {self.config.screenshot_quality}%")
            
            if old_config.app_usage_poll_interval_seconds != self.config.app_usage_poll_interval_seconds:
                logger.info(f"🔄 App poll interval: {old_config.app_usage_poll_interval_seconds} → {self.config.app_usage_poll_interval_seconds} sec")
            
            # Update components that use configuration
            self.activity_tracker.idle_threshold_seconds = self.config.idle_threshold_seconds
            self.screenshot_capture.jpeg_quality = self.config.screenshot_quality
            self.app_usage_tracker.poll_interval = self.config.app_usage_poll_interval_seconds
            self.http_transmitter.server_url = self.config.server_url
            self.http_transmitter.auth_token = self.config.auth_token
            
            logger.info("✅ Configuration hot-reloaded successfully! No restart needed.")
            print("\n" + "="*60)
            print("✅ CONFIGURATION UPDATED - HOT-RELOADED")
            print("="*60)
            print(f"📸 Screenshot Interval:    {self.config.screenshot_interval_minutes} minutes")
            print(f"📊 Data Send Interval:     {self.config.data_send_interval_minutes} minutes")
            print(f"🌍 Location Update:        {self.config.location_update_interval_minutes} minutes")
            print(f"⏱️  Idle Threshold:         {self.config.idle_threshold_seconds} seconds")
            print(f"🎨 Screenshot Quality:     {self.config.screenshot_quality}%")
            print(f"🔄 App Poll Interval:      {self.config.app_usage_poll_interval_seconds} seconds")
            print("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"❌ Error during configuration hot-reload: {e}", exc_info=True)
            print(f"❌ Configuration reload failed: {e}")
    
    def start(self) -> None:
        """
        Start the monitoring loop.
        
        Begins continuous monitoring with interval-based data collection
        and transmission.
        
        Requirements: 6.1, 6.2, 7.5
        """
        if self._running:
            logger.warning("Monitoring loop is already running")
            return
        
        self._running = True
        self._stop_event.clear()
        
        logger.info(
            f"Starting monitoring loop - "
            f"Data interval: {self.config.data_send_interval_minutes} min, "
            f"Screenshot interval: {self.config.screenshot_interval_minutes} min, "
            f"Location interval: {self.config.location_update_interval_minutes} min, "
            f"Idle threshold: {self.config.idle_threshold_seconds} sec"
        )
        
        print(f"\n{'='*60}")
        print(f"🚀 Monitoring Configuration:")
        print(f"{'='*60}")
        print(f"📊 Data Send Interval:     {self.config.data_send_interval_minutes} minutes")
        print(f"📸 Screenshot Interval:    {self.config.screenshot_interval_minutes} minutes")
        print(f"🌍 Location Update:        {self.config.location_update_interval_minutes} minutes")
        print(f"⏱️  Idle Threshold:         {self.config.idle_threshold_seconds} seconds")
        print(f"{'='*60}\n")
        
        # Start activity tracker
        try:
            self.activity_tracker.start()
            logger.info("Activity tracker started")
        except Exception as e:
            logger.error(f"Failed to start activity tracker: {e}", exc_info=True)
            self._running = False
            raise
        
        # Start application usage tracker
        try:
            self.app_usage_tracker.start()
            print(f"✅ Application usage tracker started - will poll every {self.config.app_usage_poll_interval_seconds} seconds")
            logger.info(f"Application usage tracker started with poll interval: {self.config.app_usage_poll_interval_seconds}s")
        except Exception as e:
            logger.error(f"Failed to start application usage tracker: {e}", exc_info=True)
            self.activity_tracker.stop()
            self._running = False
            raise
        
        # Start file sync manager
        try:
            self.file_sync_manager.start()
            print(f"✅ File sync manager started - checks on every app usage poll (every {self.config.app_usage_poll_interval_seconds}s)")
            logger.info(f"File sync manager started - integrated with app usage tracker polling")
        except Exception as e:
            logger.error(f"Failed to start file sync manager: {e}", exc_info=True)
            # Don't fail the entire loop if file sync fails
            logger.warning("Continuing without file sync functionality")
            print(f"⚠️  File sync manager failed to start: {e}")
        
        # Start configuration watcher
        try:
            self.config_watcher.start()
            print(f"✅ Configuration watcher started - checks every 60 seconds")
            logger.info("Configuration watcher started")
        except Exception as e:
            logger.error(f"Failed to start config watcher: {e}", exc_info=True)
            logger.warning("Continuing without config auto-update")
            print(f"⚠️  Config watcher failed to start: {e}")
        
        # Start the main monitoring loop in a separate thread
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()
        
        logger.info("Monitoring loop started successfully")
    
    def stop(self) -> None:
        """
        Stop the monitoring loop.
        
        Gracefully shuts down all monitoring modules.
        """
        if not self._running:
            logger.warning("Monitoring loop is not running")
            return
        
        logger.info("Stopping monitoring loop...")
        
        self._running = False
        self._stop_event.set()
        
        # Stop activity tracker
        try:
            self.activity_tracker.stop()
            logger.info("Activity tracker stopped")
        except Exception as e:
            logger.error(f"Error stopping activity tracker: {e}", exc_info=True)
        
        # Stop application usage tracker
        try:
            self.app_usage_tracker.stop()
            logger.info("Application usage tracker stopped")
        except Exception as e:
            logger.error(f"Error stopping application usage tracker: {e}", exc_info=True)
        
        # Stop file sync manager
        try:
            self.file_sync_manager.stop()
            logger.info("File sync manager stopped")
        except Exception as e:
            logger.error(f"Error stopping file sync manager: {e}", exc_info=True)
        
        # Wait for loop thread to finish
        if hasattr(self, '_loop_thread') and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5)
        
        logger.info("Monitoring loop stopped")
    
    def _run_loop(self) -> None:
        """
        Main monitoring loop that runs continuously.
        
        Collects data at configured intervals and handles errors gracefully.
        
        Requirements: 6.1, 6.2, 7.5
        """
        # Convert intervals from minutes to seconds (stored as instance variables for hot-reload)
        self.data_interval_seconds = self.config.data_send_interval_minutes * 60
        self.screenshot_interval_seconds = self.config.screenshot_interval_minutes * 60
        self.location_interval_seconds = self.config.location_update_interval_minutes * 60
        
        last_data_send_time = time.time()
        last_screenshot_time = time.time()
        last_location_update_time = time.time()
        last_config_check_time = time.time()
        config_check_interval = 60  # Check every 60 seconds
        
        # Start the first interval
        self.payload_builder.start_interval()
        
        # Get initial location
        logger.info("🌍 Getting initial location...")
        print("🌍 Getting initial location...")
        initial_location = self.location_tracker.get_location()
        if initial_location:
            logger.info(f"✅ Initial location obtained: {initial_location}")
            print(f"✅ Initial location: {initial_location['city']}, {initial_location['state']}, {initial_location['country']}")
        else:
            logger.warning("⚠️ Failed to get initial location")
            print("⚠️ Failed to get initial location")
        
        logger.info("Entering main monitoring loop")
        
        while self._running and not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                # Check if it's time to capture screenshot
                time_since_last_screenshot = current_time - last_screenshot_time
                if time_since_last_screenshot >= self.screenshot_interval_seconds:
                    logger.info("Screenshot interval reached, capturing screenshot")
                    try:
                        screenshot_data = self.screenshot_capture.capture_screenshot()
                        if screenshot_data:
                            self.payload_builder.set_screenshot(screenshot_data)
                            logger.info("Screenshot captured and stored")
                        else:
                            logger.warning("Screenshot capture returned no data")
                    except Exception as e:
                        logger.error(f"Error capturing screenshot: {e}", exc_info=True)
                    last_screenshot_time = current_time
                
                # Check if it's time to update location
                time_since_last_location = current_time - last_location_update_time
                if time_since_last_location >= self.location_interval_seconds:
                    logger.info(f"🌍 Location update interval reached ({self.location_interval_seconds}s)")
                    print(f"🌍 Updating location (interval: {self.config.location_update_interval_minutes} minutes)...")
                    try:
                        updated_location = self.location_tracker.get_location()
                        if updated_location:
                            logger.info(f"✅ Location updated: {updated_location}")
                            print(f"✅ Location updated: {updated_location['city']}, {updated_location['state']}")
                        else:
                            logger.warning("⚠️ Location update returned None")
                            print("⚠️ Location update returned None")
                    except Exception as e:
                        logger.error(f"❌ Error updating location: {e}", exc_info=True)
                        print(f"❌ Error updating location: {e}")
                    last_location_update_time = current_time
                
                # Note: File sync is now handled by app usage tracker's polling loop
                # No need for separate file sync interval checking here
                
                # Check for configuration updates
                time_since_last_config_check = current_time - last_config_check_time
                if time_since_last_config_check >= config_check_interval:
                    try:
                        self.config_watcher.check_once()
                    except Exception as e:
                        logger.error(f"Error checking config updates: {e}", exc_info=True)
                    last_config_check_time = current_time
                
                # Check if it's time to send data
                time_since_last_send = current_time - last_data_send_time
                
                if time_since_last_send >= self.data_interval_seconds:
                    logger.info("Data transmission interval reached")
                    self._collect_and_send_data()
                    last_data_send_time = current_time
                    
                    # Start a new interval
                    self.payload_builder.start_interval()
                    self.activity_tracker.reset_interval()
                    self.app_usage_tracker.reset_interval()
                    self.browser_tab_tracker.reset_interval()
                
                # Process queued payloads if any
                queue_size = self.retry_manager.get_queue_size()
                if queue_size > 0:
                    logger.info(f"Processing {queue_size} queued payload(s)")
                    try:
                        successful, failed = self.retry_manager.process_queue()
                        logger.info(
                            f"Queue processing: {successful} successful, {failed} failed"
                        )
                    except Exception as e:
                        logger.error(f"Error processing queue: {e}", exc_info=True)
                
                # Sleep for a short interval before checking again
                # Use a short sleep to allow responsive shutdown
                self._stop_event.wait(timeout=1.0)
                
            except Exception as e:
                # Log error but continue operation (graceful error handling)
                logger.error(
                    f"Error in monitoring loop: {e}",
                    exc_info=True
                )
                # Sleep briefly before continuing
                time.sleep(1.0)
        
        logger.info("Exited main monitoring loop")
    
    def _collect_and_send_data(self) -> None:
        """
        Collect monitoring data and send to server.
        
        Handles errors gracefully and queues data if transmission fails.
        
        Requirements: 6.3, 6.4, 7.5
        """
        try:
            # Build the payload
            logger.info("Building data payload")
            payload = self.payload_builder.build_payload(self.client_id, self.client_id)
            
            # Send with retry logic
            logger.info("Sending payload to server")
            success = self.retry_manager.send_with_retry(payload)
            
            if success:
                logger.info("Data transmitted successfully")
            else:
                logger.warning("Data transmission failed, payload queued for retry")
        
        except Exception as e:
            # Log error and continue operation
            logger.error(
                f"Error collecting and sending data: {e}",
                exc_info=True
            )
    
    def is_running(self) -> bool:
        """
        Check if the monitoring loop is currently running.
        
        Returns:
            True if running, False otherwise
        """
        return self._running
    
    def get_status(self) -> dict:
        """
        Get the current status of the monitoring loop.
        
        Returns:
            Dictionary containing status information
        """
        work_seconds, idle_seconds, current_state = self.activity_tracker.get_activity_data()
        queue_size = self.retry_manager.get_queue_size()
        
        return {
            'running': self._running,
            'client_id': self.client_id,
            'current_state': current_state.value,
            'work_seconds': work_seconds,
            'idle_seconds': idle_seconds,
            'queue_size': queue_size,
            'data_interval_minutes': self.config.data_send_interval_minutes,
            'screenshot_interval_minutes': self.config.screenshot_interval_minutes,
            'idle_threshold_seconds': self.config.idle_threshold_seconds
        }

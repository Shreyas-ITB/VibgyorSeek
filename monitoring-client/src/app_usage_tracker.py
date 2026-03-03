"""
Application Usage Tracker Module

This module tracks how long each application is actively used (foreground).
It maintains cumulative time for each application during the monitoring interval.
Also updates browser tab usage tracker in the same polling loop to avoid extra load.

Requirements: Application screen time tracking
"""

import time
import threading
import logging
from typing import Dict, Optional, TYPE_CHECKING
from .app_monitor import ApplicationMonitor

if TYPE_CHECKING:
    from .browser_tab_usage_tracker import BrowserTabUsageTracker
    from .file_sync_manager import FileSyncManager
    from .server_env_watcher import ServerEnvWatcher


logger = logging.getLogger(__name__)


class ApplicationUsageTracker:
    """Tracks cumulative usage time for each application."""
    
    def __init__(self, app_monitor: ApplicationMonitor, poll_interval: float = 2.0, browser_tab_tracker: Optional['BrowserTabUsageTracker'] = None, file_sync_manager: Optional['FileSyncManager'] = None, server_env_watcher: Optional['ServerEnvWatcher'] = None):
        """
        Initialize the application usage tracker.
        
        Args:
            app_monitor: ApplicationMonitor instance to get foreground app
            poll_interval: How often to check foreground app (seconds, default: 2.0)
            browser_tab_tracker: Optional BrowserTabUsageTracker to update concurrently
            file_sync_manager: Optional FileSyncManager to update concurrently
            server_env_watcher: Optional ServerEnvWatcher to check for config changes
        """
        self.app_monitor = app_monitor
        self.poll_interval = max(2.0, poll_interval)  # Minimum 2 seconds to reduce CPU usage
        self.browser_tab_tracker = browser_tab_tracker
        self.file_sync_manager = file_sync_manager
        self.server_env_watcher = server_env_watcher
        
        # Track cumulative time per application (in seconds)
        self._app_durations: Dict[str, float] = {}
        
        # Track current foreground app
        self._current_app: Optional[str] = None
        self._last_check_time: float = time.time()
        
        # Threading
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        logger.info(f"ApplicationUsageTracker initialized with poll_interval={self.poll_interval}s")
    
    def start(self) -> None:
        """Start tracking application usage."""
        if self._running:
            logger.warning("Application usage tracker already running")
            return
        
        logger.info("Starting application usage tracker...")
        self._running = True
        self._stop_event.clear()
        self._last_check_time = time.time()
        
        try:
            self._thread = threading.Thread(target=self._tracking_loop, daemon=True)
            self._thread.start()
            logger.info(f"Application usage tracking thread started successfully (poll interval: {self.poll_interval}s)")
            print(f"✅ APP USAGE TRACKER: Started (polling every {self.poll_interval}s)")
        except Exception as e:
            logger.error(f"Failed to start application usage tracking thread: {e}", exc_info=True)
            print(f"❌ Failed to start app usage tracker: {e}")
            self._running = False
            raise
    
    def stop(self) -> None:
        """Stop tracking application usage."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("Application usage tracking stopped")
    
    def _tracking_loop(self) -> None:
        """Main tracking loop that runs in background thread."""
        try:
            logger.info("App usage tracking loop started")
            print("🔍 APP USAGE TRACKER: Started tracking loop")
        except Exception as e:
            logger.error(f"Error in initial tracking loop setup: {e}", exc_info=True)
            print(f"❌ ERROR in tracking loop setup: {e}")
            return
        
        iteration = 0
        while self._running:
            try:
                iteration += 1
                current_time = time.time()
                
                # Get current foreground application
                try:
                    foreground_app = self.app_monitor.get_foreground_application()
                except Exception as e:
                    logger.error(f"Error getting foreground application: {e}", exc_info=True)
                    print(f"❌ ERROR getting foreground app: {e}")
                    foreground_app = None
                
                if foreground_app:
                    print(f"🎯 [Poll {iteration}] Foreground: {foreground_app}")
                    logger.info(f"[Iteration {iteration}] Foreground app: {foreground_app}")
                else:
                    print(f"❌ [Poll {iteration}] No foreground app detected!")
                    logger.warning(f"[Iteration {iteration}] No foreground app detected!")
                
                with self._lock:
                    # Calculate time elapsed since last check
                    time_elapsed = current_time - self._last_check_time
                    
                    # Add elapsed time to current app's duration
                    if self._current_app and time_elapsed > 0:
                        if self._current_app not in self._app_durations:
                            self._app_durations[self._current_app] = 0.0
                        self._app_durations[self._current_app] += time_elapsed
                        print(f"⏱️  Added {time_elapsed:.1f}s to {self._current_app} → Total: {self._app_durations[self._current_app]:.1f}s")
                        logger.info(f"[Iteration {iteration}] Added {time_elapsed:.1f}s to {self._current_app} (total: {self._app_durations[self._current_app]:.1f}s)")
                    elif self._current_app is None:
                        print(f"⏸️  First iteration - no time to add yet")
                        logger.info(f"[Iteration {iteration}] No current app to add time to (first iteration)")
                    
                    # Update current app and last check time
                    self._current_app = foreground_app
                    self._last_check_time = current_time
                    
                    if self._app_durations:
                        logger.info(f"[Iteration {iteration}] Current durations: {dict(self._app_durations)}")
                
                # Update browser tab usage tracker if provided (same polling loop)
                if self.browser_tab_tracker:
                    try:
                        self.browser_tab_tracker.update()
                        print(f"🌐 [Poll {iteration}] Updated browser tab usage")
                    except Exception as e:
                        logger.error(f"Error updating browser tab tracker: {e}", exc_info=True)
                
                # Update file sync manager if provided (same polling loop)
                if self.file_sync_manager:
                    try:
                        self.file_sync_manager.update()
                    except Exception as e:
                        logger.error(f"Error updating file sync manager: {e}", exc_info=True)
                        print(f"❌ FILE SYNC ERROR: {e}")
                
                # Check server env for changes if provided (same polling loop)
                if self.server_env_watcher:
                    try:
                        print(f"🔍 [Poll {iteration}] Checking server env for changes...")
                        changes_detected = self.server_env_watcher.check_for_changes()
                        if changes_detected:
                            print(f"🔄 SERVER ENV: Changes detected - writing to .env file")
                            logger.info("Server env changes detected, writing to .env file")
                            # Trigger config_watcher to write the new config
                            # This will be handled by a callback we'll set up
                    except Exception as e:
                        logger.error(f"Error checking server env: {e}", exc_info=True)
                        print(f"❌ SERVER ENV ERROR: {e}")
                
                # Use event-based sleep for responsive shutdown
                if self._stop_event.wait(timeout=self.poll_interval):
                    break
            
            except Exception as e:
                print(f"❌ ERROR in tracking loop: {e}")
                logger.error(f"Error in application usage tracking loop: {e}", exc_info=True)
                if self._stop_event.wait(timeout=self.poll_interval):
                    break
        
        print("🛑 APP USAGE TRACKER: Stopped tracking loop")
        logger.info("App usage tracking loop stopped")
    
    def get_application_durations(self) -> Dict[str, int]:
        """
        Get cumulative duration for each application.
        
        Returns:
            Dictionary mapping application name to duration in seconds
        """
        with self._lock:
            # Update current app's time before returning
            if self._current_app and self._running:
                current_time = time.time()
                time_elapsed = current_time - self._last_check_time
                
                if time_elapsed > 0:
                    if self._current_app not in self._app_durations:
                        self._app_durations[self._current_app] = 0.0
                    self._app_durations[self._current_app] += time_elapsed
                    self._last_check_time = current_time
                    logger.debug(f"Updated {self._current_app}: +{time_elapsed:.1f}s (total: {self._app_durations[self._current_app]:.1f}s)")
            
            # Return rounded durations (only apps with >0 duration)
            result = {
                app: int(round(duration))
                for app, duration in self._app_durations.items()
                if duration > 0
            }
            print(f"📊 DURATIONS: {result}")
            logger.info(f"Returning application durations: {result}")
            return result
    
    def reset_interval(self) -> None:
        """Reset application durations for a new interval."""
        with self._lock:
            self._app_durations.clear()
            self._last_check_time = time.time()
            logger.debug("Application usage durations reset")
    
    def get_current_application(self) -> Optional[str]:
        """Get the currently active foreground application."""
        with self._lock:
            return self._current_app


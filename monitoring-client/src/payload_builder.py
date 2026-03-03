"""
Payload Builder Module

This module aggregates data from all monitor modules and constructs
the JSON payload for transmission to the server.

Requirements: 1.3, 2.5, 3.4, 4.3, 5.4, 6.5
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, TYPE_CHECKING
import logging

from .activity_tracker import ActivityTracker
from .app_monitor import ApplicationMonitor
from .browser_monitor import BrowserMonitor
from .screenshot import ScreenshotCapture
from .app_usage_tracker import ApplicationUsageTracker

if TYPE_CHECKING:
    from .browser_tab_usage_tracker import BrowserTabUsageTracker
    from .location_tracker import LocationTracker


logger = logging.getLogger(__name__)


class PayloadBuilder:
    """Builds data payloads for transmission to the monitoring server."""
    
    def __init__(
        self,
        activity_tracker: ActivityTracker,
        app_monitor: ApplicationMonitor,
        browser_monitor: BrowserMonitor,
        screenshot_capture: ScreenshotCapture,
        app_usage_tracker: ApplicationUsageTracker,
        browser_tab_tracker: Optional['BrowserTabUsageTracker'] = None,
        location_tracker: Optional['LocationTracker'] = None
    ):
        """
        Initialize the payload builder with monitor modules.
        
        Args:
            activity_tracker: Activity tracking module instance
            app_monitor: Application monitoring module instance
            browser_monitor: Browser monitoring module instance
            screenshot_capture: Screenshot capture module instance
            app_usage_tracker: Application usage tracking module instance
            browser_tab_tracker: Browser tab usage tracking module instance (optional)
            location_tracker: Location tracking module instance (optional)
        """
        self.activity_tracker = activity_tracker
        self.app_monitor = app_monitor
        self.browser_monitor = browser_monitor
        self.screenshot_capture = screenshot_capture
        self.app_usage_tracker = app_usage_tracker
        self.browser_tab_tracker = browser_tab_tracker
        self.location_tracker = location_tracker
        self.interval_start_time: Optional[datetime] = None
        self._screenshot_data: Optional[str] = None
    
    def start_interval(self) -> None:
        """Mark the start of a new monitoring interval."""
        self.interval_start_time = datetime.now(timezone.utc)
        self._screenshot_data = None  # Clear screenshot for new interval
        logger.debug(f"Started new interval at {self.interval_start_time.isoformat()}")
    
    def set_screenshot(self, screenshot_data: str) -> None:
        """Store screenshot data for the current interval."""
        self._screenshot_data = screenshot_data
        logger.debug("Screenshot data stored for current interval")
    
    def build_payload(self, employee_name: str, client_id: str) -> Dict[str, Any]:
        """
        Build a complete data payload with all monitoring data.
        
        Args:
            employee_name: The name of the employee (deprecated, kept for compatibility)
            client_id: The unique client identifier
        
        Returns:
            Dictionary containing the complete payload structure
        
        Requirements: 1.3, 2.5, 3.4, 4.3, 5.4, 6.5
        """
        if not client_id or not client_id.strip():
            raise ValueError("client_id cannot be empty")
        
        interval_end_time = datetime.now(timezone.utc)
        
        # Use stored interval start time, or current time if not set
        if self.interval_start_time is None:
            self.interval_start_time = interval_end_time
        
        # Get activity data
        work_seconds, idle_seconds, current_state = self.activity_tracker.get_activity_data()
        
        # Get application usage durations (only foreground apps that were used)
        app_durations = self.app_usage_tracker.get_application_durations()
        print(f"📱 App durations from tracker: {app_durations}")
        logger.info(f"App usage durations from tracker: {app_durations}")
        
        # Get ALL running applications (both foreground and background)
        all_running_apps = self.app_monitor.get_application_names()
        print(f"💻 All running apps: {len(all_running_apps)} apps")
        logger.info(f"All running applications: {all_running_apps}")
        
        # Build applications list: all apps with their durations
        # Apps that were used get their tracked duration, others get 0
        applications = []
        for app_name in all_running_apps:
            duration = app_durations.get(app_name, 0)
            applications.append({"name": app_name, "duration": duration})
        
        print(f"📦 Payload will include {len(applications)} apps ({len([a for a in applications if a['duration'] > 0])} with duration > 0)")
        logger.info(f"Applications list for payload ({len(applications)} apps): {applications[:5]}...")
        
        # Get browser tab data with durations
        if self.browser_tab_tracker:
            browser_tabs = self.browser_tab_tracker.get_tab_durations()
            print(f"🌐 Browser tabs with durations: {len(browser_tabs)} tabs")
            logger.info(f"Browser tabs with durations: {browser_tabs}")
        else:
            # Fallback to basic tab data without durations
            browser_tabs = self.browser_monitor.get_browser_tabs()
            # Add duration field (0 for all)
            for tab in browser_tabs:
                tab['duration'] = 0
            print(f"🌐 Browser tabs (no duration tracking): {len(browser_tabs)} tabs")
            logger.info(f"Browser tabs without durations: {browser_tabs}")
        
        # Get location data
        location = None
        if self.location_tracker:
            logger.info("📍 Getting location for payload...")
            location = self.location_tracker.get_location()
            if location:
                logger.info(f"✅ Location data for payload: {location}")
                print(f"📍 Including location in payload: {location['city']}, {location['state']}")
            else:
                logger.warning("⚠️ No location data available for payload")
                print("⚠️ No location data available for payload")
        else:
            logger.warning("⚠️ Location tracker not initialized")
            print("⚠️ Location tracker not initialized")
        
        # Use stored screenshot data (captured at screenshot interval)
        screenshot_data = self._screenshot_data
        
        # Construct the payload
        payload = {
            "client_id": client_id.strip(),
            "employee_name": employee_name.strip() if employee_name else client_id.strip(),
            "timestamp": interval_end_time.isoformat(),
            "interval_start": self.interval_start_time.isoformat(),
            "interval_end": interval_end_time.isoformat(),
            "activity": {
                "work_seconds": work_seconds,
                "idle_seconds": idle_seconds
            },
            "applications": applications,
            "browser_tabs": browser_tabs,
            "screenshot": screenshot_data if screenshot_data else ""
        }
        
        # Add location if available
        if location:
            payload["location"] = location
            logger.info(f"✅ Location added to payload: {location}")
            print(f"✅ Location added to payload")
        else:
            logger.info("ℹ️ No location data to add to payload")
            print("ℹ️ No location in payload")
        
        logger.info(
            f"Built payload for client {client_id}: "
            f"{work_seconds}s work, {idle_seconds}s idle, "
            f"{len(applications)} apps, {len(browser_tabs)} tabs, "
            f"screenshot: {'yes' if screenshot_data else 'no'}"
        )
        
        return payload

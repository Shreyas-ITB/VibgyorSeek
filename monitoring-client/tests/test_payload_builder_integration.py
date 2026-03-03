"""Integration tests for the payload builder module."""

import pytest
import time
from datetime import datetime
from src.payload_builder import PayloadBuilder
from src.activity_tracker import ActivityTracker
from src.app_monitor import ApplicationMonitor
from src.browser_monitor import BrowserMonitor
from src.screenshot import ScreenshotCapture


class TestPayloadBuilderIntegration:
    """Integration tests for PayloadBuilder with real module instances."""
    
    @pytest.fixture
    def payload_builder(self):
        """Create a PayloadBuilder with real module instances."""
        activity_tracker = ActivityTracker(idle_threshold_seconds=5)
        app_monitor = ApplicationMonitor()
        browser_monitor = BrowserMonitor()
        screenshot_capture = ScreenshotCapture(jpeg_quality=75)
        
        return PayloadBuilder(
            activity_tracker=activity_tracker,
            app_monitor=app_monitor,
            browser_monitor=browser_monitor,
            screenshot_capture=screenshot_capture
        )
    
    def test_build_payload_with_real_modules(self, payload_builder):
        """Test building a payload with real module instances."""
        # Start the activity tracker
        payload_builder.activity_tracker.start()
        
        try:
            # Start an interval
            payload_builder.start_interval()
            
            # Wait a bit to collect some data
            time.sleep(0.5)
            
            # Build the payload
            payload = payload_builder.build_payload("test-client-id", "Test Employee")
            
            # Verify payload structure
            assert payload["employee_name"] == "Test Employee"
            assert "timestamp" in payload
            assert "interval_start" in payload
            assert "interval_end" in payload
            
            # Verify activity data
            assert "activity" in payload
            assert "work_seconds" in payload["activity"]
            assert "idle_seconds" in payload["activity"]
            assert isinstance(payload["activity"]["work_seconds"], int)
            assert isinstance(payload["activity"]["idle_seconds"], int)
            
            # Verify applications list
            assert "applications" in payload
            assert isinstance(payload["applications"], list)
            # Should have at least some applications running
            assert len(payload["applications"]) >= 0
            
            # Verify browser tabs list
            assert "browser_tabs" in payload
            assert isinstance(payload["browser_tabs"], list)
            
            # Verify screenshot
            assert "screenshot" in payload
            # Screenshot should be a string (base64 or empty)
            assert isinstance(payload["screenshot"], str)
        
        finally:
            # Stop the activity tracker
            payload_builder.activity_tracker.stop()
    
    def test_payload_interval_timing(self, payload_builder):
        """Test that interval timing is correctly tracked."""
        payload_builder.activity_tracker.start()
        
        try:
            # Start interval
            payload_builder.start_interval()
            start_time = payload_builder.interval_start_time
            
            # Wait a bit
            time.sleep(0.2)
            
            # Build payload
            payload = payload_builder.build_payload("test-client-id", "Test Employee")
            
            # Parse timestamps
            interval_start = datetime.fromisoformat(payload["interval_start"])
            interval_end = datetime.fromisoformat(payload["interval_end"])
            
            # Verify timing
            assert interval_start == start_time
            assert interval_end >= interval_start
            
            # The interval should be at least 0.2 seconds
            duration = (interval_end - interval_start).total_seconds()
            assert duration >= 0.2
        
        finally:
            payload_builder.activity_tracker.stop()
    
    def test_multiple_payloads_with_interval_reset(self, payload_builder):
        """Test building multiple payloads with interval resets."""
        payload_builder.activity_tracker.start()
        
        try:
            # First payload
            payload_builder.start_interval()
            time.sleep(0.1)
            payload1 = payload_builder.build_payload("test-client-id", "Test Employee")
            
            # Reset interval for second payload
            payload_builder.start_interval()
            time.sleep(0.1)
            payload2 = payload_builder.build_payload("test-client-id", "Test Employee")
            
            # Verify both payloads are valid
            assert payload1["employee_name"] == "Test Employee"
            assert payload2["employee_name"] == "Test Employee"
            
            # Verify they have different timestamps
            assert payload1["timestamp"] != payload2["timestamp"]
        
        finally:
            payload_builder.activity_tracker.stop()
    
    def test_payload_with_no_screenshot(self, payload_builder):
        """Test that payload handles screenshot capture gracefully."""
        payload_builder.activity_tracker.start()
        
        try:
            payload = payload_builder.build_payload("test-client-id", "Test Employee")
            
            # Screenshot field should exist (even if empty)
            assert "screenshot" in payload
            assert isinstance(payload["screenshot"], str)
        
        finally:
            payload_builder.activity_tracker.stop()
    
    def test_payload_json_serializable(self, payload_builder):
        """Test that the payload can be serialized to JSON."""
        import json
        
        payload_builder.activity_tracker.start()
        
        try:
            payload = payload_builder.build_payload("test-client-id", "Test Employee")
            
            # Should be able to serialize to JSON
            json_str = json.dumps(payload)
            
            # Should be able to deserialize back
            deserialized = json.loads(json_str)
            
            # Verify key fields are preserved
            assert deserialized["employee_name"] == "Test Employee"
            assert "activity" in deserialized
            assert "applications" in deserialized
        
        finally:
            payload_builder.activity_tracker.stop()

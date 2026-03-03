"""Unit tests for the payload builder module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from src.payload_builder import PayloadBuilder
from src.activity_tracker import ActivityState


class TestPayloadBuilder:
    """Test suite for PayloadBuilder class."""
    
    @pytest.fixture
    def mock_activity_tracker(self):
        """Create a mock activity tracker."""
        tracker = Mock()
        tracker.get_activity_data.return_value = (480, 120, ActivityState.WORK)
        return tracker
    
    @pytest.fixture
    def mock_app_monitor(self):
        """Create a mock application monitor."""
        monitor = Mock()
        monitor.get_running_applications.return_value = [
            {"name": "Chrome", "active": True},
            {"name": "VSCode", "active": False}
        ]
        return monitor
    
    @pytest.fixture
    def mock_browser_monitor(self):
        """Create a mock browser monitor."""
        monitor = Mock()
        monitor.get_browser_tabs.return_value = [
            {"browser": "Chrome", "title": "GitHub", "url": "https://github.com"}
        ]
        return monitor
    
    @pytest.fixture
    def mock_screenshot_capture(self):
        """Create a mock screenshot capture."""
        capture = Mock()
        capture.capture_screenshot.return_value = "base64_encoded_screenshot_data"
        return capture
    
    @pytest.fixture
    def payload_builder(
        self,
        mock_activity_tracker,
        mock_app_monitor,
        mock_browser_monitor,
        mock_screenshot_capture
    ):
        """Create a PayloadBuilder instance with mocked dependencies."""
        return PayloadBuilder(
            activity_tracker=mock_activity_tracker,
            app_monitor=mock_app_monitor,
            browser_monitor=mock_browser_monitor,
            screenshot_capture=mock_screenshot_capture
        )
    
    def test_build_payload_contains_all_required_fields(self, payload_builder):
        """Test that payload contains all required fields."""
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        # Check top-level fields
        assert "client_id" in payload
        assert "employee_name" in payload
        assert "timestamp" in payload
        assert "interval_start" in payload
        assert "interval_end" in payload
        assert "activity" in payload
        assert "applications" in payload
        assert "browser_tabs" in payload
        assert "screenshot" in payload
    
    def test_build_payload_client_id(self, payload_builder):
        """Test that client_id is correctly included."""
        payload = payload_builder.build_payload("test-client-123", "John Doe")
        assert payload["client_id"] == "test-client-123"
    
    def test_build_payload_employee_name(self, payload_builder):
        """Test that employee name is correctly included."""
        payload = payload_builder.build_payload("test-client-id", "Jane Smith")
        assert payload["employee_name"] == "Jane Smith"
    
    def test_build_payload_strips_employee_name(self, payload_builder):
        """Test that employee name is stripped of whitespace."""
        payload = payload_builder.build_payload("test-client-id", "  John Doe  ")
        assert payload["employee_name"] == "John Doe"
    
    def test_build_payload_empty_client_id_raises_error(self, payload_builder):
        """Test that empty client_id raises ValueError."""
        with pytest.raises(ValueError, match="client_id cannot be empty"):
            payload_builder.build_payload("", "John Doe")
    
    def test_build_payload_whitespace_client_id_raises_error(self, payload_builder):
        """Test that whitespace-only client_id raises ValueError."""
        with pytest.raises(ValueError, match="client_id cannot be empty"):
            payload_builder.build_payload("   ", "John Doe")
    
    def test_build_payload_activity_data(self, payload_builder, mock_activity_tracker):
        """Test that activity data is correctly included."""
        mock_activity_tracker.get_activity_data.return_value = (600, 300, ActivityState.WORK)
        
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        assert payload["activity"]["work_seconds"] == 600
        assert payload["activity"]["idle_seconds"] == 300
    
    def test_build_payload_applications(self, payload_builder, mock_app_monitor):
        """Test that applications list is correctly included."""
        apps = [
            {"name": "Chrome", "active": True},
            {"name": "VSCode", "active": False},
            {"name": "Slack", "active": False}
        ]
        mock_app_monitor.get_running_applications.return_value = apps
        
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        assert payload["applications"] == apps
        assert len(payload["applications"]) == 3
    
    def test_build_payload_browser_tabs(self, payload_builder, mock_browser_monitor):
        """Test that browser tabs are correctly included."""
        tabs = [
            {"browser": "Chrome", "title": "GitHub", "url": "https://github.com"},
            {"browser": "Firefox", "title": "MDN", "url": "https://developer.mozilla.org"}
        ]
        mock_browser_monitor.get_browser_tabs.return_value = tabs
        
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        assert payload["browser_tabs"] == tabs
        assert len(payload["browser_tabs"]) == 2
    
    def test_build_payload_screenshot(self, payload_builder, mock_screenshot_capture):
        """Test that screenshot is correctly included."""
        mock_screenshot_capture.capture_screenshot.return_value = "screenshot_base64_data"
        
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        assert payload["screenshot"] == "screenshot_base64_data"
    
    def test_build_payload_screenshot_failure(self, payload_builder, mock_screenshot_capture):
        """Test that payload handles screenshot capture failure gracefully."""
        mock_screenshot_capture.capture_screenshot.return_value = None
        
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        assert payload["screenshot"] == ""
    
    def test_build_payload_timestamps_are_iso_format(self, payload_builder):
        """Test that timestamps are in ISO format."""
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        # Verify timestamps can be parsed
        datetime.fromisoformat(payload["timestamp"])
        datetime.fromisoformat(payload["interval_start"])
        datetime.fromisoformat(payload["interval_end"])
    
    def test_build_payload_interval_ordering(self, payload_builder):
        """Test that interval_start is before or equal to interval_end."""
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        start = datetime.fromisoformat(payload["interval_start"])
        end = datetime.fromisoformat(payload["interval_end"])
        
        assert start <= end
    
    def test_start_interval_sets_start_time(self, payload_builder):
        """Test that start_interval sets the interval start time."""
        payload_builder.start_interval()
        
        assert payload_builder.interval_start_time is not None
        assert isinstance(payload_builder.interval_start_time, datetime)
    
    def test_build_payload_uses_interval_start_time(self, payload_builder):
        """Test that payload uses the interval start time set by start_interval."""
        payload_builder.start_interval()
        start_time = payload_builder.interval_start_time
        
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        assert payload["interval_start"] == start_time.isoformat()
    
    def test_build_payload_empty_applications_list(self, payload_builder, mock_app_monitor):
        """Test payload with no applications."""
        mock_app_monitor.get_running_applications.return_value = []
        
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        assert payload["applications"] == []
        assert len(payload["applications"]) == 0
    
    def test_build_payload_empty_browser_tabs_list(self, payload_builder, mock_browser_monitor):
        """Test payload with no browser tabs."""
        mock_browser_monitor.get_browser_tabs.return_value = []
        
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        assert payload["browser_tabs"] == []
        assert len(payload["browser_tabs"]) == 0
    
    def test_build_payload_zero_activity_time(self, payload_builder, mock_activity_tracker):
        """Test payload with zero work and idle time."""
        mock_activity_tracker.get_activity_data.return_value = (0, 0, ActivityState.IDLE)
        
        payload = payload_builder.build_payload("test-client-id", "John Doe")
        
        assert payload["activity"]["work_seconds"] == 0
        assert payload["activity"]["idle_seconds"] == 0

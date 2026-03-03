"""
Unit tests for the monitoring loop module.

Tests the main monitoring loop coordination, interval-based execution,
and error handling.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call
from src.monitoring_loop import MonitoringLoop
from src.config import Config
from src.activity_tracker import ActivityState


class TestMonitoringLoopInitialization:
    """Test monitoring loop initialization."""
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    @patch('src.monitoring_loop.ActivityTracker')
    @patch('src.monitoring_loop.ApplicationMonitor')
    @patch('src.monitoring_loop.BrowserMonitor')
    @patch('src.monitoring_loop.ScreenshotCapture')
    @patch('src.monitoring_loop.PayloadBuilder')
    @patch('src.monitoring_loop.HTTPTransmitter')
    @patch('src.monitoring_loop.QueueManager')
    @patch('src.monitoring_loop.RetryManager')
    def test_initialization_success(
        self,
        mock_retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        mock_payload_builder,
        mock_screenshot,
        mock_browser_monitor,
        mock_app_monitor,
        mock_activity_tracker,
        mock_retrieve_name
    ):
        """Test successful initialization of monitoring loop."""
        mock_retrieve_name.return_value = "John Doe"
        
        config = Mock(spec=Config)
        config.idle_threshold_seconds = 300
        config.screenshot_quality = 75
        config.server_url = "https://example.com/api"
        config.auth_token = "test_token"
        config.data_send_interval_minutes = 10
        config.screenshot_interval_minutes = 10
        
        loop = MonitoringLoop(config=config)
        
        assert loop.employee_name == "John Doe"
        assert loop.config == config
        assert not loop.is_running()
        
        # Verify all modules were initialized
        mock_activity_tracker.assert_called_once_with(idle_threshold_seconds=300)
        mock_app_monitor.assert_called_once()
        mock_browser_monitor.assert_called_once()
        mock_screenshot.assert_called_once_with(jpeg_quality=75)
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    def test_initialization_no_employee_name(self, mock_retrieve_name):
        """Test initialization fails when employee name is not configured."""
        mock_retrieve_name.return_value = None
        
        config = Mock(spec=Config)
        
        with pytest.raises(RuntimeError, match="Employee name not configured"):
            MonitoringLoop(config=config)
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    @patch('src.monitoring_loop.ActivityTracker')
    def test_initialization_module_failure(
        self,
        mock_activity_tracker,
        mock_retrieve_name
    ):
        """Test initialization handles module initialization failures."""
        mock_retrieve_name.return_value = "John Doe"
        mock_activity_tracker.side_effect = Exception("Initialization failed")
        
        config = Mock(spec=Config)
        config.idle_threshold_seconds = 300
        
        with pytest.raises(Exception, match="Initialization failed"):
            MonitoringLoop(config=config)


class TestMonitoringLoopStartStop:
    """Test monitoring loop start and stop operations."""
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    @patch('src.monitoring_loop.ActivityTracker')
    @patch('src.monitoring_loop.ApplicationMonitor')
    @patch('src.monitoring_loop.BrowserMonitor')
    @patch('src.monitoring_loop.ScreenshotCapture')
    @patch('src.monitoring_loop.PayloadBuilder')
    @patch('src.monitoring_loop.HTTPTransmitter')
    @patch('src.monitoring_loop.QueueManager')
    @patch('src.monitoring_loop.RetryManager')
    def test_start_success(
        self,
        mock_retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        mock_payload_builder,
        mock_screenshot,
        mock_browser_monitor,
        mock_app_monitor,
        mock_activity_tracker,
        mock_retrieve_name
    ):
        """Test successful start of monitoring loop."""
        mock_retrieve_name.return_value = "John Doe"
        
        config = Mock(spec=Config)
        config.idle_threshold_seconds = 300
        config.screenshot_quality = 75
        config.server_url = "https://example.com/api"
        config.auth_token = "test_token"
        config.data_send_interval_minutes = 10
        config.screenshot_interval_minutes = 10
        
        loop = MonitoringLoop(config=config)
        
        # Mock activity tracker instance
        mock_tracker_instance = mock_activity_tracker.return_value
        
        loop.start()
        
        assert loop.is_running()
        mock_tracker_instance.start.assert_called_once()
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    @patch('src.monitoring_loop.ActivityTracker')
    @patch('src.monitoring_loop.ApplicationMonitor')
    @patch('src.monitoring_loop.BrowserMonitor')
    @patch('src.monitoring_loop.ScreenshotCapture')
    @patch('src.monitoring_loop.PayloadBuilder')
    @patch('src.monitoring_loop.HTTPTransmitter')
    @patch('src.monitoring_loop.QueueManager')
    @patch('src.monitoring_loop.RetryManager')
    def test_stop_success(
        self,
        mock_retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        mock_payload_builder,
        mock_screenshot,
        mock_browser_monitor,
        mock_app_monitor,
        mock_activity_tracker,
        mock_retrieve_name
    ):
        """Test successful stop of monitoring loop."""
        mock_retrieve_name.return_value = "John Doe"
        
        config = Mock(spec=Config)
        config.idle_threshold_seconds = 300
        config.screenshot_quality = 75
        config.server_url = "https://example.com/api"
        config.auth_token = "test_token"
        config.data_send_interval_minutes = 10
        config.screenshot_interval_minutes = 10
        
        loop = MonitoringLoop(config=config)
        
        # Mock activity tracker instance
        mock_tracker_instance = mock_activity_tracker.return_value
        
        loop.start()
        time.sleep(0.1)  # Let the loop start
        loop.stop()
        
        assert not loop.is_running()
        mock_tracker_instance.stop.assert_called_once()


class TestMonitoringLoopDataCollection:
    """Test data collection and transmission."""
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    @patch('src.monitoring_loop.ActivityTracker')
    @patch('src.monitoring_loop.ApplicationMonitor')
    @patch('src.monitoring_loop.BrowserMonitor')
    @patch('src.monitoring_loop.ScreenshotCapture')
    @patch('src.monitoring_loop.PayloadBuilder')
    @patch('src.monitoring_loop.HTTPTransmitter')
    @patch('src.monitoring_loop.QueueManager')
    @patch('src.monitoring_loop.RetryManager')
    def test_collect_and_send_data_success(
        self,
        mock_retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        mock_payload_builder,
        mock_screenshot,
        mock_browser_monitor,
        mock_app_monitor,
        mock_activity_tracker,
        mock_retrieve_name
    ):
        """Test successful data collection and transmission."""
        mock_retrieve_name.return_value = "John Doe"
        
        config = Mock(spec=Config)
        config.idle_threshold_seconds = 300
        config.screenshot_quality = 75
        config.server_url = "https://example.com/api"
        config.auth_token = "test_token"
        config.data_send_interval_minutes = 10
        config.screenshot_interval_minutes = 10
        
        loop = MonitoringLoop(config=config)
        
        # Mock payload builder
        mock_builder_instance = mock_payload_builder.return_value
        mock_builder_instance.build_payload.return_value = {"test": "payload"}
        
        # Mock retry manager
        mock_retry_instance = mock_retry_manager.return_value
        mock_retry_instance.send_with_retry.return_value = True
        
        # Call the method
        loop._collect_and_send_data()
        
        # Verify payload was built and sent
        mock_builder_instance.build_payload.assert_called_once_with("John Doe")
        mock_retry_instance.send_with_retry.assert_called_once_with({"test": "payload"})
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    @patch('src.monitoring_loop.ActivityTracker')
    @patch('src.monitoring_loop.ApplicationMonitor')
    @patch('src.monitoring_loop.BrowserMonitor')
    @patch('src.monitoring_loop.ScreenshotCapture')
    @patch('src.monitoring_loop.PayloadBuilder')
    @patch('src.monitoring_loop.HTTPTransmitter')
    @patch('src.monitoring_loop.QueueManager')
    @patch('src.monitoring_loop.RetryManager')
    def test_collect_and_send_data_handles_errors(
        self,
        mock_retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        mock_payload_builder,
        mock_screenshot,
        mock_browser_monitor,
        mock_app_monitor,
        mock_activity_tracker,
        mock_retrieve_name
    ):
        """Test that data collection handles errors gracefully."""
        mock_retrieve_name.return_value = "John Doe"
        
        config = Mock(spec=Config)
        config.idle_threshold_seconds = 300
        config.screenshot_quality = 75
        config.server_url = "https://example.com/api"
        config.auth_token = "test_token"
        config.data_send_interval_minutes = 10
        config.screenshot_interval_minutes = 10
        
        loop = MonitoringLoop(config=config)
        
        # Mock payload builder to raise an exception
        mock_builder_instance = mock_payload_builder.return_value
        mock_builder_instance.build_payload.side_effect = Exception("Build failed")
        
        # Should not raise exception (graceful error handling)
        loop._collect_and_send_data()


class TestMonitoringLoopStatus:
    """Test monitoring loop status reporting."""
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    @patch('src.monitoring_loop.ActivityTracker')
    @patch('src.monitoring_loop.ApplicationMonitor')
    @patch('src.monitoring_loop.BrowserMonitor')
    @patch('src.monitoring_loop.ScreenshotCapture')
    @patch('src.monitoring_loop.PayloadBuilder')
    @patch('src.monitoring_loop.HTTPTransmitter')
    @patch('src.monitoring_loop.QueueManager')
    @patch('src.monitoring_loop.RetryManager')
    def test_get_status(
        self,
        mock_retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        mock_payload_builder,
        mock_screenshot,
        mock_browser_monitor,
        mock_app_monitor,
        mock_activity_tracker,
        mock_retrieve_name
    ):
        """Test getting monitoring loop status."""
        mock_retrieve_name.return_value = "John Doe"
        
        config = Mock(spec=Config)
        config.idle_threshold_seconds = 300
        config.screenshot_quality = 75
        config.server_url = "https://example.com/api"
        config.auth_token = "test_token"
        config.data_send_interval_minutes = 10
        config.screenshot_interval_minutes = 10
        
        loop = MonitoringLoop(config=config)
        
        # Mock activity tracker
        mock_tracker_instance = mock_activity_tracker.return_value
        mock_tracker_instance.get_activity_data.return_value = (480, 120, ActivityState.WORK)
        
        # Mock retry manager
        mock_retry_instance = mock_retry_manager.return_value
        mock_retry_instance.get_queue_size.return_value = 5
        
        status = loop.get_status()
        
        assert status['running'] == False
        assert status['employee_name'] == "John Doe"
        assert status['current_state'] == "WORK"
        assert status['work_seconds'] == 480
        assert status['idle_seconds'] == 120
        assert status['queue_size'] == 5
        assert status['data_interval_minutes'] == 10
        assert status['screenshot_interval_minutes'] == 10
        assert status['idle_threshold_seconds'] == 300

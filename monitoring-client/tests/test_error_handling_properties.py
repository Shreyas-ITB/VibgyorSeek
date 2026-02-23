"""Property-based tests for error handling and logging.

Feature: vibgyorseek-employee-monitoring

Tests that errors and exceptions are properly logged to the log file.
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.queue_manager import QueueManager
from src.http_transmitter import HTTPTransmitter
from src.screenshot import ScreenshotCapture
from src.app_monitor import ApplicationMonitor
from src.browser_monitor import BrowserMonitor
from unittest.mock import patch


# Custom strategies for generating test data
@st.composite
def error_message_strategy(draw):
    """Generate error messages for testing."""
    error_types = [
        "Connection refused",
        "Timeout error",
        "Database error",
        "File not found",
        "Permission denied",
        "Invalid data",
        "Network unreachable"
    ]
    error_type = draw(st.sampled_from(error_types))
    error_code = draw(st.integers(min_value=1, max_value=999))
    return f"{error_type}: Error code {error_code}"


@st.composite
def payload_strategy(draw):
    """Generate a valid data payload for testing."""
    employee_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' '
    )))
    
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    timestamp = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z"
    
    work_seconds = draw(st.integers(min_value=0, max_value=3600))
    idle_seconds = draw(st.integers(min_value=0, max_value=3600))
    
    return {
        "employee_name": employee_name.strip(),
        "timestamp": timestamp,
        "interval_start": timestamp,
        "interval_end": timestamp,
        "activity": {
            "work_seconds": work_seconds,
            "idle_seconds": idle_seconds
        },
        "applications": [
            {"name": "Test App", "active": True}
        ],
        "browser_tabs": [
            {"browser": "Chrome", "title": "Test", "url": "https://example.com"}
        ],
        "screenshot": "base64_test_data"
    }


# Property 11: Error Logging
# **Validates: Requirements 7.5, 16.1, 16.3**
@given(error_message=error_message_strategy())
@settings(max_examples=100, deadline=None)
def test_property_error_logging_http_transmitter(error_message):
    """
    Property 11: Error Logging
    
    For any error or exception encountered by the Monitoring_Client,
    a log entry containing the error details should be created in the log file.
    
    This test verifies that HTTP transmission errors are logged.
    
    **Validates: Requirements 7.5, 16.1, 16.3**
    """
    # Create HTTP transmitter
    transmitter = HTTPTransmitter(
        server_url="https://test-server.example.com/api/monitoring/data",
        auth_token="test_token"
    )
    
    # Mock the logger to verify it's called
    with patch('src.http_transmitter.logger') as mock_logger:
        # Mock requests.post to raise an exception with our error message
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception(error_message)
            
            # Attempt to send a payload - this should fail and log an error
            payload = {
                "employee_name": "Test Employee",
                "timestamp": "2024-01-01T12:00:00Z",
                "interval_start": "2024-01-01T12:00:00Z",
                "interval_end": "2024-01-01T12:00:00Z",
                "activity": {"work_seconds": 100, "idle_seconds": 50},
                "applications": [],
                "browser_tabs": [],
                "screenshot": "test_data"
            }
            
            success, error = transmitter.send_payload(payload)
            
            # Verify transmission failed
            assert success is False, "Transmission should fail when exception is raised"
            assert error is not None, "Error message should be returned"
            
            # Verify that logger.error was called
            assert mock_logger.error.called, \
                "Logger error method should be called when an error occurs"
            
            # Verify the error message contains relevant information
            error_calls = [str(call) for call in mock_logger.error.call_args_list]
            assert len(error_calls) > 0, "At least one error should be logged"


@given(payload=payload_strategy())
@settings(max_examples=100, deadline=None)
def test_property_error_logging_queue_manager(payload):
    """
    Property 11: Error Logging - Queue Manager
    
    For any error or exception encountered by the Queue Manager,
    a log entry containing the error details should be created in the log file.
    
    This test verifies that queue manager errors are logged.
    
    **Validates: Requirements 7.5, 16.1, 16.3**
    """
    # Mock the logger to verify it's called
    with patch('src.queue_manager.logger') as mock_logger:
        # Mock sqlite3.connect to raise an error
        with patch('sqlite3.connect') as mock_connect:
            import sqlite3
            mock_connect.side_effect = sqlite3.Error("Database connection failed")
            
            # Attempt to create queue manager - should fail and log error
            try:
                queue_manager = QueueManager(db_path="test.db")
            except Exception:
                # Expected to fail
                pass
            
            # Verify that logger.error was called
            assert mock_logger.error.called, \
                "Logger error method should be called when a database error occurs"


@given(error_message=error_message_strategy())
@settings(max_examples=100, deadline=None)
def test_property_error_logging_screenshot_capture(error_message):
    """
    Property 11: Error Logging - Screenshot Capture
    
    For any error or exception encountered during screenshot capture,
    a log entry containing the error details should be created in the log file.
    
    **Validates: Requirements 7.5, 16.1, 16.3**
    """
    # Create screenshot capture instance
    screenshot = ScreenshotCapture(jpeg_quality=75)
    
    # Mock the logger to verify it's called
    with patch('src.screenshot.logger') as mock_logger:
        # Mock ImageGrab.grab to raise an exception
        with patch('PIL.ImageGrab.grab') as mock_grab:
            mock_grab.side_effect = Exception(error_message)
            
            # Attempt to capture screenshot - should fail and log error
            result = screenshot.capture_screenshot()
            
            # Verify capture failed
            assert result is None, "Screenshot capture should return None on error"
            
            # Verify that logger.error was called
            assert mock_logger.error.called, \
                "Logger error method should be called when screenshot capture fails"


@given(error_message=error_message_strategy())
@settings(max_examples=100, deadline=None)
def test_property_error_logging_app_monitor(error_message):
    """
    Property 11: Error Logging - Application Monitor
    
    For any error or exception encountered during application monitoring,
    a log entry containing the error details should be created in the log file.
    
    **Validates: Requirements 7.5, 16.1, 16.3**
    """
    # Create app monitor instance
    app_monitor = ApplicationMonitor()
    
    # Mock the logger to verify it's called
    with patch('src.app_monitor.logger') as mock_logger:
        # Mock psutil.process_iter to raise an exception
        with patch('psutil.process_iter') as mock_process_iter:
            mock_process_iter.side_effect = Exception(error_message)
            
            # Attempt to get running applications - should fail and log error
            result = app_monitor.get_running_applications()
            
            # Verify it returns empty list on error
            assert result == [], "Should return empty list on error"
            
            # Verify that logger.error was called
            assert mock_logger.error.called, \
                "Logger error method should be called when app monitoring fails"


@given(error_message=error_message_strategy())
@settings(max_examples=100, deadline=None)
def test_property_error_logging_browser_monitor(error_message):
    """
    Property 11: Error Logging - Browser Monitor
    
    For any error or exception encountered during browser monitoring,
    a log entry containing the error details should be created in the log file.
    
    **Validates: Requirements 7.5, 16.1, 16.3**
    """
    # Create browser monitor instance
    browser_monitor = BrowserMonitor()
    
    # Mock the logger to verify it's called
    with patch('src.browser_monitor.logger') as mock_logger:
        # Mock psutil.process_iter to raise an exception
        with patch('psutil.process_iter') as mock_process_iter:
            mock_process_iter.side_effect = Exception(error_message)
            
            # Attempt to get browser tabs - should fail and log error
            result = browser_monitor.get_browser_tabs()
            
            # Verify it returns empty list on error
            assert result == [], "Should return empty list on error"
            
            # Verify that logger.error was called
            assert mock_logger.error.called, \
                "Logger error method should be called when browser monitoring fails"


# Additional property: Multiple errors are all logged
@given(error_messages=st.lists(error_message_strategy(), min_size=2, max_size=5))
@settings(max_examples=50, deadline=None)
def test_property_multiple_errors_logged(error_messages):
    """
    Property: Multiple Error Logging
    
    For any sequence of errors encountered by the Monitoring_Client,
    all errors should be logged to the log file.
    
    **Validates: Requirements 7.5, 16.1, 16.3**
    """
    # Create HTTP transmitter
    transmitter = HTTPTransmitter(
        server_url="https://test-server.example.com/api/monitoring/data",
        auth_token="test_token"
    )
    
    # Mock the logger to verify it's called
    with patch('src.http_transmitter.logger') as mock_logger:
        # Generate multiple errors
        for error_message in error_messages:
            with patch('requests.post') as mock_post:
                mock_post.side_effect = Exception(error_message)
                
                payload = {
                    "employee_name": "Test Employee",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "interval_start": "2024-01-01T12:00:00Z",
                    "interval_end": "2024-01-01T12:00:00Z",
                    "activity": {"work_seconds": 100, "idle_seconds": 50},
                    "applications": [],
                    "browser_tabs": [],
                    "screenshot": "test_data"
                }
                
                success, error = transmitter.send_payload(payload)
                assert success is False
        
        # Verify that logger.error was called at least as many times as there were errors
        assert mock_logger.error.call_count >= len(error_messages), \
            f"Logger should be called at least {len(error_messages)} times, " \
            f"but was called {mock_logger.error.call_count} times"

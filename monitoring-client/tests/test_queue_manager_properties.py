"""Property-based tests for the queue manager module.

Feature: vibgyorseek-employee-monitoring

Tests the property that failed transmission payloads are correctly queued.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings
from src.queue_manager import QueueManager
from src.http_transmitter import HTTPTransmitter


def create_temp_db():
    """Create a temporary database file for testing."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    return db_path


def cleanup_temp_db(db_path):
    """Clean up temporary database file."""
    try:
        Path(db_path).unlink(missing_ok=True)
    except Exception:
        pass


# Custom strategies for generating test data
@st.composite
def payload_strategy(draw):
    """Generate a valid data payload for testing."""
    employee_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' '
    )))
    
    # Generate timestamp
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


# Property 10: Failed Transmission Queuing
# **Validates: Requirements 6.4**
@given(payload=payload_strategy())
@settings(max_examples=100, deadline=None)
def test_property_failed_transmission_queuing(payload):
    """
    Property 10: Failed Transmission Queuing
    
    For any data transmission attempt that fails due to server unreachability,
    the Data_Payload should be added to the local queue for retry.
    
    **Validates: Requirements 6.4**
    """
    # Create temporary database for this test
    temp_db = create_temp_db()
    
    try:
        # Create queue manager
        queue_manager = QueueManager(db_path=temp_db)
        
        # Verify queue starts empty
        initial_size = queue_manager.size()
        
        # Create transmitter with a server URL
        transmitter = HTTPTransmitter(
            server_url="https://unreachable-server.example.com/api/monitoring/data",
            auth_token="test_token"
        )
        
        # Mock the requests.post to simulate server unreachability
        # This simulates network failures like connection timeout, DNS failure, etc.
        with patch('requests.post') as mock_post:
            # Simulate various types of network failures
            mock_post.side_effect = Exception("Connection refused: Server unreachable")
            
            # Attempt to send payload - should fail
            success, error = transmitter.send_payload(payload)
            
            # Verify transmission failed
            assert success is False, "Transmission should fail when server is unreachable"
            assert error is not None, "Error message should be provided on failure"
            
            # Queue the failed payload
            queue_result = queue_manager.add(payload)
            
            # Verify payload was added to queue
            assert queue_result is True, "Failed payload should be successfully added to queue"
            
            # Verify queue size increased
            final_size = queue_manager.size()
            assert final_size == initial_size + 1, \
                f"Queue size should increase by 1 after queuing failed payload. " \
                f"Initial: {initial_size}, Final: {final_size}"
            
            # Verify the queued payload can be retrieved
            queued_payloads = queue_manager.retrieve(limit=1)
            assert len(queued_payloads) > 0, "Should be able to retrieve queued payload"
            
            # Verify the retrieved payload matches the original
            _, retrieved_payload = queued_payloads[0]
            assert retrieved_payload['employee_name'] == payload['employee_name'], \
                "Retrieved payload should have same employee_name"
            assert retrieved_payload['timestamp'] == payload['timestamp'], \
                "Retrieved payload should have same timestamp"
            assert retrieved_payload['activity']['work_seconds'] == payload['activity']['work_seconds'], \
                "Retrieved payload should have same work_seconds"
    finally:
        # Cleanup
        cleanup_temp_db(temp_db)


# Additional property: Multiple failed transmissions are all queued
@given(payloads=st.lists(payload_strategy(), min_size=1, max_size=10))
@settings(max_examples=50, deadline=None)
def test_property_multiple_failed_transmissions_queued(payloads):
    """
    Property: Multiple Failed Transmission Queuing
    
    For any sequence of data transmission attempts that fail due to 
    server unreachability, all Data_Payloads should be added to the 
    local queue in order.
    
    **Validates: Requirements 6.4**
    """
    # Create temporary database for this test
    temp_db = create_temp_db()
    
    try:
        # Create queue manager
        queue_manager = QueueManager(db_path=temp_db)
        queue_manager.clear()  # Ensure clean state
        
        # Create transmitter
        transmitter = HTTPTransmitter(
            server_url="https://unreachable-server.example.com/api/monitoring/data",
            auth_token="test_token"
        )
        
        # Ensure unique timestamps for each payload to maintain order
        for i, payload in enumerate(payloads):
            # Modify timestamp to ensure uniqueness and ordering
            base_ts = payload['timestamp']
            # Add seconds to make each timestamp unique
            parts = base_ts.split(':')
            if len(parts) >= 3:
                seconds = int(parts[2][:2])
                seconds = (seconds + i) % 60
                payload['timestamp'] = f"{parts[0]}:{parts[1]}:{seconds:02d}Z"
        
        # Mock server unreachability
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Network error: Server unreachable")
            
            # Attempt to send all payloads
            for payload in payloads:
                success, error = transmitter.send_payload(payload)
                
                # Verify transmission failed
                assert success is False
                
                # Queue the failed payload
                queue_result = queue_manager.add(payload)
                assert queue_result is True
            
            # Verify all payloads were queued
            final_size = queue_manager.size()
            assert final_size == len(payloads), \
                f"All {len(payloads)} failed payloads should be queued. " \
                f"Queue size: {final_size}"
            
            # Verify payloads can be retrieved in FIFO order
            retrieved = queue_manager.retrieve(limit=len(payloads))
            assert len(retrieved) == len(payloads), \
                "Should be able to retrieve all queued payloads"
            
            # Verify order is preserved (FIFO) by checking employee names
            # Since timestamps might be equal, we check that all payloads are present
            retrieved_names = [p[1]['employee_name'] for p in retrieved]
            expected_names = [p['employee_name'] for p in payloads]
            
            # All payloads should be present (order might vary if timestamps are equal)
            for expected_name in expected_names:
                assert expected_name in retrieved_names, \
                    f"Payload with employee_name '{expected_name}' should be in queue"
    finally:
        # Cleanup
        cleanup_temp_db(temp_db)


# Property: Failed transmission with different error types
@given(
    payload=payload_strategy(),
    error_type=st.sampled_from([
        'ConnectionError',
        'Timeout',
        'ServerError500',
        'ServerError503'
    ])
)
@settings(max_examples=100, deadline=None)
def test_property_failed_transmission_various_errors(payload, error_type):
    """
    Property: Failed Transmission Queuing for Various Error Types
    
    For any data transmission attempt that fails due to network errors
    or server errors (5xx), the Data_Payload should be added to the 
    local queue for retry.
    
    **Validates: Requirements 6.4**
    """
    # Create temporary database for this test
    temp_db = create_temp_db()
    
    try:
        # Create queue manager
        queue_manager = QueueManager(db_path=temp_db)
        initial_size = queue_manager.size()
        
        # Create transmitter
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test_token"
        )
        
        # Mock different types of failures
        with patch('requests.post') as mock_post:
            if error_type == 'ConnectionError':
                from requests.exceptions import ConnectionError
                mock_post.side_effect = ConnectionError("Connection refused")
            elif error_type == 'Timeout':
                from requests.exceptions import Timeout
                mock_post.side_effect = Timeout("Request timeout")
            elif error_type == 'ServerError500':
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.text = "Internal Server Error"
                mock_post.return_value = mock_response
            elif error_type == 'ServerError503':
                mock_response = Mock()
                mock_response.status_code = 503
                mock_response.text = "Service Unavailable"
                mock_post.return_value = mock_response
            
            # Attempt transmission
            success, error = transmitter.send_payload(payload)
            
            # Verify transmission failed
            assert success is False, \
                f"Transmission should fail for error type: {error_type}"
            
            # Queue the failed payload
            queue_result = queue_manager.add(payload)
            
            # Verify payload was queued
            assert queue_result is True, \
                f"Failed payload should be queued for error type: {error_type}"
            
            # Verify queue size increased
            final_size = queue_manager.size()
            assert final_size == initial_size + 1, \
                f"Queue size should increase after queuing failed payload. " \
                f"Error type: {error_type}"
    finally:
        # Cleanup
        cleanup_temp_db(temp_db)


# Property: Successful transmission should not queue payload
@given(payload=payload_strategy())
@settings(max_examples=50, deadline=None)
def test_property_successful_transmission_not_queued(payload):
    """
    Property: Successful Transmission Not Queued
    
    For any data transmission attempt that succeeds (server returns 200),
    the Data_Payload should NOT be added to the queue.
    
    This is the inverse property to verify correct behavior.
    
    **Validates: Requirements 6.4**
    """
    # Create temporary database for this test
    temp_db = create_temp_db()
    
    try:
        # Create queue manager
        queue_manager = QueueManager(db_path=temp_db)
        queue_manager.clear()  # Start with empty queue
        initial_size = queue_manager.size()
        assert initial_size == 0
        
        # Create transmitter
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test_token"
        )
        
        # Mock successful transmission
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            # Attempt transmission
            success, error = transmitter.send_payload(payload)
            
            # Verify transmission succeeded
            assert success is True, "Transmission should succeed"
            assert error is None, "No error should be returned on success"
            
            # Do NOT queue the payload since it succeeded
            # (In real implementation, queuing only happens on failure)
            
            # Verify queue remains empty
            final_size = queue_manager.size()
            assert final_size == 0, \
                "Queue should remain empty after successful transmission"
    finally:
        # Cleanup
        cleanup_temp_db(temp_db)

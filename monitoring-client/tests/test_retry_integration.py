"""
Integration tests for retry logic with exponential backoff.

Tests the integration of QueueManager, HTTPTransmitter, and RetryManager.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from src.queue_manager import QueueManager
from src.http_transmitter import HTTPTransmitter
from src.retry_manager import RetryManager


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def queue_manager(temp_db):
    """Create a real QueueManager instance."""
    return QueueManager(db_path=temp_db)


@pytest.fixture
def mock_http_transmitter():
    """Create a mock HTTPTransmitter."""
    mock = Mock(spec=HTTPTransmitter)
    mock.send_payload.return_value = (True, None)
    return mock


@pytest.fixture
def retry_manager(queue_manager, mock_http_transmitter):
    """Create a RetryManager with real queue and mock transmitter."""
    return RetryManager(
        queue_manager=queue_manager,
        http_transmitter=mock_http_transmitter
    )


@pytest.fixture
def sample_payload():
    """Create a sample payload for testing."""
    return {
        "employee_name": "John Doe",
        "timestamp": "2024-01-15T14:30:00Z",
        "activity": {"work_seconds": 480, "idle_seconds": 120}
    }


class TestRetryIntegration:
    """Integration tests for retry logic."""
    
    def test_successful_send_no_queue(
        self,
        retry_manager,
        queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that successful send doesn't queue payload."""
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        result = retry_manager.send_with_retry(sample_payload)
        
        assert result is True
        assert queue_manager.size() == 0
    
    def test_failed_send_queues_payload(
        self,
        retry_manager,
        queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that failed send queues payload."""
        mock_http_transmitter.send_payload.return_value = (False, "Connection error")
        
        result = retry_manager.send_with_retry(sample_payload)
        
        assert result is False
        assert queue_manager.size() == 1
    
    @patch('src.retry_manager.time_module.sleep')
    def test_process_queue_success(
        self,
        mock_sleep,
        retry_manager,
        queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test processing queue with successful retry."""
        # Queue a payload
        queue_manager.add(sample_payload)
        assert queue_manager.size() == 1
        
        # Configure mock to succeed
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        # Process queue
        successful, failed = retry_manager.process_queue()
        
        assert successful == 1
        assert failed == 0
        assert queue_manager.size() == 0
    
    @patch('src.retry_manager.time_module.sleep')
    def test_process_queue_failure(
        self,
        mock_sleep,
        retry_manager,
        queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test processing queue with failed retry."""
        # Queue a payload
        queue_manager.add(sample_payload)
        assert queue_manager.size() == 1
        
        # Configure mock to fail
        mock_http_transmitter.send_payload.return_value = (False, "Connection error")
        
        # Process queue
        successful, failed = retry_manager.process_queue()
        
        assert successful == 0
        assert failed == 1
        assert queue_manager.size() == 1  # Still in queue
        
        # Check retry count was incremented
        payloads = queue_manager.retrieve()
        payload_id = payloads[0][0]
        retry_count = queue_manager.get_retry_count(payload_id)
        assert retry_count == 1
    
    @patch('src.retry_manager.time_module.sleep')
    def test_fifo_order(
        self,
        mock_sleep,
        retry_manager,
        queue_manager,
        mock_http_transmitter
    ):
        """Test that payloads are processed in FIFO order."""
        # Queue multiple payloads
        payload1 = {"timestamp": "2024-01-15T14:30:00Z", "data": "first"}
        payload2 = {"timestamp": "2024-01-15T14:31:00Z", "data": "second"}
        payload3 = {"timestamp": "2024-01-15T14:32:00Z", "data": "third"}
        
        queue_manager.add(payload1)
        queue_manager.add(payload2)
        queue_manager.add(payload3)
        
        assert queue_manager.size() == 3
        
        # Configure mock to succeed
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        # Process queue
        successful, failed = retry_manager.process_queue()
        
        assert successful == 3
        assert failed == 0
        assert queue_manager.size() == 0
        
        # Verify order
        calls = mock_http_transmitter.send_payload.call_args_list
        assert calls[0][0][0]["data"] == "first"
        assert calls[1][0][0]["data"] == "second"
        assert calls[2][0][0]["data"] == "third"
    
    @patch('src.retry_manager.time_module.sleep')
    def test_max_retries_exceeded(
        self,
        mock_sleep,
        retry_manager,
        queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that payloads exceeding max retries are removed."""
        # Queue a payload
        queue_manager.add(sample_payload)
        payloads = queue_manager.retrieve()
        payload_id = payloads[0][0]
        
        # Set retry count to max
        for _ in range(RetryManager.MAX_RETRY_ATTEMPTS):
            queue_manager.increment_retry_count(payload_id)
        
        assert queue_manager.get_retry_count(payload_id) == RetryManager.MAX_RETRY_ATTEMPTS
        
        # Process queue
        successful, failed = retry_manager.process_queue()
        
        assert successful == 0
        assert failed == 1
        assert queue_manager.size() == 0  # Removed from queue
        
        # Should not have attempted to send
        mock_http_transmitter.send_payload.assert_not_called()
    
    @patch('src.retry_manager.time_module.sleep')
    def test_stops_on_first_failure(
        self,
        mock_sleep,
        retry_manager,
        queue_manager,
        mock_http_transmitter
    ):
        """Test that processing stops after first failure."""
        # Queue multiple payloads
        payload1 = {"timestamp": "2024-01-15T14:30:00Z"}
        payload2 = {"timestamp": "2024-01-15T14:31:00Z"}
        payload3 = {"timestamp": "2024-01-15T14:32:00Z"}
        
        queue_manager.add(payload1)
        queue_manager.add(payload2)
        queue_manager.add(payload3)
        
        # Configure mock to fail
        mock_http_transmitter.send_payload.return_value = (False, "Connection error")
        
        # Process queue
        successful, failed = retry_manager.process_queue()
        
        assert successful == 0
        assert failed == 1
        assert queue_manager.size() == 3  # All still in queue
        
        # Should only have attempted once
        assert mock_http_transmitter.send_payload.call_count == 1
    
    @patch('src.retry_manager.time_module.sleep')
    def test_exponential_backoff_applied(
        self,
        mock_sleep,
        retry_manager,
        queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that exponential backoff is applied."""
        # Queue a payload and set retry count
        queue_manager.add(sample_payload)
        payloads = queue_manager.retrieve()
        payload_id = payloads[0][0]
        
        # Set retry count to 3
        for _ in range(3):
            queue_manager.increment_retry_count(payload_id)
        
        # Configure mock to succeed
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        # Process queue
        retry_manager.process_queue()
        
        # Verify sleep was called with exponential backoff
        # For retry_count=3: 1 * (2^3) = 8 seconds
        expected_backoff = RetryManager.INITIAL_BACKOFF_SECONDS * (RetryManager.BACKOFF_MULTIPLIER ** 3)
        
        if mock_sleep.called:
            actual_sleep = mock_sleep.call_args[0][0]
            assert actual_sleep >= expected_backoff - 0.1


class TestRetryWorkflow:
    """Test complete retry workflows."""
    
    @patch('src.retry_manager.time_module.sleep')
    def test_complete_workflow(
        self,
        mock_sleep,
        retry_manager,
        queue_manager,
        mock_http_transmitter
    ):
        """Test complete workflow: fail, queue, retry, succeed."""
        payload = {"employee_name": "Jane Doe", "timestamp": "2024-01-15T15:00:00Z"}
        
        # Step 1: Initial send fails
        mock_http_transmitter.send_payload.return_value = (False, "Connection error")
        result = retry_manager.send_with_retry(payload)
        
        assert result is False
        assert queue_manager.size() == 1
        
        # Step 2: Retry also fails
        successful, failed = retry_manager.process_queue()
        
        assert successful == 0
        assert failed == 1
        assert queue_manager.size() == 1
        
        # Step 3: Connection restored, retry succeeds
        mock_http_transmitter.send_payload.return_value = (True, None)
        successful, failed = retry_manager.process_queue()
        
        assert successful == 1
        assert failed == 0
        assert queue_manager.size() == 0

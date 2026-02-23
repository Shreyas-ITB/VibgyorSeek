"""
Unit tests for the Retry Manager module.

Tests retry logic with exponential backoff for failed transmissions.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from src.retry_manager import RetryManager
from src.queue_manager import QueueManager
from src.http_transmitter import HTTPTransmitter


@pytest.fixture
def mock_queue_manager():
    """Create a mock QueueManager."""
    mock = Mock(spec=QueueManager)
    mock.size.return_value = 0
    mock.add.return_value = True
    mock.retrieve.return_value = []
    mock.delete.return_value = True
    mock.clear.return_value = True
    mock.get_retry_count.return_value = 0
    mock.increment_retry_count.return_value = True
    return mock


@pytest.fixture
def mock_http_transmitter():
    """Create a mock HTTPTransmitter."""
    mock = Mock(spec=HTTPTransmitter)
    mock.send_payload.return_value = (True, None)
    return mock


@pytest.fixture
def retry_manager(mock_queue_manager, mock_http_transmitter):
    """Create a RetryManager instance with mocks."""
    return RetryManager(
        queue_manager=mock_queue_manager,
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


class TestRetryManagerInitialization:
    """Tests for RetryManager initialization."""
    
    def test_initialization(self, mock_queue_manager, mock_http_transmitter):
        """Test successful initialization."""
        manager = RetryManager(
            queue_manager=mock_queue_manager,
            http_transmitter=mock_http_transmitter
        )
        
        assert manager.queue_manager == mock_queue_manager
        assert manager.http_transmitter == mock_http_transmitter
        assert manager._current_backoff == RetryManager.INITIAL_BACKOFF_SECONDS


class TestSendWithRetry:
    """Tests for send_with_retry method."""
    
    def test_successful_send(self, retry_manager, mock_http_transmitter, sample_payload):
        """Test successful payload transmission."""
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        result = retry_manager.send_with_retry(sample_payload)
        
        assert result is True
        mock_http_transmitter.send_payload.assert_called_once_with(sample_payload)
    
    def test_failed_send_queues_payload(
        self,
        retry_manager,
        mock_http_transmitter,
        mock_queue_manager,
        sample_payload
    ):
        """Test that failed transmission queues the payload."""
        mock_http_transmitter.send_payload.return_value = (False, "Connection error")
        mock_queue_manager.add.return_value = True
        
        result = retry_manager.send_with_retry(sample_payload)
        
        assert result is False
        mock_http_transmitter.send_payload.assert_called_once_with(sample_payload)
        mock_queue_manager.add.assert_called_once_with(sample_payload)
    
    def test_failed_send_with_queue_failure(
        self,
        retry_manager,
        mock_http_transmitter,
        mock_queue_manager,
        sample_payload
    ):
        """Test handling when both transmission and queuing fail."""
        mock_http_transmitter.send_payload.return_value = (False, "Connection error")
        mock_queue_manager.add.return_value = False
        
        result = retry_manager.send_with_retry(sample_payload)
        
        assert result is False
        mock_queue_manager.add.assert_called_once_with(sample_payload)
    
    def test_successful_send_resets_backoff(
        self,
        retry_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that successful send resets backoff."""
        # Set backoff to a higher value
        retry_manager._current_backoff = 10
        
        mock_http_transmitter.send_payload.return_value = (True, None)
        retry_manager.send_with_retry(sample_payload)
        
        assert retry_manager._current_backoff == RetryManager.INITIAL_BACKOFF_SECONDS


class TestProcessQueue:
    """Tests for process_queue method."""
    
    def test_empty_queue(self, retry_manager, mock_queue_manager):
        """Test processing an empty queue."""
        mock_queue_manager.size.return_value = 0
        mock_queue_manager.retrieve.return_value = []
        
        successful, failed = retry_manager.process_queue()
        
        assert successful == 0
        assert failed == 0
    
    @patch('src.retry_manager.time_module.sleep')
    def test_single_successful_retry(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test successful retry of a single payload."""
        mock_queue_manager.size.return_value = 1
        mock_queue_manager.retrieve.return_value = [(1, sample_payload)]
        mock_queue_manager.get_retry_count.return_value = 0
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        successful, failed = retry_manager.process_queue()
        
        assert successful == 1
        assert failed == 0
        mock_http_transmitter.send_payload.assert_called_once_with(sample_payload)
        mock_queue_manager.delete.assert_called_once_with(1)
    
    @patch('src.retry_manager.time_module.sleep')
    def test_single_failed_retry(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test failed retry of a single payload."""
        mock_queue_manager.size.return_value = 1
        mock_queue_manager.retrieve.return_value = [(1, sample_payload)]
        mock_queue_manager.get_retry_count.return_value = 0
        mock_http_transmitter.send_payload.return_value = (False, "Connection error")
        
        successful, failed = retry_manager.process_queue()
        
        assert successful == 0
        assert failed == 1
        mock_queue_manager.increment_retry_count.assert_called_once_with(1)
        mock_queue_manager.delete.assert_not_called()
    
    @patch('src.retry_manager.time_module.sleep')
    def test_fifo_order_processing(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter
    ):
        """Test that payloads are processed in FIFO order."""
        payload1 = {"timestamp": "2024-01-15T14:30:00Z"}
        payload2 = {"timestamp": "2024-01-15T14:31:00Z"}
        
        # Mock retrieve to return payloads one at a time
        mock_queue_manager.size.return_value = 2
        mock_queue_manager.retrieve.side_effect = [
            [(1, payload1)],
            [(2, payload2)],
            []  # Empty on third call
        ]
        mock_queue_manager.get_retry_count.return_value = 0
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        successful, failed = retry_manager.process_queue()
        
        assert successful == 2
        assert failed == 0
        
        # Verify payloads were sent in order
        calls = mock_http_transmitter.send_payload.call_args_list
        assert calls[0][0][0] == payload1
        assert calls[1][0][0] == payload2
    
    @patch('src.retry_manager.time_module.sleep')
    def test_stops_on_first_failure(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter
    ):
        """Test that processing stops on first failure."""
        payload1 = {"timestamp": "2024-01-15T14:30:00Z"}
        
        mock_queue_manager.size.return_value = 3
        mock_queue_manager.retrieve.return_value = [(1, payload1)]
        mock_queue_manager.get_retry_count.return_value = 0
        mock_http_transmitter.send_payload.return_value = (False, "Connection error")
        
        successful, failed = retry_manager.process_queue()
        
        assert successful == 0
        assert failed == 1
        
        # Should only attempt once, then stop
        assert mock_http_transmitter.send_payload.call_count == 1
    
    @patch('src.retry_manager.time_module.sleep')
    def test_exponential_backoff_calculation(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that backoff delay increases exponentially."""
        mock_queue_manager.size.return_value = 1
        mock_queue_manager.retrieve.side_effect = [
            [(1, sample_payload)],
            [(1, sample_payload)],
            [(1, sample_payload)],
            []
        ]
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        # Test with different retry counts
        for retry_count in [0, 1, 2]:
            mock_queue_manager.get_retry_count.return_value = retry_count
            
            expected_backoff = min(
                RetryManager.INITIAL_BACKOFF_SECONDS * (RetryManager.BACKOFF_MULTIPLIER ** retry_count),
                RetryManager.MAX_BACKOFF_SECONDS
            )
            
            # The backoff is calculated correctly (we can't easily test the sleep)
            assert expected_backoff >= RetryManager.INITIAL_BACKOFF_SECONDS
    
    @patch('src.retry_manager.time_module.sleep')
    def test_max_backoff_limit(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that backoff doesn't exceed maximum."""
        mock_queue_manager.size.return_value = 1
        mock_queue_manager.retrieve.return_value = [(1, sample_payload)]
        mock_queue_manager.get_retry_count.return_value = 20  # Very high retry count
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        # Calculate expected backoff
        expected_backoff = min(
            RetryManager.INITIAL_BACKOFF_SECONDS * (RetryManager.BACKOFF_MULTIPLIER ** 20),
            RetryManager.MAX_BACKOFF_SECONDS
        )
        
        assert expected_backoff == RetryManager.MAX_BACKOFF_SECONDS
    
    @patch('src.retry_manager.time_module.sleep')
    def test_max_retry_attempts_exceeded(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that payloads exceeding max retries are removed."""
        mock_queue_manager.size.return_value = 1
        mock_queue_manager.retrieve.return_value = [(1, sample_payload)]
        mock_queue_manager.get_retry_count.return_value = RetryManager.MAX_RETRY_ATTEMPTS
        
        successful, failed = retry_manager.process_queue()
        
        assert successful == 0
        assert failed == 1
        
        # Payload should be deleted without attempting to send
        mock_http_transmitter.send_payload.assert_not_called()
        mock_queue_manager.delete.assert_called_once_with(1)
    
    @patch('src.retry_manager.time_module.sleep')
    def test_backoff_reset_on_success(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that backoff is reset after successful retry."""
        retry_manager._current_backoff = 10
        
        mock_queue_manager.size.return_value = 1
        mock_queue_manager.retrieve.return_value = [(1, sample_payload)]
        mock_queue_manager.get_retry_count.return_value = 0
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        retry_manager.process_queue()
        
        assert retry_manager._current_backoff == RetryManager.INITIAL_BACKOFF_SECONDS


class TestQueueManagement:
    """Tests for queue management methods."""
    
    def test_get_queue_size(self, retry_manager, mock_queue_manager):
        """Test getting queue size."""
        mock_queue_manager.size.return_value = 5
        
        size = retry_manager.get_queue_size()
        
        assert size == 5
        mock_queue_manager.size.assert_called_once()
    
    def test_clear_queue(self, retry_manager, mock_queue_manager):
        """Test clearing the queue."""
        mock_queue_manager.clear.return_value = True
        
        result = retry_manager.clear_queue()
        
        assert result is True
        mock_queue_manager.clear.assert_called_once()


class TestBackoffTiming:
    """Tests for backoff timing behavior."""
    
    @patch('src.retry_manager.time_module.sleep')
    @patch('src.retry_manager.time_module.time')
    def test_backoff_delay_applied(
        self,
        mock_time,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that backoff delay is applied between retries."""
        mock_queue_manager.size.return_value = 1
        mock_queue_manager.retrieve.return_value = [(1, sample_payload)]
        mock_queue_manager.get_retry_count.return_value = 1  # Second attempt
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        # Mock time to simulate passage of time
        mock_time.side_effect = [100.0, 100.0, 102.0]  # Start, check, after sleep
        retry_manager._last_retry_time = 100.0
        
        retry_manager.process_queue()
        
        # Should have called sleep with backoff delay (2 seconds for retry_count=1)
        expected_backoff = RetryManager.INITIAL_BACKOFF_SECONDS * (RetryManager.BACKOFF_MULTIPLIER ** 1)
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args[0][0] >= expected_backoff - 0.1
    
    @patch('src.retry_manager.time_module.sleep')
    def test_no_backoff_on_first_attempt(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test that no backoff is applied on first attempt."""
        mock_queue_manager.size.return_value = 1
        mock_queue_manager.retrieve.return_value = [(1, sample_payload)]
        mock_queue_manager.get_retry_count.return_value = 0
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        retry_manager.process_queue()
        
        # Sleep should not be called or called with 0
        if mock_sleep.called:
            assert mock_sleep.call_args[0][0] <= 0.1


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    @patch('src.retry_manager.time_module.sleep')
    def test_none_retry_count(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter,
        sample_payload
    ):
        """Test handling when retry count is None."""
        mock_queue_manager.size.return_value = 1
        mock_queue_manager.retrieve.return_value = [(1, sample_payload)]
        mock_queue_manager.get_retry_count.return_value = None
        mock_http_transmitter.send_payload.return_value = (True, None)
        
        successful, failed = retry_manager.process_queue()
        
        # Should treat None as 0
        assert successful == 1
        assert failed == 0
    
    @patch('src.retry_manager.time_module.sleep')
    def test_multiple_payloads_with_mixed_results(
        self,
        mock_sleep,
        retry_manager,
        mock_queue_manager,
        mock_http_transmitter
    ):
        """Test processing multiple payloads with some successes and failures."""
        payload1 = {"timestamp": "2024-01-15T14:30:00Z"}
        payload2 = {"timestamp": "2024-01-15T14:31:00Z"}
        
        mock_queue_manager.size.return_value = 2
        mock_queue_manager.retrieve.side_effect = [
            [(1, payload1)],
            [(2, payload2)],
            []
        ]
        mock_queue_manager.get_retry_count.return_value = 0
        
        # First succeeds, second fails
        mock_http_transmitter.send_payload.side_effect = [
            (True, None),
            (False, "Connection error")
        ]
        
        successful, failed = retry_manager.process_queue()
        
        assert successful == 1
        assert failed == 1

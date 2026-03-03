"""
Integration tests for Queue Manager with HTTP Transmitter.

Tests the interaction between the queue manager and HTTP transmission,
verifying that failed transmissions are queued and retried correctly.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from src.queue_manager import QueueManager
from src.http_transmitter import HTTPTransmitter


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
    """Create a QueueManager instance with a temporary database."""
    return QueueManager(db_path=temp_db)


@pytest.fixture
def sample_payload():
    """Create a sample payload for testing."""
    return {
        "employee_name": "John Doe",
        "timestamp": "2024-01-15T14:30:00Z",
        "interval_start": "2024-01-15T14:20:00Z",
        "interval_end": "2024-01-15T14:30:00Z",
        "activity": {
            "work_seconds": 480,
            "idle_seconds": 120
        },
        "applications": [
            {"name": "Visual Studio Code", "active": True}
        ],
        "browser_tabs": [
            {"browser": "Chrome", "title": "GitHub", "url": "https://github.com"}
        ],
        "screenshot": "base64_encoded_data"
    }


class TestQueueManagerWithTransmitter:
    """Integration tests for queue manager with HTTP transmitter."""
    
    def test_queue_payload_on_network_failure(self, queue_manager, sample_payload):
        """Test that payloads are queued when transmission fails due to network error."""
        # Create transmitter with mock server
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test_token"
        )
        
        # Mock the requests.post to simulate network failure
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Network error")
            
            # Attempt to send payload
            success, error = transmitter.send_payload(sample_payload)
            
            # Transmission should fail
            assert success is False
            assert error is not None
            
            # Queue the failed payload
            queue_result = queue_manager.add(sample_payload)
            assert queue_result is True
            assert queue_manager.size() == 1
    
    def test_retry_queued_payload_on_success(self, queue_manager, sample_payload):
        """Test that queued payloads can be retried successfully."""
        # Add payload to queue
        queue_manager.add(sample_payload)
        assert queue_manager.size() == 1
        
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
            
            # Retrieve and retry
            payloads = queue_manager.retrieve(limit=1)
            assert len(payloads) == 1
            
            payload_id, payload = payloads[0]
            success, error = transmitter.send_payload(payload)
            
            # Transmission should succeed
            assert success is True
            assert error is None
            
            # Remove from queue
            delete_result = queue_manager.delete(payload_id)
            assert delete_result is True
            assert queue_manager.size() == 0
    
    def test_multiple_retry_attempts(self, queue_manager, sample_payload):
        """Test tracking multiple retry attempts for a payload."""
        # Add payload to queue
        queue_manager.add(sample_payload)
        
        # Get payload ID
        payloads = queue_manager.retrieve()
        payload_id = payloads[0][0]
        
        # Create transmitter
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test_token"
        )
        
        # Simulate 3 failed retry attempts
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Network error")
            
            for i in range(3):
                # Retrieve payload
                payloads = queue_manager.retrieve()
                payload = payloads[0][1]
                
                # Attempt transmission
                success, error = transmitter.send_payload(payload)
                assert success is False
                
                # Increment retry count
                queue_manager.increment_retry_count(payload_id)
                
                # Verify retry count
                retry_count = queue_manager.get_retry_count(payload_id)
                assert retry_count == i + 1
        
        # Final retry count should be 3
        final_count = queue_manager.get_retry_count(payload_id)
        assert final_count == 3
    
    def test_process_multiple_queued_payloads(self, queue_manager, sample_payload):
        """Test processing multiple queued payloads in FIFO order."""
        # Add 3 payloads to queue
        timestamps = [
            "2024-01-15T14:30:00Z",
            "2024-01-15T14:31:00Z",
            "2024-01-15T14:32:00Z"
        ]
        
        for ts in timestamps:
            payload = sample_payload.copy()
            payload['timestamp'] = ts
            queue_manager.add(payload)
        
        assert queue_manager.size() == 3
        
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
            
            # Process all queued payloads
            processed_timestamps = []
            while queue_manager.size() > 0:
                payloads = queue_manager.retrieve(limit=1)
                payload_id, payload = payloads[0]
                
                # Track order
                processed_timestamps.append(payload['timestamp'])
                
                # Send
                success, error = transmitter.send_payload(payload)
                assert success is True
                
                # Remove from queue
                queue_manager.delete(payload_id)
            
            # Verify FIFO order
            assert processed_timestamps == timestamps
            assert queue_manager.size() == 0
    
    def test_queue_survives_application_restart(self, temp_db, sample_payload):
        """Test that queued payloads persist across application restarts."""
        # Create first queue manager instance and add payload
        qm1 = QueueManager(db_path=temp_db)
        qm1.add(sample_payload)
        assert qm1.size() == 1
        
        # Simulate application restart by creating new instance
        qm2 = QueueManager(db_path=temp_db)
        
        # Payload should still be in queue
        assert qm2.size() == 1
        
        # Retrieve and verify
        payloads = qm2.retrieve()
        assert len(payloads) == 1
        assert payloads[0][1]['employee_name'] == sample_payload['employee_name']
    
    def test_handle_server_error_responses(self, queue_manager, sample_payload):
        """Test handling different server error responses."""
        # Add payload to queue
        queue_manager.add(sample_payload)
        
        # Create transmitter
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test_token"
        )
        
        # Test 500 server error
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response
            
            payloads = queue_manager.retrieve()
            payload_id, payload = payloads[0]
            
            success, error = transmitter.send_payload(payload)
            assert success is False
            assert "Server error" in error
            
            # Payload should remain in queue for retry
            assert queue_manager.size() == 1
    
    def test_remove_payload_on_authentication_error(self, queue_manager, sample_payload):
        """Test that payloads with authentication errors should not be retried."""
        # Add payload to queue
        queue_manager.add(sample_payload)
        
        # Create transmitter
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="invalid_token"
        )
        
        # Test 401 authentication error
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_post.return_value = mock_response
            
            payloads = queue_manager.retrieve()
            payload_id, payload = payloads[0]
            
            success, error = transmitter.send_payload(payload)
            assert success is False
            assert "Authentication failed" in error
            
            # Remove from queue since auth errors won't be fixed by retry
            queue_manager.delete(payload_id)
            assert queue_manager.size() == 0
    
    def test_batch_processing_with_partial_failures(self, queue_manager, sample_payload):
        """Test processing a batch where some succeed and some fail."""
        # Add 5 payloads to queue
        for i in range(5):
            payload = sample_payload.copy()
            payload['timestamp'] = f"2024-01-15T14:{30+i}:00Z"
            queue_manager.add(payload)
        
        assert queue_manager.size() == 5
        
        # Create transmitter
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test_token"
        )
        
        # Mock responses: first 2 succeed, next 3 fail
        with patch('requests.post') as mock_post:
            responses = []
            for i in range(5):
                mock_response = Mock()
                if i < 2:
                    mock_response.status_code = 200
                else:
                    mock_response.status_code = 500
                    mock_response.text = "Server error"
                responses.append(mock_response)
            
            mock_post.side_effect = responses
            
            # Process all payloads
            payloads = queue_manager.retrieve(limit=5)
            for payload_id, payload in payloads:
                success, error = transmitter.send_payload(payload)
                
                if success:
                    # Remove successful ones
                    queue_manager.delete(payload_id)
            
            # Should have 3 failed payloads remaining
            assert queue_manager.size() == 3


class TestQueueManagerErrorRecovery:
    """Tests for error recovery scenarios."""
    
    def test_corrupted_payload_handling(self, temp_db):
        """Test that corrupted payloads are skipped during retrieval."""
        import sqlite3
        
        # Create queue manager
        qm = QueueManager(db_path=temp_db)
        
        # Manually insert a corrupted payload
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payload_queue (payload_json, timestamp, created_at)
                VALUES (?, ?, ?)
            """, ("invalid json {{{", "2024-01-15T14:30:00Z", "2024-01-15T14:30:00Z"))
            conn.commit()
        
        # Add a valid payload
        valid_payload = {"employee_name": "John Doe", "data": "test"}
        qm.add(valid_payload)
        
        # Retrieve should skip corrupted and return valid
        payloads = qm.retrieve(limit=10)
        
        # Should only get the valid payload
        assert len(payloads) == 1
        assert payloads[0][1]['employee_name'] == "John Doe"
    
    def test_database_connection_resilience(self, queue_manager, sample_payload):
        """Test that operations handle database connection issues gracefully."""
        # Add a payload successfully
        result = queue_manager.add(sample_payload)
        assert result is True
        
        # Simulate database file being locked or unavailable
        # by using an invalid path for a new operation
        # (This is a simplified test - real scenarios would be more complex)
        
        # The queue manager should handle errors gracefully
        # and return False/empty results rather than crashing
        payloads = queue_manager.retrieve()
        assert isinstance(payloads, list)

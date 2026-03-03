"""
Unit tests for the Queue Manager module.

Tests the SQLite-based queue for storing and retrieving failed transmission payloads.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from src.queue_manager import QueueManager


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


class TestQueueManagerInitialization:
    """Tests for QueueManager initialization."""
    
    def test_init_with_custom_path(self, temp_db):
        """Test initialization with a custom database path."""
        qm = QueueManager(db_path=temp_db)
        assert qm.db_path == Path(temp_db)
        assert qm.db_path.exists()
    
    def test_init_with_default_path(self):
        """Test initialization with default database path."""
        qm = QueueManager()
        assert qm.db_path == QueueManager.DEFAULT_DB_PATH
        # Cleanup
        qm.db_path.unlink(missing_ok=True)
        qm.db_path.parent.rmdir()
    
    def test_database_table_created(self, queue_manager, temp_db):
        """Test that the database table is created on initialization."""
        import sqlite3
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='payload_queue'
            """)
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'payload_queue'


class TestQueueManagerAdd:
    """Tests for adding payloads to the queue."""
    
    def test_add_valid_payload(self, queue_manager, sample_payload):
        """Test adding a valid payload to the queue."""
        result = queue_manager.add(sample_payload)
        assert result is True
        assert queue_manager.size() == 1
    
    def test_add_empty_payload(self, queue_manager):
        """Test that adding an empty payload fails."""
        result = queue_manager.add({})
        assert result is False
        assert queue_manager.size() == 0
    
    def test_add_none_payload(self, queue_manager):
        """Test that adding None fails."""
        result = queue_manager.add(None)
        assert result is False
        assert queue_manager.size() == 0
    
    def test_add_multiple_payloads(self, queue_manager, sample_payload):
        """Test adding multiple payloads to the queue."""
        for i in range(5):
            payload = sample_payload.copy()
            payload['timestamp'] = f"2024-01-15T14:{30+i}:00Z"
            result = queue_manager.add(payload)
            assert result is True
        
        assert queue_manager.size() == 5
    
    def test_add_payload_without_timestamp(self, queue_manager):
        """Test adding a payload without a timestamp field."""
        payload = {"employee_name": "Jane Doe", "data": "test"}
        result = queue_manager.add(payload)
        assert result is True
        assert queue_manager.size() == 1
    
    def test_add_when_queue_full(self, queue_manager, sample_payload):
        """Test that adding to a full queue removes the oldest payload."""
        # Fill the queue to max capacity
        original_max = QueueManager.MAX_QUEUE_SIZE
        QueueManager.MAX_QUEUE_SIZE = 3  # Temporarily set to small value
        
        try:
            # Add 3 payloads
            for i in range(3):
                payload = sample_payload.copy()
                payload['timestamp'] = f"2024-01-15T14:{30+i}:00Z"
                queue_manager.add(payload)
            
            assert queue_manager.size() == 3
            
            # Add one more - should remove oldest
            new_payload = sample_payload.copy()
            new_payload['timestamp'] = "2024-01-15T14:40:00Z"
            result = queue_manager.add(new_payload)
            
            assert result is True
            assert queue_manager.size() == 3  # Still at max
            
            # Verify oldest was removed (first one should be gone)
            payloads = queue_manager.retrieve(limit=3)
            timestamps = [p[1]['timestamp'] for p in payloads]
            assert "2024-01-15T14:30:00Z" not in timestamps
            assert "2024-01-15T14:40:00Z" in timestamps
        
        finally:
            QueueManager.MAX_QUEUE_SIZE = original_max


class TestQueueManagerRetrieve:
    """Tests for retrieving payloads from the queue."""
    
    def test_retrieve_from_empty_queue(self, queue_manager):
        """Test retrieving from an empty queue returns empty list."""
        result = queue_manager.retrieve()
        assert result == []
    
    def test_retrieve_single_payload(self, queue_manager, sample_payload):
        """Test retrieving a single payload."""
        queue_manager.add(sample_payload)
        
        result = queue_manager.retrieve()
        assert len(result) == 1
        
        payload_id, payload = result[0]
        assert isinstance(payload_id, int)
        assert payload['employee_name'] == sample_payload['employee_name']
        assert payload['timestamp'] == sample_payload['timestamp']
    
    def test_retrieve_multiple_payloads(self, queue_manager, sample_payload):
        """Test retrieving multiple payloads."""
        # Add 5 payloads
        for i in range(5):
            payload = sample_payload.copy()
            payload['timestamp'] = f"2024-01-15T14:{30+i}:00Z"
            queue_manager.add(payload)
        
        # Retrieve 3 payloads
        result = queue_manager.retrieve(limit=3)
        assert len(result) == 3
    
    def test_retrieve_fifo_order(self, queue_manager, sample_payload):
        """Test that payloads are retrieved in FIFO order."""
        timestamps = [
            "2024-01-15T14:30:00Z",
            "2024-01-15T14:31:00Z",
            "2024-01-15T14:32:00Z"
        ]
        
        # Add payloads
        for ts in timestamps:
            payload = sample_payload.copy()
            payload['timestamp'] = ts
            queue_manager.add(payload)
        
        # Retrieve all
        result = queue_manager.retrieve(limit=3)
        retrieved_timestamps = [p[1]['timestamp'] for p in result]
        
        assert retrieved_timestamps == timestamps
    
    def test_retrieve_does_not_remove(self, queue_manager, sample_payload):
        """Test that retrieve does not remove payloads from the queue."""
        queue_manager.add(sample_payload)
        
        # Retrieve
        result1 = queue_manager.retrieve()
        assert len(result1) == 1
        
        # Retrieve again - should still be there
        result2 = queue_manager.retrieve()
        assert len(result2) == 1
        
        # Queue size should still be 1
        assert queue_manager.size() == 1


class TestQueueManagerDelete:
    """Tests for deleting payloads from the queue."""
    
    def test_delete_existing_payload(self, queue_manager, sample_payload):
        """Test deleting an existing payload."""
        queue_manager.add(sample_payload)
        
        # Retrieve to get ID
        result = queue_manager.retrieve()
        payload_id = result[0][0]
        
        # Delete
        delete_result = queue_manager.delete(payload_id)
        assert delete_result is True
        assert queue_manager.size() == 0
    
    def test_delete_nonexistent_payload(self, queue_manager):
        """Test deleting a non-existent payload."""
        result = queue_manager.delete(99999)
        assert result is False
    
    def test_delete_multiple_payloads(self, queue_manager, sample_payload):
        """Test deleting multiple payloads."""
        # Add 3 payloads
        for i in range(3):
            payload = sample_payload.copy()
            payload['timestamp'] = f"2024-01-15T14:{30+i}:00Z"
            queue_manager.add(payload)
        
        assert queue_manager.size() == 3
        
        # Retrieve and delete all
        payloads = queue_manager.retrieve(limit=3)
        for payload_id, _ in payloads:
            result = queue_manager.delete(payload_id)
            assert result is True
        
        assert queue_manager.size() == 0


class TestQueueManagerSize:
    """Tests for getting queue size."""
    
    def test_size_empty_queue(self, queue_manager):
        """Test size of empty queue."""
        assert queue_manager.size() == 0
    
    def test_size_after_additions(self, queue_manager, sample_payload):
        """Test size after adding payloads."""
        for i in range(5):
            queue_manager.add(sample_payload)
            assert queue_manager.size() == i + 1
    
    def test_size_after_deletions(self, queue_manager, sample_payload):
        """Test size after deleting payloads."""
        # Add 3 payloads
        for _ in range(3):
            queue_manager.add(sample_payload)
        
        assert queue_manager.size() == 3
        
        # Delete one
        payloads = queue_manager.retrieve(limit=1)
        queue_manager.delete(payloads[0][0])
        
        assert queue_manager.size() == 2


class TestQueueManagerClear:
    """Tests for clearing the queue."""
    
    def test_clear_empty_queue(self, queue_manager):
        """Test clearing an empty queue."""
        result = queue_manager.clear()
        assert result is True
        assert queue_manager.size() == 0
    
    def test_clear_with_payloads(self, queue_manager, sample_payload):
        """Test clearing a queue with payloads."""
        # Add multiple payloads
        for i in range(5):
            queue_manager.add(sample_payload)
        
        assert queue_manager.size() == 5
        
        # Clear
        result = queue_manager.clear()
        assert result is True
        assert queue_manager.size() == 0


class TestQueueManagerRetryCount:
    """Tests for retry count functionality."""
    
    def test_increment_retry_count(self, queue_manager, sample_payload):
        """Test incrementing retry count."""
        queue_manager.add(sample_payload)
        
        # Get payload ID
        payloads = queue_manager.retrieve()
        payload_id = payloads[0][0]
        
        # Initial retry count should be 0
        count = queue_manager.get_retry_count(payload_id)
        assert count == 0
        
        # Increment
        result = queue_manager.increment_retry_count(payload_id)
        assert result is True
        
        # Check new count
        count = queue_manager.get_retry_count(payload_id)
        assert count == 1
    
    def test_increment_multiple_times(self, queue_manager, sample_payload):
        """Test incrementing retry count multiple times."""
        queue_manager.add(sample_payload)
        
        payloads = queue_manager.retrieve()
        payload_id = payloads[0][0]
        
        # Increment 3 times
        for i in range(3):
            queue_manager.increment_retry_count(payload_id)
        
        count = queue_manager.get_retry_count(payload_id)
        assert count == 3
    
    def test_get_retry_count_nonexistent(self, queue_manager):
        """Test getting retry count for non-existent payload."""
        count = queue_manager.get_retry_count(99999)
        assert count is None
    
    def test_increment_retry_count_nonexistent(self, queue_manager):
        """Test incrementing retry count for non-existent payload."""
        result = queue_manager.increment_retry_count(99999)
        assert result is False


class TestQueueManagerEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_payload_with_special_characters(self, queue_manager):
        """Test payload with special characters in JSON."""
        payload = {
            "employee_name": "José García",
            "data": "Special chars: \n\t\r",
            "unicode": "🎉 emoji test"
        }
        
        result = queue_manager.add(payload)
        assert result is True
        
        retrieved = queue_manager.retrieve()
        assert len(retrieved) == 1
        assert retrieved[0][1]['employee_name'] == "José García"
        assert retrieved[0][1]['unicode'] == "🎉 emoji test"
    
    def test_large_payload(self, queue_manager):
        """Test adding a large payload."""
        payload = {
            "employee_name": "John Doe",
            "screenshot": "x" * 100000,  # Large string
            "data": list(range(1000))
        }
        
        result = queue_manager.add(payload)
        assert result is True
        
        retrieved = queue_manager.retrieve()
        assert len(retrieved) == 1
        assert len(retrieved[0][1]['screenshot']) == 100000
    
    def test_nested_payload_structure(self, queue_manager):
        """Test payload with deeply nested structure."""
        payload = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "data": "deep"
                        }
                    }
                }
            }
        }
        
        result = queue_manager.add(payload)
        assert result is True
        
        retrieved = queue_manager.retrieve()
        assert retrieved[0][1]['level1']['level2']['level3']['level4']['data'] == "deep"

"""
Queue Manager Module

This module manages a local SQLite queue for storing failed data transmission payloads.
When the server is unreachable, payloads are queued locally and can be retrieved for retry.

Requirements: 6.4
"""

import sqlite3
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)


class QueueManager:
    """Manages a SQLite-based queue for failed transmission payloads."""
    
    # Default database path in user's app data directory
    DEFAULT_DB_PATH = Path.home() / ".vibgyorseek" / "queue.db"
    
    # Maximum queue size (number of payloads)
    MAX_QUEUE_SIZE = 1000
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the queue manager.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses default path.
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = self.DEFAULT_DB_PATH
        
        # Ensure the directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize the database
        self._init_database()
        
        logger.info(f"Queue manager initialized with database: {self.db_path}")
    
    def _init_database(self) -> None:
        """
        Initialize the SQLite database and create the queue table if it doesn't exist.
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Create the queue table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS payload_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        payload_json TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        retry_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Create index on timestamp for efficient FIFO retrieval
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON payload_queue(timestamp)
                """)
                
                conn.commit()
                logger.debug("Database initialized successfully")
        
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    def add(self, payload: Dict[str, Any]) -> bool:
        """
        Add a payload to the queue.
        
        Args:
            payload: The data payload dictionary to queue
        
        Returns:
            True if payload was added successfully, False otherwise
        
        Requirements: 6.4
        """
        if not payload:
            logger.error("Cannot add empty payload to queue")
            return False
        
        try:
            # Check queue size before adding
            current_size = self.size()
            if current_size >= self.MAX_QUEUE_SIZE:
                logger.warning(
                    f"Queue is full ({current_size} items). "
                    "Removing oldest payload to make room."
                )
                self._remove_oldest()
            
            # Serialize payload to JSON
            payload_json = json.dumps(payload)
            
            # Get timestamp from payload or use current time
            timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
            created_at = datetime.utcnow().isoformat()
            
            # Insert into database
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO payload_queue (payload_json, timestamp, created_at)
                    VALUES (?, ?, ?)
                """, (payload_json, timestamp, created_at))
                conn.commit()
            
            logger.info(f"Payload added to queue (timestamp: {timestamp})")
            return True
        
        except (json.JSONEncodeError, sqlite3.Error) as e:
            logger.error(f"Failed to add payload to queue: {e}", exc_info=True)
            return False
    
    def retrieve(self, limit: int = 1) -> List[Tuple[int, Dict[str, Any]]]:
        """
        Retrieve payloads from the queue in FIFO order.
        
        Args:
            limit: Maximum number of payloads to retrieve (default: 1)
        
        Returns:
            List of tuples (id, payload_dict) in FIFO order
        
        Requirements: 6.4
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Retrieve oldest payloads (FIFO)
                cursor.execute("""
                    SELECT id, payload_json
                    FROM payload_queue
                    ORDER BY timestamp ASC, id ASC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                
                # Parse JSON payloads
                results = []
                for row_id, payload_json in rows:
                    try:
                        payload = json.loads(payload_json)
                        results.append((row_id, payload))
                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Failed to parse payload {row_id}: {e}. "
                            "Skipping corrupted entry."
                        )
                        continue
                
                if results:
                    logger.debug(f"Retrieved {len(results)} payload(s) from queue")
                
                return results
        
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve payloads from queue: {e}", exc_info=True)
            return []
    
    def delete(self, payload_id: int) -> bool:
        """
        Delete a payload from the queue by ID.
        
        Args:
            payload_id: The ID of the payload to delete
        
        Returns:
            True if payload was deleted successfully, False otherwise
        
        Requirements: 6.4
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM payload_queue
                    WHERE id = ?
                """, (payload_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.debug(f"Deleted payload {payload_id} from queue")
                    return True
                else:
                    logger.warning(f"Payload {payload_id} not found in queue")
                    return False
        
        except sqlite3.Error as e:
            logger.error(f"Failed to delete payload {payload_id}: {e}", exc_info=True)
            return False
    
    def size(self) -> int:
        """
        Get the current number of payloads in the queue.
        
        Returns:
            Number of payloads in the queue
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM payload_queue")
                count = cursor.fetchone()[0]
                return count
        
        except sqlite3.Error as e:
            logger.error(f"Failed to get queue size: {e}", exc_info=True)
            return 0
    
    def clear(self) -> bool:
        """
        Clear all payloads from the queue.
        
        Returns:
            True if queue was cleared successfully, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM payload_queue")
                conn.commit()
                
                logger.info(f"Cleared {cursor.rowcount} payload(s) from queue")
                return True
        
        except sqlite3.Error as e:
            logger.error(f"Failed to clear queue: {e}", exc_info=True)
            return False
    
    def _remove_oldest(self) -> bool:
        """
        Remove the oldest payload from the queue.
        
        Returns:
            True if a payload was removed, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM payload_queue
                    WHERE id = (
                        SELECT id FROM payload_queue
                        ORDER BY timestamp ASC, id ASC
                        LIMIT 1
                    )
                """)
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.warning("Removed oldest payload from full queue")
                    return True
                else:
                    return False
        
        except sqlite3.Error as e:
            logger.error(f"Failed to remove oldest payload: {e}", exc_info=True)
            return False
    
    def increment_retry_count(self, payload_id: int) -> bool:
        """
        Increment the retry count for a payload.
        
        Args:
            payload_id: The ID of the payload
        
        Returns:
            True if retry count was incremented, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE payload_queue
                    SET retry_count = retry_count + 1
                    WHERE id = ?
                """, (payload_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.debug(f"Incremented retry count for payload {payload_id}")
                    return True
                else:
                    logger.warning(f"Payload {payload_id} not found for retry count update")
                    return False
        
        except sqlite3.Error as e:
            logger.error(f"Failed to increment retry count: {e}", exc_info=True)
            return False
    
    def get_retry_count(self, payload_id: int) -> Optional[int]:
        """
        Get the retry count for a payload.
        
        Args:
            payload_id: The ID of the payload
        
        Returns:
            The retry count, or None if payload not found
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT retry_count
                    FROM payload_queue
                    WHERE id = ?
                """, (payload_id,))
                
                row = cursor.fetchone()
                if row:
                    return row[0]
                else:
                    return None
        
        except sqlite3.Error as e:
            logger.error(f"Failed to get retry count: {e}", exc_info=True)
            return None

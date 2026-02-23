"""
Retry Manager Module

This module implements retry logic with exponential backoff for failed transmissions.
It integrates the QueueManager and HTTPTransmitter to process queued payloads when
the connection is restored.

Requirements: 6.4
"""

import logging
import time as time_module
from typing import Dict, Any, Optional, Tuple
from src.queue_manager import QueueManager
from src.http_transmitter import HTTPTransmitter


logger = logging.getLogger(__name__)


class RetryManager:
    """Manages retry logic with exponential backoff for failed transmissions."""
    
    # Exponential backoff parameters
    INITIAL_BACKOFF_SECONDS = 1
    MAX_BACKOFF_SECONDS = 300  # 5 minutes
    BACKOFF_MULTIPLIER = 2
    MAX_RETRY_ATTEMPTS = 10
    
    def __init__(
        self,
        queue_manager: QueueManager,
        http_transmitter: HTTPTransmitter
    ):
        """
        Initialize the retry manager.
        
        Args:
            queue_manager: QueueManager instance for payload queuing
            http_transmitter: HTTPTransmitter instance for sending payloads
        """
        self.queue_manager = queue_manager
        self.http_transmitter = http_transmitter
        self._last_retry_time = 0
        self._current_backoff = self.INITIAL_BACKOFF_SECONDS
        
        logger.info("Retry manager initialized")
    
    def send_with_retry(self, payload: Dict[str, Any]) -> bool:
        """
        Send a payload with automatic queuing on failure.
        
        Args:
            payload: The data payload to send
        
        Returns:
            True if sent successfully, False if queued for retry
        
        Requirements: 6.4
        """
        success, error = self.http_transmitter.send_payload(payload)
        
        if success:
            logger.info("Payload sent successfully")
            # Reset backoff on successful transmission
            self._current_backoff = self.INITIAL_BACKOFF_SECONDS
            return True
        else:
            logger.warning(f"Transmission failed: {error}. Queuing for retry.")
            # Queue the payload for retry
            if self.queue_manager.add(payload):
                logger.info("Payload queued for retry")
            else:
                logger.error("Failed to queue payload")
            return False
    
    def process_queue(self) -> Tuple[int, int]:
        """
        Process queued payloads with exponential backoff.
        
        Attempts to send queued payloads in FIFO order. Uses exponential backoff
        to avoid overwhelming the server. Stops processing if a transmission fails.
        
        Returns:
            Tuple of (successful_count, failed_count)
        
        Requirements: 6.4
        """
        queue_size = self.queue_manager.size()
        if queue_size == 0:
            return 0, 0
        
        logger.info(f"Processing queue with {queue_size} payload(s)")
        
        successful_count = 0
        failed_count = 0
        
        # Process payloads in FIFO order
        while True:
            # Retrieve next payload
            payloads = self.queue_manager.retrieve(limit=1)
            if not payloads:
                break
            
            payload_id, payload = payloads[0]
            retry_count = self.queue_manager.get_retry_count(payload_id) or 0
            
            # Check if max retries exceeded
            if retry_count >= self.MAX_RETRY_ATTEMPTS:
                logger.error(
                    f"Payload {payload_id} exceeded max retry attempts ({self.MAX_RETRY_ATTEMPTS}). "
                    "Removing from queue."
                )
                self.queue_manager.delete(payload_id)
                failed_count += 1
                continue
            
            # Calculate backoff delay based on retry count
            backoff_delay = min(
                self.INITIAL_BACKOFF_SECONDS * (self.BACKOFF_MULTIPLIER ** retry_count),
                self.MAX_BACKOFF_SECONDS
            )
            
            # Apply backoff delay
            current_time = time_module.time()
            time_since_last_retry = current_time - self._last_retry_time
            
            if time_since_last_retry < backoff_delay:
                wait_time = backoff_delay - time_since_last_retry
                logger.debug(f"Applying backoff delay: {wait_time:.2f} seconds")
                time_module.sleep(wait_time)
            
            # Attempt to send payload
            logger.info(f"Retrying payload {payload_id} (attempt {retry_count + 1})")
            success, error = self.http_transmitter.send_payload(payload)
            self._last_retry_time = time_module.time()
            
            if success:
                logger.info(f"Payload {payload_id} sent successfully on retry")
                self.queue_manager.delete(payload_id)
                successful_count += 1
                # Reset backoff on success
                self._current_backoff = self.INITIAL_BACKOFF_SECONDS
            else:
                logger.warning(f"Retry failed for payload {payload_id}: {error}")
                self.queue_manager.increment_retry_count(payload_id)
                failed_count += 1
                # Stop processing queue on failure (server likely still unreachable)
                break
        
        logger.info(
            f"Queue processing complete: {successful_count} successful, "
            f"{failed_count} failed"
        )
        
        return successful_count, failed_count
    
    def get_queue_size(self) -> int:
        """
        Get the current queue size.
        
        Returns:
            Number of payloads in the queue
        """
        return self.queue_manager.size()
    
    def clear_queue(self) -> bool:
        """
        Clear all queued payloads.
        
        Returns:
            True if queue was cleared successfully
        """
        return self.queue_manager.clear()

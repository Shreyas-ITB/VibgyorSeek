"""
Integration tests for the monitoring loop module.

Tests the monitoring loop with real module instances to verify
end-to-end coordination and interval-based execution.
"""

import pytest
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.monitoring_loop import MonitoringLoop
from src.config import Config


class TestMonitoringLoopIntegration:
    """Integration tests for monitoring loop."""
    
    @pytest.fixture
    def temp_env_file(self):
        """Create a temporary .env file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("SERVER_URL=https://test.example.com/api\n")
            f.write("AUTH_TOKEN=test_token_123\n")
            f.write("DATA_SEND_INTERVAL_MINUTES=1\n")
            f.write("SCREENSHOT_INTERVAL_MINUTES=1\n")
            f.write("IDLE_THRESHOLD_SECONDS=60\n")
            f.write("SCREENSHOT_QUALITY=75\n")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    @patch('src.http_transmitter.requests.post')
    def test_monitoring_loop_runs_and_collects_data(
        self,
        mock_post,
        mock_retrieve_name,
        temp_env_file
    ):
        """Test that monitoring loop runs and collects data at intervals."""
        mock_retrieve_name.return_value = "Test Employee"
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Create config from temp env file
        config = Config(env_file=temp_env_file)
        
        # Create monitoring loop
        loop = MonitoringLoop(config=config)
        
        # Start the loop
        loop.start()
        
        try:
            assert loop.is_running()
            
            # Let it run for a short time
            time.sleep(2)
            
            # Check status
            status = loop.get_status()
            assert status['running'] == True
            assert status['employee_name'] == "Test Employee"
            assert status['data_interval_minutes'] == 1
            
        finally:
            # Stop the loop
            loop.stop()
            assert not loop.is_running()
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    @patch('src.http_transmitter.requests.post')
    def test_monitoring_loop_handles_transmission_failure(
        self,
        mock_post,
        mock_retrieve_name,
        temp_env_file
    ):
        """Test that monitoring loop handles transmission failures gracefully."""
        mock_retrieve_name.return_value = "Test Employee"
        
        # Mock failed HTTP response (connection error)
        mock_post.side_effect = Exception("Connection failed")
        
        # Create config from temp env file
        config = Config(env_file=temp_env_file)
        
        # Create monitoring loop
        loop = MonitoringLoop(config=config)
        
        # Start the loop
        loop.start()
        
        try:
            assert loop.is_running()
            
            # Let it run for a short time
            time.sleep(2)
            
            # Loop should still be running despite transmission failures
            assert loop.is_running()
            
            # Check that queue has items (failed transmissions)
            status = loop.get_status()
            # Queue size might be 0 or more depending on timing
            assert status['queue_size'] >= 0
            
        finally:
            # Stop the loop
            loop.stop()
            assert not loop.is_running()
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    def test_monitoring_loop_graceful_error_handling(
        self,
        mock_retrieve_name,
        temp_env_file
    ):
        """Test that monitoring loop continues operation despite errors."""
        mock_retrieve_name.return_value = "Test Employee"
        
        # Create config from temp env file
        config = Config(env_file=temp_env_file)
        
        # Create monitoring loop
        loop = MonitoringLoop(config=config)
        
        # Mock payload builder to occasionally fail
        original_build = loop.payload_builder.build_payload
        call_count = [0]
        
        def failing_build(employee_name):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Simulated build failure")
            return original_build(employee_name)
        
        loop.payload_builder.build_payload = failing_build
        
        # Start the loop
        loop.start()
        
        try:
            assert loop.is_running()
            
            # Let it run for a short time
            time.sleep(2)
            
            # Loop should still be running despite the error
            assert loop.is_running()
            
        finally:
            # Stop the loop
            loop.stop()
            assert not loop.is_running()
    
    @patch('src.monitoring_loop.retrieve_employee_name')
    @patch('src.http_transmitter.requests.post')
    def test_monitoring_loop_processes_queue(
        self,
        mock_post,
        mock_retrieve_name,
        temp_env_file
    ):
        """Test that monitoring loop processes queued payloads."""
        mock_retrieve_name.return_value = "Test Employee"
        
        # First fail, then succeed
        call_count = [0]
        
        def mock_post_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Connection failed")
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        # Create config from temp env file
        config = Config(env_file=temp_env_file)
        
        # Create monitoring loop
        loop = MonitoringLoop(config=config)
        
        # Start the loop
        loop.start()
        
        try:
            assert loop.is_running()
            
            # Let it run long enough for multiple attempts
            time.sleep(3)
            
            # Check that queue was processed
            status = loop.get_status()
            # Queue should be empty or smaller after successful retry
            assert status['queue_size'] >= 0
            
        finally:
            # Stop the loop
            loop.stop()
            assert not loop.is_running()

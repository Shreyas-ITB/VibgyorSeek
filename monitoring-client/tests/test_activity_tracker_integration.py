"""Integration tests for activity tracker with configuration."""

import time
import pytest
from src.activity_tracker import ActivityTracker, ActivityState
from src.config import Config


class TestActivityTrackerIntegration:
    """Integration tests for ActivityTracker with Config."""
    
    def test_tracker_with_config_idle_threshold(self, tmp_path):
        """Test that tracker uses idle threshold from config."""
        # Create a temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            "SERVER_URL=https://example.com\n"
            "AUTH_TOKEN=test_token\n"
            "IDLE_THRESHOLD_SECONDS=2\n"
        )
        
        # Load config
        config = Config(str(env_file))
        
        # Create tracker with config value
        tracker = ActivityTracker(idle_threshold_seconds=config.idle_threshold_seconds)
        
        # Verify threshold is set correctly
        assert tracker.idle_threshold == 2
    
    def test_tracker_with_default_config_threshold(self, tmp_path, monkeypatch):
        """Test that tracker uses default idle threshold when not specified."""
        # Clear any existing IDLE_THRESHOLD_SECONDS environment variable
        monkeypatch.delenv("IDLE_THRESHOLD_SECONDS", raising=False)
        
        # Create a temporary .env file without IDLE_THRESHOLD_SECONDS
        env_file = tmp_path / ".env"
        env_file.write_text(
            "SERVER_URL=https://example.com\n"
            "AUTH_TOKEN=test_token\n"
        )
        
        # Load config
        config = Config(str(env_file))
        
        # Create tracker with config value
        tracker = ActivityTracker(idle_threshold_seconds=config.idle_threshold_seconds)
        
        # Verify default threshold is used
        assert tracker.idle_threshold == 300
    
    def test_full_activity_cycle(self):
        """Test a complete activity monitoring cycle."""
        # Create tracker with short idle threshold for testing
        tracker = ActivityTracker(idle_threshold_seconds=1)
        
        # Start tracking
        tracker.start()
        
        try:
            # Simulate work activity
            tracker._on_activity()
            time.sleep(0.5)
            
            # Check state is WORK
            assert tracker.current_state == ActivityState.WORK
            
            # Get activity data
            work_seconds, idle_seconds, state = tracker.get_activity_data()
            assert work_seconds > 0
            assert state == ActivityState.WORK
            
            # Wait for idle threshold
            time.sleep(2.0)
            
            # Check state is IDLE
            assert tracker.current_state == ActivityState.IDLE
            
            # Get activity data again
            work_seconds, idle_seconds, state = tracker.get_activity_data()
            assert idle_seconds > 0
            assert state == ActivityState.IDLE
            
            # Simulate activity again
            tracker._on_activity()
            
            # Check state is back to WORK
            assert tracker.current_state == ActivityState.WORK
            
        finally:
            # Stop tracking
            tracker.stop()
    
    def test_reset_interval_preserves_state(self):
        """Test that reset_interval preserves current state."""
        tracker = ActivityTracker(idle_threshold_seconds=1)
        
        # Accumulate some time
        time.sleep(0.5)
        
        # Get initial state
        initial_state = tracker.current_state
        
        # Reset interval
        tracker.reset_interval()
        
        # State should be preserved
        assert tracker.current_state == initial_state
        
        # But counters should be reset
        work_seconds, idle_seconds, _ = tracker.get_activity_data()
        assert work_seconds < 1
        assert idle_seconds < 1

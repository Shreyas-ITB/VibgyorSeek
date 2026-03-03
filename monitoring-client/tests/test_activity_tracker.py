"""Unit tests for the activity tracker module."""

import time
import pytest
from unittest.mock import Mock, patch
from src.activity_tracker import ActivityTracker, ActivityState


class TestActivityTracker:
    """Unit tests for ActivityTracker class."""
    
    def test_initialization_with_default_threshold(self):
        """Test that tracker initializes with default idle threshold."""
        tracker = ActivityTracker()
        assert tracker.idle_threshold == 300
        assert tracker.current_state == ActivityState.WORK
    
    def test_initialization_with_custom_threshold(self):
        """Test that tracker initializes with custom idle threshold."""
        tracker = ActivityTracker(idle_threshold_seconds=600)
        assert tracker.idle_threshold == 600
    
    def test_initialization_with_invalid_threshold(self):
        """Test that tracker raises error for invalid threshold."""
        with pytest.raises(ValueError, match="idle_threshold_seconds must be positive"):
            ActivityTracker(idle_threshold_seconds=0)
        
        with pytest.raises(ValueError, match="idle_threshold_seconds must be positive"):
            ActivityTracker(idle_threshold_seconds=-10)
    
    def test_initial_state_is_work(self):
        """Test that initial state is WORK."""
        tracker = ActivityTracker()
        assert tracker.current_state == ActivityState.WORK
    
    def test_get_activity_data_initial(self):
        """Test getting activity data immediately after initialization."""
        tracker = ActivityTracker()
        work_seconds, idle_seconds, state = tracker.get_activity_data()
        
        # Should have minimal time accumulated
        assert work_seconds >= 0
        assert idle_seconds >= 0
        assert state == ActivityState.WORK
    
    def test_start_and_stop(self):
        """Test starting and stopping the tracker."""
        tracker = ActivityTracker()
        
        # Start tracking
        tracker.start()
        assert tracker._running is True
        assert tracker._keyboard_listener is not None
        assert tracker._mouse_listener is not None
        
        # Stop tracking
        tracker.stop()
        assert tracker._running is False
    
    def test_start_when_already_running(self):
        """Test that starting when already running is safe."""
        tracker = ActivityTracker()
        tracker.start()
        
        # Starting again should be safe
        tracker.start()
        assert tracker._running is True
        
        tracker.stop()
    
    def test_stop_when_not_running(self):
        """Test that stopping when not running is safe."""
        tracker = ActivityTracker()
        
        # Stopping when not running should be safe
        tracker.stop()
        assert tracker._running is False
    
    def test_activity_triggers_work_state(self):
        """Test that activity keeps the tracker in WORK state."""
        tracker = ActivityTracker(idle_threshold_seconds=2)
        
        # Simulate activity
        tracker._on_activity()
        
        # Should be in WORK state
        assert tracker.current_state == ActivityState.WORK
    
    def test_no_activity_triggers_idle_state(self):
        """Test that lack of activity transitions to IDLE state."""
        tracker = ActivityTracker(idle_threshold_seconds=1)
        
        # Wait for idle threshold to pass
        time.sleep(1.5)
        
        # Should be in IDLE state
        assert tracker.current_state == ActivityState.IDLE
    
    def test_activity_after_idle_returns_to_work(self):
        """Test that activity after IDLE transitions back to WORK."""
        tracker = ActivityTracker(idle_threshold_seconds=1)
        
        # Wait for idle threshold
        time.sleep(1.5)
        assert tracker.current_state == ActivityState.IDLE
        
        # Simulate activity
        tracker._on_activity()
        
        # Should be back in WORK state
        assert tracker.current_state == ActivityState.WORK
    
    def test_cumulative_time_tracking(self):
        """Test that cumulative time is tracked correctly."""
        tracker = ActivityTracker(idle_threshold_seconds=2)
        
        # Simulate some work time
        time.sleep(0.5)
        
        work_seconds, idle_seconds, state = tracker.get_activity_data()
        
        # Should have accumulated some work time
        assert work_seconds > 0
        assert idle_seconds == 0
        assert state == ActivityState.WORK
    
    def test_reset_interval(self):
        """Test that reset_interval clears counters."""
        tracker = ActivityTracker(idle_threshold_seconds=2)
        
        # Accumulate some time
        time.sleep(0.5)
        
        # Reset interval
        tracker.reset_interval()
        
        # Get activity data
        work_seconds, idle_seconds, state = tracker.get_activity_data()
        
        # Counters should be near zero (minimal time since reset)
        assert work_seconds < 1
        assert idle_seconds < 1
    
    def test_work_and_idle_time_sum(self):
        """Test that work and idle time sum to total elapsed time."""
        tracker = ActivityTracker(idle_threshold_seconds=1)
        
        # Let some time pass
        time.sleep(1.5)
        
        work_seconds, idle_seconds, state = tracker.get_activity_data()
        total_time = work_seconds + idle_seconds
        
        # Total should be approximately 1.5 seconds (with some tolerance)
        assert 1.0 <= total_time <= 2.0
    
    def test_multiple_activities_extend_work_time(self):
        """Test that multiple activities keep extending work time."""
        tracker = ActivityTracker(idle_threshold_seconds=1)
        
        # Simulate multiple activities
        for _ in range(3):
            tracker._on_activity()
            time.sleep(0.3)
        
        work_seconds, idle_seconds, state = tracker.get_activity_data()
        
        # Should have accumulated work time
        assert work_seconds > 0
        assert state == ActivityState.WORK
    
    def test_thread_safety(self):
        """Test that tracker is thread-safe."""
        tracker = ActivityTracker(idle_threshold_seconds=2)
        
        # Simulate concurrent access
        import threading
        
        def simulate_activity():
            for _ in range(10):
                tracker._on_activity()
                time.sleep(0.01)
        
        threads = [threading.Thread(target=simulate_activity) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should not crash and should have accumulated time
        work_seconds, idle_seconds, state = tracker.get_activity_data()
        assert work_seconds >= 0
        assert idle_seconds >= 0

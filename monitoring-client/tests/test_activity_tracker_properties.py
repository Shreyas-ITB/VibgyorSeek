"""Property-based tests for the activity tracker module.

Feature: vibgyorseek-employee-monitoring

NOTE: These tests use real time.sleep() and can be slow.
Run with: pytest tests/test_activity_tracker_properties.py -v
Or skip with: pytest -m "not slow"
"""

import time
import pytest
from hypothesis import given, strategies as st, settings, assume
from src.activity_tracker import ActivityTracker, ActivityState

# Mark all tests in this module as slow
pytestmark = pytest.mark.slow


# Property 4: Activity Time Accounting
# **Validates: Requirements 2.4**
@given(
    idle_threshold=st.integers(min_value=1, max_value=2),
    work_duration=st.floats(min_value=0.5, max_value=1.0),
    idle_duration=st.floats(min_value=0.5, max_value=1.0)
)
@settings(max_examples=5, deadline=None)
def test_property_activity_time_accounting(idle_threshold, work_duration, idle_duration):
    """
    Property 4: Activity Time Accounting
    
    For any monitoring interval, the sum of work_seconds and idle_seconds 
    should equal the total interval duration in seconds.
    
    **Validates: Requirements 2.4**
    """
    tracker = ActivityTracker(idle_threshold_seconds=idle_threshold)
    
    # Simulate work period with activity
    start_time = time.time()
    tracker._on_activity()
    time.sleep(work_duration)
    
    # Simulate idle period (no activity)
    time.sleep(idle_duration)
    
    # Get activity data
    work_seconds, idle_seconds, state = tracker.get_activity_data()
    total_tracked = work_seconds + idle_seconds
    actual_elapsed = time.time() - start_time
    
    # The sum should approximately equal the total elapsed time
    # Allow 20% tolerance for timing variations and rounding
    tolerance = max(1.0, actual_elapsed * 0.2)
    assert abs(total_tracked - actual_elapsed) <= tolerance, \
        f"Time accounting mismatch: work={work_seconds}, idle={idle_seconds}, " \
        f"total={total_tracked}, elapsed={actual_elapsed}"


# Property 5: Idle State Classification
# **Validates: Requirements 2.2**
@given(
    idle_threshold=st.integers(min_value=1, max_value=2),
    wait_multiplier=st.floats(min_value=1.2, max_value=1.5)
)
@settings(max_examples=5, deadline=None)
def test_property_idle_state_classification(idle_threshold, wait_multiplier):
    """
    Property 5: Idle State Classification
    
    For any time period where no keyboard or mouse input is detected and 
    the duration exceeds the configured idle threshold, the Activity_State 
    should be classified as IDLE.
    
    **Validates: Requirements 2.2**
    """
    tracker = ActivityTracker(idle_threshold_seconds=idle_threshold)
    
    # Start with activity to ensure we're in WORK state
    tracker._on_activity()
    assert tracker.current_state == ActivityState.WORK
    
    # Wait for longer than the idle threshold without any activity
    wait_time = idle_threshold * wait_multiplier
    time.sleep(wait_time)
    
    # Should now be in IDLE state
    current_state = tracker.current_state
    assert current_state == ActivityState.IDLE, \
        f"Expected IDLE after {wait_time}s with threshold {idle_threshold}s, " \
        f"but got {current_state}"


# Property 6: Work State Classification
# **Validates: Requirements 2.3**
@given(
    idle_threshold=st.integers(min_value=2, max_value=3),
    activity_interval=st.floats(min_value=0.01, max_value=0.1)
)
@settings(max_examples=5, deadline=None)
def test_property_work_state_classification(idle_threshold, activity_interval):
    """
    Property 6: Work State Classification
    
    For any time period where keyboard or mouse input is detected, 
    the Activity_State should be classified as WORK.
    
    **Validates: Requirements 2.3**
    """
    # Ensure activity interval is less than idle threshold
    assume(activity_interval < idle_threshold)
    
    tracker = ActivityTracker(idle_threshold_seconds=idle_threshold)
    
    # Simulate continuous activity by triggering activity events
    # at intervals shorter than the idle threshold
    num_activities = 5
    for i in range(num_activities):
        tracker._on_activity()
        
        # Check state immediately after activity
        current_state = tracker.current_state
        assert current_state == ActivityState.WORK, \
            f"Expected WORK after activity event {i+1}, but got {current_state}"
        
        # Wait for less than idle threshold
        if i < num_activities - 1:
            time.sleep(activity_interval)
    
    # Final check - should still be in WORK state
    assert tracker.current_state == ActivityState.WORK


# Additional property: State transition from IDLE to WORK
@given(
    idle_threshold=st.integers(min_value=1, max_value=2)
)
@settings(max_examples=5, deadline=None)
def test_property_idle_to_work_transition(idle_threshold):
    """
    Property: State Transition from IDLE to WORK
    
    For any tracker in IDLE state, detecting keyboard or mouse input 
    should immediately transition the state to WORK.
    
    **Validates: Requirements 2.2, 2.3**
    """
    tracker = ActivityTracker(idle_threshold_seconds=idle_threshold)
    
    # Wait to enter IDLE state
    time.sleep(idle_threshold * 1.5)
    assert tracker.current_state == ActivityState.IDLE
    
    # Trigger activity
    tracker._on_activity()
    
    # Should immediately transition to WORK
    current_state = tracker.current_state
    assert current_state == ActivityState.WORK, \
        f"Expected WORK after activity from IDLE, but got {current_state}"


# Property: Time accounting with state transitions
@given(
    idle_threshold=st.integers(min_value=1, max_value=2),
    work_period=st.floats(min_value=0.05, max_value=0.2)
)
@settings(max_examples=5, deadline=None)
def test_property_time_accounting_with_transitions(idle_threshold, work_period):
    """
    Property: Time Accounting with State Transitions
    
    For any sequence of WORK and IDLE periods, the cumulative time 
    should accurately reflect the time spent in each state.
    
    **Validates: Requirements 2.2, 2.3, 2.4**
    """
    tracker = ActivityTracker(idle_threshold_seconds=idle_threshold)
    
    start_time = time.time()
    
    # Work period
    tracker._on_activity()
    time.sleep(work_period)
    
    # Idle period (wait for threshold + buffer)
    idle_period = idle_threshold * 1.5
    time.sleep(idle_period)
    
    # Get activity data
    work_seconds, idle_seconds, state = tracker.get_activity_data()
    total_tracked = work_seconds + idle_seconds
    actual_elapsed = time.time() - start_time
    
    # Verify state is IDLE
    assert state == ActivityState.IDLE
    
    # Verify time accounting
    # Allow larger tolerance for rounding and timing variations
    tolerance = max(1.0, actual_elapsed * 0.25)
    assert abs(total_tracked - actual_elapsed) <= tolerance, \
        f"Time accounting with transitions: work={work_seconds}, idle={idle_seconds}, " \
        f"total={total_tracked}, elapsed={actual_elapsed}"
    
    # Verify work time is approximately the work period
    # (plus idle threshold since we count until threshold is reached)
    expected_work = work_period + idle_threshold
    work_tolerance = max(1.0, expected_work * 0.3)
    assert abs(work_seconds - expected_work) <= work_tolerance, \
        f"Work time mismatch: expected ~{expected_work}, got {work_seconds}"

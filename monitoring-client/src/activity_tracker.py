"""Activity state tracker for monitoring keyboard and mouse events."""

import time
import threading
from enum import Enum
from typing import Tuple
from pynput import keyboard, mouse


class ActivityState(Enum):
    """Enumeration of activity states."""
    IDLE = "IDLE"
    WORK = "WORK"


class ActivityTracker:
    """
    Tracks user activity state (IDLE/WORK) based on keyboard and mouse input.
    
    Uses pynput to monitor input events and maintains a state machine that
    transitions between IDLE and WORK states based on activity and idle threshold.
    """
    
    def __init__(self, idle_threshold_seconds: int = 300):
        """
        Initialize the activity tracker.
        
        Args:
            idle_threshold_seconds: Number of seconds without input before
                                   transitioning to IDLE state (default: 300).
        """
        if idle_threshold_seconds <= 0:
            raise ValueError("idle_threshold_seconds must be positive")
        
        self.idle_threshold = idle_threshold_seconds
        self._state = ActivityState.WORK
        self._last_activity_time = time.time()
        self._work_seconds = 0.0
        self._idle_seconds = 0.0
        self._interval_start_time = time.time()
        self._lock = threading.Lock()
        
        # Listeners for keyboard and mouse
        self._keyboard_listener = None
        self._mouse_listener = None
        self._running = False
    
    def start(self) -> None:
        """Start monitoring keyboard and mouse activity."""
        if self._running:
            return
        
        self._running = True
        
        # Start keyboard listener
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_activity
        )
        self._keyboard_listener.start()
        
        # Start mouse listener
        self._mouse_listener = mouse.Listener(
            on_move=self._on_activity,
            on_click=self._on_activity,
            on_scroll=self._on_activity
        )
        self._mouse_listener.start()
    
    def stop(self) -> None:
        """Stop monitoring keyboard and mouse activity."""
        if not self._running:
            return
        
        self._running = False
        
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
    
    def _on_activity(self, *args, **kwargs) -> None:
        """
        Callback for any keyboard or mouse activity.
        
        Updates last activity time and transitions to WORK state if needed.
        """
        with self._lock:
            current_time = time.time()
            
            # Update cumulative time before state change
            self._update_cumulative_time(current_time)
            
            # Update last activity time
            self._last_activity_time = current_time
            
            # Transition to WORK state if not already
            if self._state == ActivityState.IDLE:
                self._state = ActivityState.WORK
    
    def _update_cumulative_time(self, current_time: float) -> None:
        """
        Update cumulative work and idle time based on current state.
        
        Args:
            current_time: Current timestamp.
        """
        # Calculate time since last update
        time_delta = current_time - self._interval_start_time
        
        if time_delta <= 0:
            return
        
        # Check if we should transition to IDLE
        time_since_activity = current_time - self._last_activity_time
        
        if time_since_activity >= self.idle_threshold:
            # We should be in IDLE state
            if self._state == ActivityState.WORK:
                # Transition from WORK to IDLE
                # Calculate when we became idle
                idle_start_time = self._last_activity_time + self.idle_threshold
                
                # Time from interval start to idle start is work time
                work_time = idle_start_time - self._interval_start_time
                if work_time > 0:
                    self._work_seconds += work_time
                
                # Time from idle start to now is idle time
                idle_time = current_time - idle_start_time
                if idle_time > 0:
                    self._idle_seconds += idle_time
                
                self._state = ActivityState.IDLE
            else:
                # Already IDLE, add all time as idle
                self._idle_seconds += time_delta
        else:
            # Still active, add all time as work
            self._work_seconds += time_delta
        
        # Reset interval start time
        self._interval_start_time = current_time
    
    def get_activity_data(self) -> Tuple[int, int, ActivityState]:
        """
        Get cumulative activity data for the current interval.
        
        Returns:
            Tuple of (work_seconds, idle_seconds, current_state).
        """
        with self._lock:
            current_time = time.time()
            
            # Update cumulative time before returning
            self._update_cumulative_time(current_time)
            
            return (
                int(round(self._work_seconds)),
                int(round(self._idle_seconds)),
                self._state
            )
    
    def reset_interval(self) -> None:
        """
        Reset the activity counters for a new interval.
        
        Preserves the current state and last activity time.
        """
        with self._lock:
            current_time = time.time()
            
            # Update cumulative time before reset
            self._update_cumulative_time(current_time)
            
            # Reset counters
            self._work_seconds = 0.0
            self._idle_seconds = 0.0
            self._interval_start_time = current_time
    
    @property
    def current_state(self) -> ActivityState:
        """Get the current activity state."""
        with self._lock:
            current_time = time.time()
            time_since_activity = current_time - self._last_activity_time
            
            # Check if we should be in IDLE state
            if time_since_activity >= self.idle_threshold:
                return ActivityState.IDLE
            else:
                return ActivityState.WORK

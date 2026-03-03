"""
Browser Tab Usage Tracker Module

This module tracks how long each browser tab is open and active.
It maintains cumulative time for each tab during the monitoring interval.
Works concurrently with ApplicationUsageTracker using the same polling mechanism.

Requirements: Browser tab screen time tracking
"""

import time
import logging
from typing import Dict, Optional, List
from .browser_monitor import BrowserMonitor


logger = logging.getLogger(__name__)


class BrowserTabUsageTracker:
    """Tracks cumulative usage time for each browser tab."""
    
    def __init__(self, browser_monitor: BrowserMonitor):
        """
        Initialize the browser tab usage tracker.
        
        Args:
            browser_monitor: BrowserMonitor instance to get open tabs
        """
        self.browser_monitor = browser_monitor
        
        # Track cumulative time per tab (in seconds)
        # Key format: "browser|title" to uniquely identify tabs
        self._tab_durations: Dict[str, float] = {}
        
        # Track currently open tabs
        self._current_tabs: List[Dict[str, str]] = []
        self._last_update_time: float = time.time()
        
        logger.info("BrowserTabUsageTracker initialized")
    
    def update(self) -> None:
        """
        Update tab durations based on currently open tabs.
        Should be called from the same polling loop as ApplicationUsageTracker.
        """
        try:
            current_time = time.time()
            time_elapsed = current_time - self._last_update_time
            
            # Get currently open tabs
            open_tabs = self.browser_monitor.get_browser_tabs()
            
            # Add elapsed time to all currently open tabs
            if time_elapsed > 0 and self._current_tabs:
                for tab in self._current_tabs:
                    tab_key = self._get_tab_key(tab)
                    if tab_key not in self._tab_durations:
                        self._tab_durations[tab_key] = 0.0
                    self._tab_durations[tab_key] += time_elapsed
                    logger.debug(f"Added {time_elapsed:.1f}s to tab: {tab_key} → Total: {self._tab_durations[tab_key]:.1f}s")
            
            # Update current tabs and last update time
            self._current_tabs = open_tabs
            self._last_update_time = current_time
            
            if open_tabs:
                logger.info(f"Tracking {len(open_tabs)} open browser tabs")
            
        except Exception as e:
            logger.error(f"Error updating browser tab usage: {e}", exc_info=True)
    
    def _get_tab_key(self, tab: Dict[str, str]) -> str:
        """
        Generate a unique key for a tab.
        
        Args:
            tab: Tab dictionary with 'browser', 'title', and optionally 'url'
        
        Returns:
            Unique key string
        """
        # Use browser and title to create unique key
        browser = tab.get('browser', 'Unknown')
        title = tab.get('title', 'Untitled')
        return f"{browser}|{title}"
    
    def _parse_tab_key(self, tab_key: str) -> Dict[str, str]:
        """
        Parse a tab key back into browser and title.
        
        Args:
            tab_key: Tab key string
        
        Returns:
            Dictionary with 'browser' and 'title'
        """
        parts = tab_key.split('|', 1)
        if len(parts) == 2:
            return {'browser': parts[0], 'title': parts[1]}
        return {'browser': 'Unknown', 'title': tab_key}
    
    def get_tab_durations(self) -> List[Dict[str, any]]:
        """
        Get cumulative duration for each browser tab.
        
        Returns:
            List of dictionaries with tab info and duration:
            [
                {"browser": "Chrome", "title": "GitHub", "url": "", "duration": 120},
                ...
            ]
        """
        # Update durations one more time before returning
        current_time = time.time()
        time_elapsed = current_time - self._last_update_time
        
        if time_elapsed > 0 and self._current_tabs:
            for tab in self._current_tabs:
                tab_key = self._get_tab_key(tab)
                if tab_key not in self._tab_durations:
                    self._tab_durations[tab_key] = 0.0
                self._tab_durations[tab_key] += time_elapsed
            self._last_update_time = current_time
        
        # Build result list with tab details and durations
        result = []
        for tab_key, duration in self._tab_durations.items():
            if duration > 0:
                tab_info = self._parse_tab_key(tab_key)
                
                # Try to find URL from current tabs
                url = ""
                for current_tab in self._current_tabs:
                    if self._get_tab_key(current_tab) == tab_key:
                        url = current_tab.get('url', '')
                        break
                
                result.append({
                    'browser': tab_info['browser'],
                    'title': tab_info['title'],
                    'url': url,
                    'duration': int(round(duration))
                })
        
        # Sort by duration (highest first)
        result.sort(key=lambda x: x['duration'], reverse=True)
        
        logger.info(f"Returning {len(result)} browser tabs with durations")
        return result
    
    def reset_interval(self) -> None:
        """Reset tab durations for a new interval."""
        self._tab_durations.clear()
        self._last_update_time = time.time()
        logger.debug("Browser tab usage durations reset")

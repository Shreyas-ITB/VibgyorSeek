"""
Integration tests for Browser Monitor module.

Tests the browser monitor in real-world scenarios.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from browser_monitor import BrowserMonitor


class TestBrowserMonitorIntegration:
    """Integration tests for BrowserMonitor."""
    
    def test_get_browser_tabs_integration(self):
        """Test getting browser tabs in a real environment."""
        monitor = BrowserMonitor()
        tabs = monitor.get_browser_tabs()
        
        # Should return a list (may be empty if no browsers running)
        assert isinstance(tabs, list)
        
        # If tabs are found, verify structure
        for tab in tabs:
            assert isinstance(tab, dict)
            assert 'browser' in tab
            assert tab['browser'] in ['Chrome', 'Firefox', 'Edge']
            
            # Must have title or URL (Property 7)
            has_title = 'title' in tab and tab['title']
            has_url = 'url' in tab and tab['url']
            assert has_title or has_url, "Tab must have either title or URL"
    
    def test_get_running_browsers_integration(self):
        """Test detecting running browsers in a real environment."""
        monitor = BrowserMonitor()
        running = monitor._get_running_browsers()
        
        # Should return a list
        assert isinstance(running, list)
        
        # All detected browsers should be supported
        for browser in running:
            assert browser in ['chrome', 'firefox', 'edge']
    
    def test_browser_detection_consistency(self):
        """Test that browser detection is consistent across multiple calls."""
        monitor = BrowserMonitor()
        
        # Call twice
        running1 = monitor._get_running_browsers()
        running2 = monitor._get_running_browsers()
        
        # Should return the same browsers (assuming no browsers started/stopped)
        assert set(running1) == set(running2)
    
    def test_tab_data_completeness(self):
        """Test that tab data is complete and valid."""
        monitor = BrowserMonitor()
        tabs = monitor.get_browser_tabs()
        
        for tab in tabs:
            # Browser field should be a non-empty string
            assert isinstance(tab['browser'], str)
            assert len(tab['browser']) > 0
            
            # Title should be string if present
            if 'title' in tab:
                assert isinstance(tab['title'], str)
            
            # URL should be string if present
            if 'url' in tab:
                assert isinstance(tab['url'], str)
                # URL should start with http:// or https:// if present
                if tab['url']:
                    assert tab['url'].startswith('http://') or tab['url'].startswith('https://')
    
    def test_error_handling(self):
        """Test that browser monitor handles errors gracefully."""
        monitor = BrowserMonitor()
        
        # Should not raise exceptions even if browsers are not accessible
        try:
            tabs = monitor.get_browser_tabs()
            assert isinstance(tabs, list)
        except Exception as e:
            pytest.fail(f"Browser monitor should not raise exceptions: {e}")
    
    def test_multiple_calls(self):
        """Test that multiple calls to get_browser_tabs work correctly."""
        monitor = BrowserMonitor()
        
        # Call multiple times
        tabs1 = monitor.get_browser_tabs()
        tabs2 = monitor.get_browser_tabs()
        tabs3 = monitor.get_browser_tabs()
        
        # All should return lists
        assert isinstance(tabs1, list)
        assert isinstance(tabs2, list)
        assert isinstance(tabs3, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

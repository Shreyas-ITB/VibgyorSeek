"""
Unit tests for the Browser Monitor module.

Tests browser detection and tab extraction functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import sqlite3
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from browser_monitor import BrowserMonitor


class TestBrowserMonitor:
    """Test suite for BrowserMonitor class."""
    
    def test_initialization(self):
        """Test that BrowserMonitor initializes correctly."""
        monitor = BrowserMonitor()
        assert monitor is not None
        assert monitor.platform in ['Windows', 'Darwin', 'Linux']
    
    def test_get_browser_tabs_returns_list(self):
        """Test that get_browser_tabs returns a list."""
        monitor = BrowserMonitor()
        tabs = monitor.get_browser_tabs()
        assert isinstance(tabs, list)
    
    def test_get_browser_tabs_structure(self):
        """Test that browser tabs have correct structure."""
        monitor = BrowserMonitor()
        tabs = monitor.get_browser_tabs()
        
        for tab in tabs:
            assert isinstance(tab, dict)
            assert 'browser' in tab
            assert 'title' in tab or 'url' in tab
            assert tab['browser'] in ['Chrome', 'Firefox', 'Edge']
    
    @patch('browser_monitor.psutil.process_iter')
    def test_get_running_browsers_chrome(self, mock_process_iter):
        """Test detection of Chrome browser."""
        # Mock Chrome process
        mock_proc = Mock()
        mock_proc.info = {'name': 'chrome.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        monitor = BrowserMonitor()
        running = monitor._get_running_browsers()
        
        assert 'chrome' in running
    
    @patch('browser_monitor.psutil.process_iter')
    def test_get_running_browsers_firefox(self, mock_process_iter):
        """Test detection of Firefox browser."""
        # Mock Firefox process
        mock_proc = Mock()
        mock_proc.info = {'name': 'firefox.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        monitor = BrowserMonitor()
        running = monitor._get_running_browsers()
        
        assert 'firefox' in running
    
    @patch('browser_monitor.psutil.process_iter')
    def test_get_running_browsers_edge(self, mock_process_iter):
        """Test detection of Edge browser."""
        # Mock Edge process
        mock_proc = Mock()
        mock_proc.info = {'name': 'msedge.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        monitor = BrowserMonitor()
        running = monitor._get_running_browsers()
        
        assert 'edge' in running
    
    @patch('browser_monitor.psutil.process_iter')
    def test_get_running_browsers_multiple(self, mock_process_iter):
        """Test detection of multiple browsers."""
        # Mock multiple browser processes
        mock_chrome = Mock()
        mock_chrome.info = {'name': 'chrome.exe'}
        mock_firefox = Mock()
        mock_firefox.info = {'name': 'firefox.exe'}
        
        mock_process_iter.return_value = [mock_chrome, mock_firefox]
        
        monitor = BrowserMonitor()
        running = monitor._get_running_browsers()
        
        assert 'chrome' in running
        assert 'firefox' in running
    
    @patch('browser_monitor.psutil.process_iter')
    def test_get_running_browsers_none(self, mock_process_iter):
        """Test when no browsers are running."""
        # Mock non-browser processes
        mock_proc = Mock()
        mock_proc.info = {'name': 'notepad.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        monitor = BrowserMonitor()
        running = monitor._get_running_browsers()
        
        assert len(running) == 0
    
    def test_read_chrome_history_with_mock_db(self):
        """Test reading Chrome history from a mock database."""
        monitor = BrowserMonitor()
        
        # Create a temporary SQLite database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            # Create mock history database
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE urls (
                    id INTEGER PRIMARY KEY,
                    url TEXT,
                    title TEXT,
                    last_visit_time INTEGER
                )
            """)
            
            cursor.execute("""
                INSERT INTO urls (url, title, last_visit_time)
                VALUES (?, ?, ?)
            """, ('https://github.com', 'GitHub', 1000))
            
            cursor.execute("""
                INSERT INTO urls (url, title, last_visit_time)
                VALUES (?, ?, ?)
            """, ('https://stackoverflow.com', 'Stack Overflow', 2000))
            
            conn.commit()
            conn.close()
            
            # Test reading
            tabs = monitor._read_chrome_history(tmp_path)
            
            assert len(tabs) == 2
            assert any(tab['url'] == 'https://github.com' for tab in tabs)
            assert any(tab['url'] == 'https://stackoverflow.com' for tab in tabs)
            assert all(tab['browser'] == 'Chrome' for tab in tabs)
        
        finally:
            # Clean up
            tmp_path.unlink()
    
    def test_parse_firefox_session_json(self):
        """Test parsing Firefox session JSON data."""
        monitor = BrowserMonitor()
        
        # Mock Firefox session data
        session_data = {
            'windows': [
                {
                    'tabs': [
                        {
                            'entries': [
                                {
                                    'url': 'https://github.com',
                                    'title': 'GitHub'
                                }
                            ]
                        },
                        {
                            'entries': [
                                {
                                    'url': 'https://stackoverflow.com',
                                    'title': 'Stack Overflow'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        tabs = monitor._parse_firefox_session_json(session_data)
        
        assert len(tabs) == 2
        assert any(tab['url'] == 'https://github.com' for tab in tabs)
        assert any(tab['url'] == 'https://stackoverflow.com' for tab in tabs)
        assert all(tab['browser'] == 'Firefox' for tab in tabs)
    
    def test_parse_firefox_session_json_empty(self):
        """Test parsing empty Firefox session data."""
        monitor = BrowserMonitor()
        
        session_data = {'windows': []}
        tabs = monitor._parse_firefox_session_json(session_data)
        
        assert len(tabs) == 0
    
    def test_parse_firefox_session_json_no_entries(self):
        """Test parsing Firefox session with tabs but no entries."""
        monitor = BrowserMonitor()
        
        session_data = {
            'windows': [
                {
                    'tabs': [
                        {'entries': []}
                    ]
                }
            ]
        }
        
        tabs = monitor._parse_firefox_session_json(session_data)
        assert len(tabs) == 0
    
    def test_read_edge_history_with_mock_db(self):
        """Test reading Edge history from a mock database."""
        monitor = BrowserMonitor()
        
        # Create a temporary SQLite database
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            # Create mock history database
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE urls (
                    id INTEGER PRIMARY KEY,
                    url TEXT,
                    title TEXT,
                    last_visit_time INTEGER
                )
            """)
            
            cursor.execute("""
                INSERT INTO urls (url, title, last_visit_time)
                VALUES (?, ?, ?)
            """, ('https://microsoft.com', 'Microsoft', 1000))
            
            conn.commit()
            conn.close()
            
            # Test reading
            tabs = monitor._read_edge_history(tmp_path)
            
            assert len(tabs) == 1
            assert tabs[0]['url'] == 'https://microsoft.com'
            assert tabs[0]['browser'] == 'Edge'
        
        finally:
            # Clean up
            tmp_path.unlink()
    
    def test_get_chrome_profile_paths(self):
        """Test getting Chrome profile paths."""
        monitor = BrowserMonitor()
        paths = monitor._get_chrome_profile_paths()
        
        # Should return a list (may be empty if Chrome not installed)
        assert isinstance(paths, list)
    
    def test_get_firefox_profile_paths(self):
        """Test getting Firefox profile paths."""
        monitor = BrowserMonitor()
        paths = monitor._get_firefox_profile_paths()
        
        # Should return a list (may be empty if Firefox not installed)
        assert isinstance(paths, list)
    
    def test_get_edge_profile_paths(self):
        """Test getting Edge profile paths."""
        monitor = BrowserMonitor()
        paths = monitor._get_edge_profile_paths()
        
        # Should return a list (may be empty if Edge not installed)
        assert isinstance(paths, list)
    
    @patch('browser_monitor.psutil.process_iter')
    def test_get_browser_tabs_with_no_browsers(self, mock_process_iter):
        """Test get_browser_tabs when no browsers are running."""
        # Mock no browser processes
        mock_proc = Mock()
        mock_proc.info = {'name': 'notepad.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        monitor = BrowserMonitor()
        tabs = monitor.get_browser_tabs()
        
        assert isinstance(tabs, list)
        assert len(tabs) == 0
    
    def test_tab_has_title_or_url(self):
        """Test that tabs have at least title or URL (Property 7)."""
        monitor = BrowserMonitor()
        tabs = monitor.get_browser_tabs()
        
        # Each tab must have either title or URL (or both)
        for tab in tabs:
            has_title = 'title' in tab and tab['title']
            has_url = 'url' in tab and tab['url']
            assert has_title or has_url, "Tab must have either title or URL"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

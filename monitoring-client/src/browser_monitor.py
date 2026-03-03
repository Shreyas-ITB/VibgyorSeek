"""
Browser Monitor Module

This module monitors open browser tabs across different browsers.
It detects running browser processes and extracts tab information
including titles and URLs using UI Automation.

Supported browsers: Chrome, Firefox, Edge

Requirements: 4.1, 4.2, 4.4
"""

import psutil
import logging
import json
import sqlite3
import os
import platform
from typing import List, Dict, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class BrowserMonitor:
    """Monitors browser tabs across Chrome, Firefox, and Edge."""
    
    # Browser process names by platform
    BROWSER_PROCESSES = {
        'Windows': {
            'chrome': ['chrome.exe'],
            'firefox': ['firefox.exe'],
            'edge': ['msedge.exe']
        },
        'Darwin': {  # macOS
            'chrome': ['Google Chrome'],
            'firefox': ['Firefox'],
            'edge': ['Microsoft Edge']
        },
        'Linux': {
            'chrome': ['chrome', 'chromium', 'google-chrome'],
            'firefox': ['firefox'],
            'edge': ['msedge', 'microsoft-edge']
        }
    }
    
    def __init__(self):
        """Initialize the browser monitor."""
        self.platform = platform.system()
        logger.info(f"BrowserMonitor initialized for platform: {self.platform}")
    
    def get_browser_tabs(self) -> List[Dict[str, str]]:
        """
        Get list of open browser tabs from all supported browsers using UI Automation.
        
        Returns:
            List of dictionaries containing tab information:
            [
                {"browser": "Chrome", "title": "GitHub", "url": "https://github.com"},
                {"browser": "Firefox", "title": "Stack Overflow", "url": "https://stackoverflow.com"},
                ...
            ]
        
        Requirements: 4.1, 4.2, 4.4
        """
        tabs = []
        
        try:
            # Check which browsers are running
            running_browsers = self._get_running_browsers()
            
            for browser in running_browsers:
                if browser == 'chrome':
                    tabs.extend(self._get_chrome_tabs_uia())
                elif browser == 'firefox':
                    tabs.extend(self._get_firefox_tabs())
                elif browser == 'edge':
                    tabs.extend(self._get_edge_tabs_uia())
            
            logger.debug(f"Found {len(tabs)} browser tabs across {len(running_browsers)} browsers")
            return tabs
        
        except Exception as e:
            logger.error(f"Error getting browser tabs: {e}")
            return []
    
    def _get_running_browsers(self) -> List[str]:
        """
        Detect which browsers are currently running.
        
        Returns:
            List of browser names (e.g., ['chrome', 'firefox'])
        
        Requirements: 4.1
        """
        running = []
        browser_processes = self.BROWSER_PROCESSES.get(self.platform, {})
        
        try:
            # Get all running process names
            running_process_names = set()
            for proc in psutil.process_iter(['name']):
                try:
                    running_process_names.add(proc.info['name'].lower())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Check each browser
            for browser, process_names in browser_processes.items():
                for proc_name in process_names:
                    if proc_name.lower() in running_process_names:
                        running.append(browser)
                        break
            
            logger.debug(f"Running browsers: {running}")
            return running
        
        except Exception as e:
            logger.error(f"Error detecting running browsers: {e}")
            return []
    
    def _get_chrome_tabs_uia(self) -> List[Dict[str, str]]:
        """
        Extract tab information from Chrome using UI Automation.
        
        Returns:
            List of tab dictionaries with titles
        
        Requirements: 4.2, 4.4
        """
        tabs = []
        
        try:
            from pywinauto import Desktop
            
            desktop = Desktop(backend="uia")
            windows = desktop.windows(title_re=".*Chrome.*", control_type="Window")
            
            for window in windows:
                try:
                    # Get all TabItem controls (these are the browser tabs)
                    tab_items = window.descendants(control_type="TabItem")
                    
                    for tab in tab_items:
                        try:
                            title = tab.window_text()
                            if title and title.strip():
                                tabs.append({
                                    'browser': 'Chrome',
                                    'title': title.strip(),
                                    'url': ''  # URL not easily accessible via UI Automation
                                })
                        except Exception as e:
                            logger.debug(f"Error reading Chrome tab: {e}")
                            continue
                
                except Exception as e:
                    logger.debug(f"Error processing Chrome window: {e}")
                    continue
            
            logger.debug(f"Found {len(tabs)} Chrome tabs via UI Automation")
            return tabs
        
        except ImportError:
            logger.warning("pywinauto not available, falling back to history")
            return self._get_chrome_tabs()
        except Exception as e:
            logger.error(f"Error getting Chrome tabs via UI Automation: {e}")
            return []
    
    def _get_edge_tabs_uia(self) -> List[Dict[str, str]]:
        """
        Extract tab information from Edge using UI Automation.
        
        Returns:
            List of tab dictionaries with titles
        
        Requirements: 4.2, 4.4
        """
        tabs = []
        
        try:
            from pywinauto import Desktop
            
            desktop = Desktop(backend="uia")
            windows = desktop.windows(title_re=".*Edge.*", control_type="Window")
            
            for window in windows:
                try:
                    # Get all TabItem controls (these are the browser tabs)
                    tab_items = window.descendants(control_type="TabItem")
                    
                    for tab in tab_items:
                        try:
                            title = tab.window_text()
                            if title and title.strip():
                                tabs.append({
                                    'browser': 'Edge',
                                    'title': title.strip(),
                                    'url': ''  # URL not easily accessible via UI Automation
                                })
                        except Exception as e:
                            logger.debug(f"Error reading Edge tab: {e}")
                            continue
                
                except Exception as e:
                    logger.debug(f"Error processing Edge window: {e}")
                    continue
            
            logger.debug(f"Found {len(tabs)} Edge tabs via UI Automation")
            return tabs
        
        except ImportError:
            logger.warning("pywinauto not available, falling back to history")
            return self._get_edge_tabs()
        except Exception as e:
            logger.error(f"Error getting Edge tabs via UI Automation: {e}")
            return []
    
    def _get_chrome_tabs(self) -> List[Dict[str, str]]:
        """
        Extract tab information from Chrome.
        
        Uses Chrome's session storage to read tab data.
        
        Returns:
            List of tab dictionaries
        
        Requirements: 4.2, 4.4
        """
        tabs = []
        
        try:
            # Chrome stores session data in the user profile directory
            profile_paths = self._get_chrome_profile_paths()
            
            for profile_path in profile_paths:
                # Try to read from Sessions or Current Session/Tabs files
                tabs.extend(self._read_chrome_session_data(profile_path))
            
            logger.debug(f"Found {len(tabs)} Chrome tabs")
            return tabs
        
        except Exception as e:
            logger.error(f"Error getting Chrome tabs: {e}")
            return []
    
    def _get_chrome_profile_paths(self) -> List[Path]:
        """Get Chrome user profile directory paths."""
        paths = []
        
        try:
            if self.platform == 'Windows':
                base = Path(os.environ.get('LOCALAPPDATA', '')) / 'Google' / 'Chrome' / 'User Data'
            elif self.platform == 'Darwin':
                base = Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome'
            else:  # Linux
                base = Path.home() / '.config' / 'google-chrome'
            
            if base.exists():
                # Check Default profile and numbered profiles
                for profile in ['Default', 'Profile 1', 'Profile 2', 'Profile 3']:
                    profile_path = base / profile
                    if profile_path.exists():
                        paths.append(profile_path)
            
            return paths
        
        except Exception as e:
            logger.debug(f"Error getting Chrome profile paths: {e}")
            return []
    
    def _read_chrome_session_data(self, profile_path: Path) -> List[Dict[str, str]]:
        """
        Read Chrome session data from profile directory.
        
        Chrome stores tab data in various files. We'll try to read from:
        - Current Session
        - Current Tabs
        - History (as fallback)
        """
        tabs = []
        
        try:
            # Try reading from History database (most reliable)
            history_db = profile_path / 'History'
            if history_db.exists():
                tabs.extend(self._read_chrome_history(history_db))
            
            return tabs
        
        except Exception as e:
            logger.debug(f"Error reading Chrome session data: {e}")
            return []
    
    def _read_chrome_history(self, history_path: Path) -> List[Dict[str, str]]:
        """
        Read recent URLs from Chrome history database.
        
        Note: This reads recent history, not necessarily open tabs.
        For true open tabs, we'd need Chrome DevTools Protocol.
        """
        tabs = []
        
        try:
            # Copy the database to avoid locking issues
            import tempfile
            import shutil
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
                tmp_path = tmp.name
            
            try:
                shutil.copy2(history_path, tmp_path)
                
                conn = sqlite3.connect(tmp_path)
                cursor = conn.cursor()
                
                # Get most recent URLs (last 10)
                cursor.execute("""
                    SELECT title, url 
                    FROM urls 
                    ORDER BY last_visit_time DESC 
                    LIMIT 10
                """)
                
                for title, url in cursor.fetchall():
                    if title and url:
                        tabs.append({
                            'browser': 'Chrome',
                            'title': title,
                            'url': url
                        })
                
                conn.close()
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
            return tabs
        
        except Exception as e:
            logger.debug(f"Error reading Chrome history: {e}")
            return []
    
    def _get_firefox_tabs(self) -> List[Dict[str, str]]:
        """
        Extract tab information from Firefox.
        
        Uses Firefox's sessionstore to read tab data.
        
        Returns:
            List of tab dictionaries
        
        Requirements: 4.2, 4.4
        """
        tabs = []
        
        try:
            profile_paths = self._get_firefox_profile_paths()
            
            for profile_path in profile_paths:
                tabs.extend(self._read_firefox_session_data(profile_path))
            
            logger.debug(f"Found {len(tabs)} Firefox tabs")
            return tabs
        
        except Exception as e:
            logger.error(f"Error getting Firefox tabs: {e}")
            return []
    
    def _get_firefox_profile_paths(self) -> List[Path]:
        """Get Firefox profile directory paths."""
        paths = []
        
        try:
            if self.platform == 'Windows':
                base = Path(os.environ.get('APPDATA', '')) / 'Mozilla' / 'Firefox' / 'Profiles'
            elif self.platform == 'Darwin':
                base = Path.home() / 'Library' / 'Application Support' / 'Firefox' / 'Profiles'
            else:  # Linux
                base = Path.home() / '.mozilla' / 'firefox'
            
            if base.exists():
                # Firefox profiles are in subdirectories
                for item in base.iterdir():
                    if item.is_dir():
                        paths.append(item)
            
            return paths
        
        except Exception as e:
            logger.debug(f"Error getting Firefox profile paths: {e}")
            return []
    
    def _read_firefox_session_data(self, profile_path: Path) -> List[Dict[str, str]]:
        """Read Firefox session data from sessionstore files."""
        tabs = []
        
        try:
            # Firefox stores session data in sessionstore.jsonlz4 or recovery.jsonlz4
            session_files = [
                profile_path / 'sessionstore.jsonlz4',
                profile_path / 'sessionstore-backups' / 'recovery.jsonlz4',
                profile_path / 'sessionstore.js'
            ]
            
            for session_file in session_files:
                if session_file.exists():
                    if session_file.suffix == '.jsonlz4':
                        # LZ4 compressed JSON
                        tabs.extend(self._read_firefox_lz4_session(session_file))
                    else:
                        # Plain JSON
                        tabs.extend(self._read_firefox_json_session(session_file))
                    
                    if tabs:
                        break
            
            return tabs
        
        except Exception as e:
            logger.debug(f"Error reading Firefox session data: {e}")
            return []
    
    def _read_firefox_lz4_session(self, session_file: Path) -> List[Dict[str, str]]:
        """Read Firefox LZ4-compressed session file."""
        tabs = []
        
        try:
            import lz4.block
            
            with open(session_file, 'rb') as f:
                # Skip the "mozLz40\0" header (8 bytes)
                magic = f.read(8)
                if magic != b'mozLz40\0':
                    return []
                
                # Decompress the rest
                compressed_data = f.read()
                decompressed = lz4.block.decompress(compressed_data)
                
                # Parse JSON
                session_data = json.loads(decompressed.decode('utf-8'))
                tabs.extend(self._parse_firefox_session_json(session_data))
        
        except ImportError:
            logger.debug("lz4 library not available, cannot read Firefox session")
        except Exception as e:
            logger.debug(f"Error reading Firefox LZ4 session: {e}")
        
        return tabs
    
    def _read_firefox_json_session(self, session_file: Path) -> List[Dict[str, str]]:
        """Read Firefox plain JSON session file."""
        tabs = []
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                tabs.extend(self._parse_firefox_session_json(session_data))
        
        except Exception as e:
            logger.debug(f"Error reading Firefox JSON session: {e}")
        
        return tabs
    
    def _parse_firefox_session_json(self, session_data: dict) -> List[Dict[str, str]]:
        """Parse Firefox session JSON to extract tab information."""
        tabs = []
        
        try:
            windows = session_data.get('windows', [])
            
            for window in windows:
                window_tabs = window.get('tabs', [])
                
                for tab in window_tabs:
                    entries = tab.get('entries', [])
                    if entries:
                        # Get the current entry (last one)
                        current_entry = entries[-1]
                        title = current_entry.get('title', '')
                        url = current_entry.get('url', '')
                        
                        if title or url:
                            tabs.append({
                                'browser': 'Firefox',
                                'title': title,
                                'url': url
                            })
        
        except Exception as e:
            logger.debug(f"Error parsing Firefox session JSON: {e}")
        
        return tabs
    
    def _get_edge_tabs(self) -> List[Dict[str, str]]:
        """
        Extract tab information from Microsoft Edge.
        
        Edge is Chromium-based, so uses similar structure to Chrome.
        
        Returns:
            List of tab dictionaries
        
        Requirements: 4.2, 4.4
        """
        tabs = []
        
        try:
            profile_paths = self._get_edge_profile_paths()
            
            for profile_path in profile_paths:
                tabs.extend(self._read_edge_session_data(profile_path))
            
            logger.debug(f"Found {len(tabs)} Edge tabs")
            return tabs
        
        except Exception as e:
            logger.error(f"Error getting Edge tabs: {e}")
            return []
    
    def _get_edge_profile_paths(self) -> List[Path]:
        """Get Edge user profile directory paths."""
        paths = []
        
        try:
            if self.platform == 'Windows':
                base = Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'Edge' / 'User Data'
            elif self.platform == 'Darwin':
                base = Path.home() / 'Library' / 'Application Support' / 'Microsoft Edge'
            else:  # Linux
                base = Path.home() / '.config' / 'microsoft-edge'
            
            if base.exists():
                # Check Default profile and numbered profiles
                for profile in ['Default', 'Profile 1', 'Profile 2', 'Profile 3']:
                    profile_path = base / profile
                    if profile_path.exists():
                        paths.append(profile_path)
            
            return paths
        
        except Exception as e:
            logger.debug(f"Error getting Edge profile paths: {e}")
            return []
    
    def _read_edge_session_data(self, profile_path: Path) -> List[Dict[str, str]]:
        """Read Edge session data (similar to Chrome)."""
        tabs = []
        
        try:
            # Try reading from History database
            history_db = profile_path / 'History'
            if history_db.exists():
                tabs.extend(self._read_edge_history(history_db))
            
            return tabs
        
        except Exception as e:
            logger.debug(f"Error reading Edge session data: {e}")
            return []
    
    def _read_edge_history(self, history_path: Path) -> List[Dict[str, str]]:
        """Read recent URLs from Edge history database."""
        tabs = []
        
        try:
            import tempfile
            import shutil
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
                tmp_path = tmp.name
            
            try:
                shutil.copy2(history_path, tmp_path)
                
                conn = sqlite3.connect(tmp_path)
                cursor = conn.cursor()
                
                # Get most recent URLs (last 10)
                cursor.execute("""
                    SELECT title, url 
                    FROM urls 
                    ORDER BY last_visit_time DESC 
                    LIMIT 10
                """)
                
                for title, url in cursor.fetchall():
                    if title and url:
                        tabs.append({
                            'browser': 'Edge',
                            'title': title,
                            'url': url
                        })
                
                conn.close()
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
            return tabs
        
        except Exception as e:
            logger.debug(f"Error reading Edge history: {e}")
            return []

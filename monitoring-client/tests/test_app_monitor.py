"""
Unit tests for the Application Monitor module.

Tests specific examples and edge cases for application monitoring functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import psutil
from src.app_monitor import ApplicationMonitor


class TestApplicationMonitor:
    """Unit tests for ApplicationMonitor class."""
    
    def test_initialization(self):
        """Test that ApplicationMonitor initializes correctly."""
        monitor = ApplicationMonitor()
        assert monitor.platform in ['Windows', 'Darwin', 'Linux']
    
    def test_system_process_exclusion(self):
        """Test that system processes are correctly identified and excluded."""
        monitor = ApplicationMonitor()
        
        # Create mock process for system process
        mock_proc = Mock(spec=psutil.Process)
        
        # Test system process names
        assert not monitor._is_user_application(mock_proc, 'svchost.exe')
        assert not monitor._is_user_application(mock_proc, 'system')
        assert not monitor._is_user_application(mock_proc, 'systemd')
    
    def test_user_application_identification(self):
        """Test that user applications are correctly identified."""
        monitor = ApplicationMonitor()
        
        # Create mock process for user application
        mock_proc = Mock(spec=psutil.Process)
        
        # Test user application names
        assert monitor._is_user_application(mock_proc, 'chrome.exe')
        assert monitor._is_user_application(mock_proc, 'code.exe')
        assert monitor._is_user_application(mock_proc, 'firefox.exe')
    
    def test_empty_process_name_exclusion(self):
        """Test that processes with empty names are excluded."""
        monitor = ApplicationMonitor()
        mock_proc = Mock(spec=psutil.Process)
        
        assert not monitor._is_user_application(mock_proc, '')
        assert not monitor._is_user_application(mock_proc, '   ')
    
    @patch('src.app_monitor.psutil.process_iter')
    def test_get_running_applications_empty(self, mock_process_iter):
        """Test getting applications when no processes are running."""
        mock_process_iter.return_value = []
        
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        assert isinstance(applications, list)
        assert len(applications) == 0
    
    @patch('src.app_monitor.psutil.process_iter')
    @patch.object(ApplicationMonitor, '_get_foreground_pid')
    def test_get_running_applications_with_processes(self, mock_foreground, mock_process_iter):
        """Test getting applications with mock processes."""
        # Mock foreground PID
        mock_foreground.return_value = 1234
        
        # Create mock processes
        mock_proc1 = Mock()
        mock_proc1.info = {'pid': 1234, 'name': 'chrome.exe', 'username': 'user'}
        
        mock_proc2 = Mock()
        mock_proc2.info = {'pid': 5678, 'name': 'code.exe', 'username': 'user'}
        
        mock_proc3 = Mock()
        mock_proc3.info = {'pid': 9999, 'name': 'svchost.exe', 'username': 'SYSTEM'}
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2, mock_proc3]
        
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        # Should have 2 user applications (chrome and code), excluding svchost
        assert len(applications) == 2
        
        # Check that chrome is marked as active
        chrome_app = next((app for app in applications if app['name'] == 'chrome.exe'), None)
        assert chrome_app is not None
        assert chrome_app['active'] is True
        
        # Check that code is not marked as active
        code_app = next((app for app in applications if app['name'] == 'code.exe'), None)
        assert code_app is not None
        assert code_app['active'] is False
    
    @patch('src.app_monitor.psutil.process_iter')
    def test_get_running_applications_handles_access_denied(self, mock_process_iter):
        """Test that AccessDenied exceptions are handled gracefully."""
        # Create a mock process that raises AccessDenied
        mock_proc = Mock()
        mock_proc.info = Mock(side_effect=psutil.AccessDenied())
        
        mock_process_iter.return_value = [mock_proc]
        
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        # Should return empty list without crashing
        assert isinstance(applications, list)
        assert len(applications) == 0
    
    @patch('src.app_monitor.psutil.process_iter')
    def test_get_running_applications_handles_no_such_process(self, mock_process_iter):
        """Test that NoSuchProcess exceptions are handled gracefully."""
        # Create a mock process that raises NoSuchProcess
        mock_proc = Mock()
        mock_proc.info = Mock(side_effect=psutil.NoSuchProcess(pid=123))
        
        mock_process_iter.return_value = [mock_proc]
        
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        # Should return empty list without crashing
        assert isinstance(applications, list)
        assert len(applications) == 0
    
    @patch('src.app_monitor.psutil.process_iter')
    @patch.object(ApplicationMonitor, '_get_foreground_pid')
    def test_get_application_names(self, mock_foreground, mock_process_iter):
        """Test getting just application names without active status."""
        mock_foreground.return_value = None
        
        # Create mock processes
        mock_proc1 = Mock()
        mock_proc1.info = {'pid': 1234, 'name': 'chrome.exe', 'username': 'user'}
        
        mock_proc2 = Mock()
        mock_proc2.info = {'pid': 5678, 'name': 'code.exe', 'username': 'user'}
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2]
        
        monitor = ApplicationMonitor()
        names = monitor.get_application_names()
        
        assert isinstance(names, list)
        assert len(names) == 2
        assert 'chrome.exe' in names
        assert 'code.exe' in names
    
    @patch('src.app_monitor.psutil.process_iter')
    @patch.object(ApplicationMonitor, '_get_foreground_pid')
    def test_get_foreground_application(self, mock_foreground, mock_process_iter):
        """Test getting the foreground application name."""
        mock_foreground.return_value = 1234
        
        # Create mock processes
        mock_proc1 = Mock()
        mock_proc1.info = {'pid': 1234, 'name': 'chrome.exe', 'username': 'user'}
        
        mock_proc2 = Mock()
        mock_proc2.info = {'pid': 5678, 'name': 'code.exe', 'username': 'user'}
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2]
        
        monitor = ApplicationMonitor()
        foreground = monitor.get_foreground_application()
        
        assert foreground == 'chrome.exe'
    
    @patch('src.app_monitor.psutil.process_iter')
    @patch.object(ApplicationMonitor, '_get_foreground_pid')
    def test_get_foreground_application_none(self, mock_foreground, mock_process_iter):
        """Test getting foreground application when none is active."""
        mock_foreground.return_value = None
        
        mock_proc = Mock()
        mock_proc.info = {'pid': 1234, 'name': 'chrome.exe', 'username': 'user'}
        
        mock_process_iter.return_value = [mock_proc]
        
        monitor = ApplicationMonitor()
        foreground = monitor.get_foreground_application()
        
        assert foreground is None
    
    @patch('src.app_monitor.psutil.process_iter')
    @patch.object(ApplicationMonitor, '_get_foreground_pid')
    def test_duplicate_application_names_filtered(self, mock_foreground, mock_process_iter):
        """Test that duplicate application names are filtered out."""
        mock_foreground.return_value = None
        
        # Create multiple processes with same name (e.g., multiple Chrome windows)
        mock_proc1 = Mock()
        mock_proc1.info = {'pid': 1234, 'name': 'chrome.exe', 'username': 'user'}
        
        mock_proc2 = Mock()
        mock_proc2.info = {'pid': 5678, 'name': 'chrome.exe', 'username': 'user'}
        
        mock_proc3 = Mock()
        mock_proc3.info = {'pid': 9999, 'name': 'code.exe', 'username': 'user'}
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2, mock_proc3]
        
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        # Should only have 2 unique applications (chrome and code)
        assert len(applications) == 2
        
        names = [app['name'] for app in applications]
        assert names.count('chrome.exe') == 1
        assert names.count('code.exe') == 1


class TestForegroundDetection:
    """Tests for platform-specific foreground detection."""
    
    def test_get_foreground_pid_returns_int_or_none(self):
        """Test that _get_foreground_pid returns either an int or None."""
        monitor = ApplicationMonitor()
        pid = monitor._get_foreground_pid()
        
        # Should return either an integer PID or None
        assert pid is None or isinstance(pid, int)
        
        # If it returns an int, it should be positive
        if isinstance(pid, int):
            assert pid > 0

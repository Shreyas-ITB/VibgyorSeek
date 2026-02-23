"""
Integration tests for the Application Monitor module.

These tests verify the module works with real system processes.
"""

import pytest
from src.app_monitor import ApplicationMonitor


class TestApplicationMonitorIntegration:
    """Integration tests for ApplicationMonitor with real system processes."""
    
    def test_get_running_applications_returns_list(self):
        """Test that get_running_applications returns a list."""
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        assert isinstance(applications, list)
    
    def test_get_running_applications_returns_valid_structure(self):
        """Test that each application has the required structure."""
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        # Should have at least some applications running
        assert len(applications) > 0
        
        # Each application should have 'name' and 'active' fields
        for app in applications:
            assert 'name' in app
            assert 'active' in app
            assert isinstance(app['name'], str)
            assert isinstance(app['active'], bool)
            assert len(app['name']) > 0
    
    def test_only_one_application_is_active(self):
        """Test that at most one application is marked as active."""
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        active_count = sum(1 for app in applications if app['active'])
        
        # Should have 0 or 1 active application
        assert active_count <= 1
    
    def test_get_application_names_returns_strings(self):
        """Test that get_application_names returns a list of strings."""
        monitor = ApplicationMonitor()
        names = monitor.get_application_names()
        
        assert isinstance(names, list)
        assert len(names) > 0
        
        for name in names:
            assert isinstance(name, str)
            assert len(name) > 0
    
    def test_get_foreground_application_returns_string_or_none(self):
        """Test that get_foreground_application returns a string or None."""
        monitor = ApplicationMonitor()
        foreground = monitor.get_foreground_application()
        
        # Should return either a string or None
        assert foreground is None or isinstance(foreground, str)
        
        # If it returns a string, it should be non-empty
        if isinstance(foreground, str):
            assert len(foreground) > 0
    
    def test_foreground_application_is_in_running_applications(self):
        """Test that the foreground application is in the list of running applications."""
        monitor = ApplicationMonitor()
        foreground = monitor.get_foreground_application()
        applications = monitor.get_running_applications()
        
        if foreground is not None:
            # The foreground app should be in the list of running applications
            app_names = [app['name'] for app in applications]
            assert foreground in app_names
            
            # The foreground app should be marked as active
            foreground_app = next((app for app in applications if app['name'] == foreground), None)
            assert foreground_app is not None
            assert foreground_app['active'] is True
    
    def test_no_duplicate_application_names(self):
        """Test that there are no duplicate application names in the list."""
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        names = [app['name'] for app in applications]
        unique_names = set(names)
        
        # All names should be unique
        assert len(names) == len(unique_names)
    
    def test_system_processes_excluded(self):
        """Test that common system processes are excluded from the list."""
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        app_names_lower = [app['name'].lower() for app in applications]
        
        # Common system processes should not be in the list
        system_processes = ['svchost.exe', 'system', 'csrss.exe', 'systemd']
        
        for sys_proc in system_processes:
            assert sys_proc not in app_names_lower
    
    def test_python_process_detected(self):
        """Test that the Python process running the tests is detected."""
        monitor = ApplicationMonitor()
        applications = monitor.get_running_applications()
        
        app_names_lower = [app['name'].lower() for app in applications]
        
        # Python should be in the list (since we're running Python tests)
        python_found = any('python' in name for name in app_names_lower)
        assert python_found, "Python process should be detected in running applications"
    
    def test_multiple_calls_return_consistent_results(self):
        """Test that multiple calls return similar results."""
        monitor = ApplicationMonitor()
        
        apps1 = monitor.get_running_applications()
        apps2 = monitor.get_running_applications()
        
        # The number of applications should be similar (within a reasonable range)
        # Some processes may start/stop between calls
        assert abs(len(apps1) - len(apps2)) <= 5
        
        # Most application names should be the same
        names1 = set(app['name'] for app in apps1)
        names2 = set(app['name'] for app in apps2)
        
        # At least 80% of applications should be the same
        common_names = names1.intersection(names2)
        assert len(common_names) >= min(len(names1), len(names2)) * 0.8

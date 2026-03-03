"""
Unit tests for the Service Manager module.

Tests service installation, lifecycle management, and security configuration.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys

# Mock win32 modules before importing service_manager
sys.modules['win32serviceutil'] = MagicMock()
sys.modules['win32service'] = MagicMock()
sys.modules['win32event'] = MagicMock()
sys.modules['servicemanager'] = MagicMock()
sys.modules['win32api'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32security'] = MagicMock()
sys.modules['ntsecuritycon'] = MagicMock()

from src.service_manager import ServiceManager, MonitoringService


class TestServiceManager(unittest.TestCase):
    """Test cases for ServiceManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service_name = "VibgyorSeekMonitoring"
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.win32service')
    @patch('src.service_manager.logger')
    def test_install_service_success(self, mock_logger, mock_win32service, mock_win32serviceutil):
        """Test successful service installation."""
        # Arrange
        mock_win32service.SERVICE_AUTO_START = 2
        
        # Act
        result = ServiceManager.install_service()
        
        # Assert
        self.assertTrue(result)
        mock_win32serviceutil.InstallService.assert_called_once()
        mock_logger.info.assert_called()
    
    @patch('src.service_manager.win32serviceutil', None)
    @patch('src.service_manager.logger')
    def test_install_service_no_pywin32(self, mock_logger):
        """Test service installation fails when pywin32 not available."""
        # Act
        result = ServiceManager.install_service()
        
        # Assert
        self.assertFalse(result)
        mock_logger.error.assert_called_with("pywin32 not available - cannot install service")
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.logger')
    def test_install_service_failure(self, mock_logger, mock_win32serviceutil):
        """Test service installation handles errors gracefully."""
        # Arrange
        mock_win32serviceutil.InstallService.side_effect = Exception("Installation failed")
        
        # Act
        result = ServiceManager.install_service()
        
        # Assert
        self.assertFalse(result)
        mock_logger.error.assert_called()
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.ServiceManager.stop_service')
    @patch('src.service_manager.logger')
    def test_remove_service_success(self, mock_logger, mock_stop, mock_win32serviceutil):
        """Test successful service removal."""
        # Arrange
        mock_stop.return_value = True
        
        # Act
        result = ServiceManager.remove_service()
        
        # Assert
        self.assertTrue(result)
        mock_stop.assert_called_once()
        mock_win32serviceutil.RemoveService.assert_called_once_with(self.service_name)
        mock_logger.info.assert_called()
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.logger')
    def test_start_service_success(self, mock_logger, mock_win32serviceutil):
        """Test successful service start."""
        # Act
        result = ServiceManager.start_service()
        
        # Assert
        self.assertTrue(result)
        mock_win32serviceutil.StartService.assert_called_once_with(self.service_name)
        mock_logger.info.assert_called()
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.logger')
    def test_start_service_failure(self, mock_logger, mock_win32serviceutil):
        """Test service start handles errors gracefully."""
        # Arrange
        mock_win32serviceutil.StartService.side_effect = Exception("Start failed")
        
        # Act
        result = ServiceManager.start_service()
        
        # Assert
        self.assertFalse(result)
        mock_logger.error.assert_called()
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.logger')
    def test_stop_service_success(self, mock_logger, mock_win32serviceutil):
        """Test successful service stop."""
        # Act
        result = ServiceManager.stop_service()
        
        # Assert
        self.assertTrue(result)
        mock_win32serviceutil.StopService.assert_called_once_with(self.service_name)
        mock_logger.info.assert_called()
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.logger')
    def test_stop_service_failure(self, mock_logger, mock_win32serviceutil):
        """Test service stop handles errors gracefully."""
        # Arrange
        mock_win32serviceutil.StopService.side_effect = Exception("Stop failed")
        
        # Act
        result = ServiceManager.stop_service()
        
        # Assert
        self.assertFalse(result)
        mock_logger.error.assert_called()
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.logger')
    def test_restart_service_success(self, mock_logger, mock_win32serviceutil):
        """Test successful service restart."""
        # Act
        result = ServiceManager.restart_service()
        
        # Assert
        self.assertTrue(result)
        mock_win32serviceutil.RestartService.assert_called_once_with(self.service_name)
        mock_logger.info.assert_called()
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.win32service')
    @patch('src.service_manager.logger')
    def test_get_service_status_running(self, mock_logger, mock_win32service, mock_win32serviceutil):
        """Test getting service status when running."""
        # Arrange
        mock_win32service.SERVICE_RUNNING = 4
        mock_status = (None, 4, 0, 0, 0, 0, 0)
        mock_win32serviceutil.QueryServiceStatus.return_value = mock_status
        
        # Act
        result = ServiceManager.get_service_status()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "running")
        self.assertEqual(result["status_code"], 4)
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.win32service')
    @patch('src.service_manager.logger')
    def test_get_service_status_stopped(self, mock_logger, mock_win32service, mock_win32serviceutil):
        """Test getting service status when stopped."""
        # Arrange
        mock_win32service.SERVICE_STOPPED = 1
        mock_status = (None, 1, 0, 0, 0, 0, 0)
        mock_win32serviceutil.QueryServiceStatus.return_value = mock_status
        
        # Act
        result = ServiceManager.get_service_status()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["status_code"], 1)
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.logger')
    def test_get_service_status_failure(self, mock_logger, mock_win32serviceutil):
        """Test getting service status handles errors gracefully."""
        # Arrange
        mock_win32serviceutil.QueryServiceStatus.side_effect = Exception("Query failed")
        
        # Act
        result = ServiceManager.get_service_status()
        
        # Assert
        self.assertIsNone(result)
        mock_logger.error.assert_called()
    
    @patch('src.service_manager.win32service')
    @patch('src.service_manager.logger')
    def test_configure_service_recovery(self, mock_logger, mock_win32service):
        """Test service recovery configuration."""
        # Arrange
        mock_hscm = MagicMock()
        mock_hs = MagicMock()
        mock_win32service.OpenSCManager.return_value = mock_hscm
        mock_win32service.OpenService.return_value = mock_hs
        mock_win32service.SC_ACTION_RESTART = 1
        
        # Act
        ServiceManager._configure_service_recovery()
        
        # Assert
        mock_win32service.OpenSCManager.assert_called_once()
        mock_win32service.OpenService.assert_called_once()
        mock_win32service.ChangeServiceConfig2.assert_called_once()
        mock_win32service.CloseServiceHandle.assert_called()
    
    @patch('src.service_manager.win32service')
    @patch('src.service_manager.win32security')
    @patch('src.service_manager.logger')
    def test_set_service_security(self, mock_logger, mock_win32security, mock_win32service):
        """Test service security configuration."""
        # Arrange
        mock_hscm = MagicMock()
        mock_hs = MagicMock()
        mock_sd = MagicMock()
        mock_dacl = MagicMock()
        mock_new_dacl = MagicMock()
        
        mock_win32service.OpenSCManager.return_value = mock_hscm
        mock_win32service.OpenService.return_value = mock_hs
        mock_win32service.QueryServiceObjectSecurity.return_value = mock_sd
        mock_sd.GetSecurityDescriptorDacl.return_value = mock_dacl
        mock_win32security.ACL.return_value = mock_new_dacl
        mock_win32security.CreateWellKnownSid.return_value = b'mock_sid'
        
        # Act
        ServiceManager._set_service_security()
        
        # Assert
        mock_win32service.OpenSCManager.assert_called_once()
        mock_win32service.OpenService.assert_called_once()
        mock_win32service.QueryServiceObjectSecurity.assert_called_once()
        mock_win32service.SetServiceObjectSecurity.assert_called_once()


class TestMonitoringService(unittest.TestCase):
    """Test cases for MonitoringService class."""
    
    @patch('src.service_manager.win32event')
    @patch('src.service_manager.win32serviceutil')
    def test_service_initialization(self, mock_win32serviceutil, mock_win32event):
        """Test service initialization."""
        # Arrange
        mock_event = MagicMock()
        mock_win32event.CreateEvent.return_value = mock_event
        mock_win32serviceutil.ServiceFramework = object  # Use object as base
        
        # Act
        service = MonitoringService(['service_name'])
        
        # Assert
        self.assertIsNotNone(service.stop_event)
        # Check attributes exist (they may be mocked)
        self.assertTrue(hasattr(service, 'is_running'))
        self.assertTrue(hasattr(service, 'monitoring_loop'))
    
    @patch('src.service_manager.win32event')
    @patch('src.service_manager.win32service')
    @patch('src.service_manager.win32serviceutil')
    def test_service_stop(self, mock_win32serviceutil, mock_win32service, mock_win32event):
        """Test service stop request handling."""
        # Arrange
        mock_event = MagicMock()
        mock_win32event.CreateEvent.return_value = mock_event
        mock_win32serviceutil.ServiceFramework = object  # Use object as base
        
        service = MonitoringService(['service_name'])
        service.is_running = True
        service.ReportServiceStatus = MagicMock()
        
        # Act
        service.SvcStop()
        
        # Assert
        self.assertFalse(service.is_running)
        mock_win32event.SetEvent.assert_called_once_with(mock_event)
        service.ReportServiceStatus.assert_called_once()
    
    @patch('src.service_manager.servicemanager')
    @patch('src.service_manager.win32event')
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.Config')
    def test_service_main_loop(self, mock_config_class, mock_win32serviceutil, 
                               mock_win32event, mock_servicemanager):
        """Test service main loop execution."""
        # Arrange
        mock_event = MagicMock()
        mock_win32event.CreateEvent.return_value = mock_event
        mock_win32event.WaitForSingleObject.return_value = mock_win32event.WAIT_OBJECT_0
        mock_win32event.WAIT_OBJECT_0 = 0
        mock_win32serviceutil.ServiceFramework = object  # Use object as base
        
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        
        # Mock MonitoringLoop at the point of import
        with patch('src.service_manager.MonitoringLoop') as mock_monitoring_loop_class:
            mock_monitoring_loop = MagicMock()
            mock_monitoring_loop.run_once = MagicMock()
            mock_monitoring_loop.stop = MagicMock()
            mock_monitoring_loop_class.return_value = mock_monitoring_loop
            
            service = MonitoringService(['service_name'])
            
            # Act
            service.SvcDoRun()
            
            # Assert
            mock_config_class.assert_called_once()
            mock_monitoring_loop_class.assert_called_once_with(mock_config)
            mock_servicemanager.LogMsg.assert_called()


class TestServiceManagerEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    @patch('src.service_manager.win32serviceutil', None)
    def test_all_operations_fail_without_pywin32(self):
        """Test that all operations fail gracefully without pywin32."""
        # Test install
        self.assertFalse(ServiceManager.install_service())
        
        # Test remove
        self.assertFalse(ServiceManager.remove_service())
        
        # Test start
        self.assertFalse(ServiceManager.start_service())
        
        # Test stop
        self.assertFalse(ServiceManager.stop_service())
        
        # Test restart
        self.assertFalse(ServiceManager.restart_service())
        
        # Test status
        self.assertIsNone(ServiceManager.get_service_status())
    
    @patch('src.service_manager.win32service')
    @patch('src.service_manager.logger')
    def test_configure_recovery_handles_errors(self, mock_logger, mock_win32service):
        """Test that recovery configuration handles errors gracefully."""
        # Arrange
        mock_win32service.OpenSCManager.side_effect = Exception("Access denied")
        
        # Act
        ServiceManager._configure_service_recovery()
        
        # Assert
        mock_logger.warning.assert_called()
    
    @patch('src.service_manager.win32service')
    @patch('src.service_manager.logger')
    def test_set_security_handles_errors(self, mock_logger, mock_win32service):
        """Test that security configuration handles errors gracefully."""
        # Arrange
        mock_win32service.OpenSCManager.side_effect = Exception("Access denied")
        
        # Act
        ServiceManager._set_service_security()
        
        # Assert
        mock_logger.warning.assert_called()


if __name__ == '__main__':
    unittest.main()

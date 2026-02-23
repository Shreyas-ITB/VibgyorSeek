"""
Integration tests for the Service Manager module.

Tests service lifecycle and integration with monitoring components.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import time

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


class TestServiceLifecycle(unittest.TestCase):
    """Test complete service lifecycle scenarios."""
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.win32service')
    @patch('src.service_manager.ServiceManager._configure_service_recovery')
    @patch('src.service_manager.ServiceManager._set_service_security')
    def test_install_and_configure_service(self, mock_set_security, mock_configure_recovery,
                                          mock_win32service, mock_win32serviceutil):
        """Test installing service with full configuration."""
        # Arrange
        mock_win32service.SERVICE_AUTO_START = 2
        
        # Act
        result = ServiceManager.install_service()
        
        # Assert
        self.assertTrue(result)
        mock_win32serviceutil.InstallService.assert_called_once()
        mock_configure_recovery.assert_called_once()
        mock_set_security.assert_called_once()
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.ServiceManager.stop_service')
    def test_remove_service_stops_first(self, mock_stop, mock_win32serviceutil):
        """Test that removing service stops it first."""
        # Arrange
        mock_stop.return_value = True
        
        # Act
        result = ServiceManager.remove_service()
        
        # Assert
        self.assertTrue(result)
        mock_stop.assert_called_once()
        mock_win32serviceutil.RemoveService.assert_called_once()
    
    @patch('src.service_manager.win32serviceutil')
    def test_service_lifecycle_sequence(self, mock_win32serviceutil):
        """Test complete install -> start -> stop -> remove sequence."""
        # Install
        result = ServiceManager.install_service()
        self.assertTrue(result)
        
        # Start
        result = ServiceManager.start_service()
        self.assertTrue(result)
        
        # Stop
        result = ServiceManager.stop_service()
        self.assertTrue(result)
        
        # Remove
        result = ServiceManager.remove_service()
        self.assertTrue(result)
        
        # Verify call sequence
        self.assertEqual(mock_win32serviceutil.InstallService.call_count, 1)
        self.assertEqual(mock_win32serviceutil.StartService.call_count, 1)
        self.assertEqual(mock_win32serviceutil.StopService.call_count, 2)  # Once in stop, once in remove
        self.assertEqual(mock_win32serviceutil.RemoveService.call_count, 1)


class TestServiceWithMonitoringLoop(unittest.TestCase):
    """Test service integration with monitoring loop."""
    
    @patch('src.service_manager.servicemanager')
    @patch('src.service_manager.win32event')
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.Config')
    def test_service_runs_monitoring_loop(self, mock_config_class, mock_win32serviceutil,
                                         mock_win32event, mock_servicemanager):
        """Test that service properly runs monitoring loop."""
        # Arrange
        mock_event = MagicMock()
        mock_win32event.CreateEvent.return_value = mock_event
        mock_win32event.WAIT_OBJECT_0 = 0
        mock_win32serviceutil.ServiceFramework = object  # Use object as base
        
        # Simulate stop after one iteration
        mock_win32event.WaitForSingleObject.return_value = mock_win32event.WAIT_OBJECT_0
        
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
            mock_monitoring_loop_class.assert_called_once_with(mock_config)
            mock_monitoring_loop.stop.assert_called_once()
    
    @patch('src.service_manager.servicemanager')
    @patch('src.service_manager.win32event')
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.Config')
    @patch('src.service_manager.logger')
    def test_service_continues_on_monitoring_error(self, mock_logger, mock_config_class,
                                                   mock_win32serviceutil, mock_win32event, mock_servicemanager):
        """Test that service continues running even if monitoring loop has errors."""
        # Arrange
        mock_event = MagicMock()
        mock_win32event.CreateEvent.return_value = mock_event
        mock_win32event.WAIT_OBJECT_0 = 0
        mock_win32event.WAIT_TIMEOUT = 258
        mock_win32serviceutil.ServiceFramework = object  # Use object as base
        
        # First call returns timeout (continue), second returns stop signal
        mock_win32event.WaitForSingleObject.side_effect = [
            mock_win32event.WAIT_TIMEOUT,
            mock_win32event.WAIT_OBJECT_0
        ]
        
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        
        # Mock MonitoringLoop at the point of import
        with patch('src.service_manager.MonitoringLoop') as mock_monitoring_loop_class:
            mock_monitoring_loop = MagicMock()
            # First call raises error, should be caught and logged
            mock_monitoring_loop.run_once.side_effect = [
                Exception("Monitoring error"),
                None
            ]
            mock_monitoring_loop.stop = MagicMock()
            mock_monitoring_loop_class.return_value = mock_monitoring_loop
            
            service = MonitoringService(['service_name'])
            
            # Act
            service.SvcDoRun()
            
            # Assert
            # Service should log error but continue
            mock_logger.error.assert_called()
            mock_monitoring_loop.stop.assert_called_once()


class TestServiceStatusReporting(unittest.TestCase):
    """Test service status reporting functionality."""
    
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.win32service')
    def test_status_reports_all_states(self, mock_win32service, mock_win32serviceutil):
        """Test that status correctly reports different service states."""
        # Define status constants
        mock_win32service.SERVICE_STOPPED = 1
        mock_win32service.SERVICE_START_PENDING = 2
        mock_win32service.SERVICE_STOP_PENDING = 3
        mock_win32service.SERVICE_RUNNING = 4
        mock_win32service.SERVICE_CONTINUE_PENDING = 5
        mock_win32service.SERVICE_PAUSE_PENDING = 6
        mock_win32service.SERVICE_PAUSED = 7
        
        test_cases = [
            (1, "stopped"),
            (2, "starting"),
            (3, "stopping"),
            (4, "running"),
            (5, "continuing"),
            (6, "pausing"),
            (7, "paused")
        ]
        
        for status_code, expected_status in test_cases:
            with self.subTest(status_code=status_code):
                # Arrange
                mock_status = (None, status_code, 0, 0, 0, 0, 0)
                mock_win32serviceutil.QueryServiceStatus.return_value = mock_status
                
                # Act
                result = ServiceManager.get_service_status()
                
                # Assert
                self.assertIsNotNone(result)
                self.assertEqual(result["status"], expected_status)
                self.assertEqual(result["status_code"], status_code)


class TestServiceRecoveryConfiguration(unittest.TestCase):
    """Test service recovery and restart configuration."""
    
    @patch('src.service_manager.win32service')
    def test_recovery_configures_restart_actions(self, mock_win32service):
        """Test that recovery configuration sets up restart actions."""
        # Arrange
        mock_hscm = MagicMock()
        mock_hs = MagicMock()
        mock_win32service.OpenSCManager.return_value = mock_hscm
        mock_win32service.OpenService.return_value = mock_hs
        mock_win32service.SC_ACTION_RESTART = 1
        mock_win32service.SC_MANAGER_ALL_ACCESS = 0xF003F
        mock_win32service.SERVICE_ALL_ACCESS = 0xF01FF
        mock_win32service.SERVICE_CONFIG_FAILURE_ACTIONS = 2
        
        # Act
        ServiceManager._configure_service_recovery()
        
        # Assert
        mock_win32service.ChangeServiceConfig2.assert_called_once()
        call_args = mock_win32service.ChangeServiceConfig2.call_args
        
        # Verify the failure actions configuration
        self.assertEqual(call_args[0][0], mock_hs)
        self.assertEqual(call_args[0][1], mock_win32service.SERVICE_CONFIG_FAILURE_ACTIONS)
        
        failure_actions = call_args[0][2]
        self.assertIn('Actions', failure_actions)
        self.assertEqual(len(failure_actions['Actions']), 3)  # Three restart actions


class TestServiceSecurityConfiguration(unittest.TestCase):
    """Test service security and permission configuration."""
    
    @patch('src.service_manager.win32service')
    @patch('src.service_manager.win32security')
    def test_security_restricts_non_admin_access(self, mock_win32security, mock_win32service):
        """Test that security configuration restricts non-admin users."""
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
        
        # Mock SID creation
        admin_sid = b'admin_sid'
        system_sid = b'system_sid'
        users_sid = b'users_sid'
        
        mock_win32security.CreateWellKnownSid.side_effect = [
            admin_sid,
            system_sid,
            users_sid
        ]
        
        mock_win32service.SERVICE_ALL_ACCESS = 0xF01FF
        mock_win32service.SERVICE_QUERY_STATUS = 0x0004
        mock_win32service.SERVICE_INTERROGATE = 0x0080
        
        # Act
        ServiceManager._set_service_security()
        
        # Assert
        # Verify three ACEs were added (admin, system, users)
        self.assertEqual(mock_new_dacl.AddAccessAllowedAce.call_count, 3)
        
        # Verify admin and system get full access
        admin_call = mock_new_dacl.AddAccessAllowedAce.call_args_list[0]
        self.assertEqual(admin_call[0][1], mock_win32service.SERVICE_ALL_ACCESS)
        
        system_call = mock_new_dacl.AddAccessAllowedAce.call_args_list[1]
        self.assertEqual(system_call[0][1], mock_win32service.SERVICE_ALL_ACCESS)
        
        # Verify users get limited access (query status only, no stop/start)
        users_call = mock_new_dacl.AddAccessAllowedAce.call_args_list[2]
        expected_users_access = (
            mock_win32service.SERVICE_QUERY_STATUS | 
            mock_win32service.SERVICE_INTERROGATE
        )
        self.assertEqual(users_call[0][1], expected_users_access)
        
        # Verify security descriptor was applied
        mock_win32service.SetServiceObjectSecurity.assert_called_once()


class TestServiceErrorHandling(unittest.TestCase):
    """Test service error handling and resilience."""
    
    @patch('src.service_manager.servicemanager')
    @patch('src.service_manager.win32event')
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.Config')
    @patch('src.service_manager.logger')
    def test_service_handles_config_load_error(self, mock_logger, mock_config_class,
                                               mock_win32serviceutil, mock_win32event, mock_servicemanager):
        """Test that service handles configuration loading errors."""
        # Arrange
        mock_event = MagicMock()
        mock_win32event.CreateEvent.return_value = mock_event
        mock_config_class.side_effect = Exception("Config error")
        mock_win32serviceutil.ServiceFramework = object  # Use object as base
        
        service = MonitoringService(['service_name'])
        
        # Act
        service.SvcDoRun()
        
        # Assert
        mock_logger.error.assert_called()
        mock_servicemanager.LogErrorMsg.assert_called()
    
    @patch('src.service_manager.servicemanager')
    @patch('src.service_manager.win32event')
    @patch('src.service_manager.win32serviceutil')
    @patch('src.service_manager.Config')
    @patch('src.service_manager.logger')
    def test_service_handles_monitoring_loop_init_error(self, mock_logger, mock_config_class,
                                                        mock_win32serviceutil, mock_win32event, mock_servicemanager):
        """Test that service handles monitoring loop initialization errors."""
        # Arrange
        mock_event = MagicMock()
        mock_win32event.CreateEvent.return_value = mock_event
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_win32serviceutil.ServiceFramework = object  # Use object as base
        
        # Mock MonitoringLoop at the point of import
        with patch('src.service_manager.MonitoringLoop') as mock_monitoring_loop_class:
            mock_monitoring_loop_class.side_effect = Exception("Init error")
            
            service = MonitoringService(['service_name'])
            
            # Act & Assert
            with self.assertRaises(Exception):
                service.SvcDoRun()
            
            mock_logger.error.assert_called()


if __name__ == '__main__':
    unittest.main()

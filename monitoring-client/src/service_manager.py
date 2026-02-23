"""
Service Manager Module for VibgyorSeek Employee Monitoring System

This module implements Windows service functionality using pywin32.
It handles service registration, lifecycle management, and ensures the
monitoring client runs as a background service with automatic startup.

Requirements: 7.1, 7.2, 7.3, 7.4
"""

import sys
import os
import time
import traceback
from pathlib import Path

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    import win32api
    import win32con
    import win32security
    import ntsecuritycon
except ImportError:
    # Allow module to be imported on non-Windows systems for testing
    win32serviceutil = None
    win32service = None
    win32event = None
    servicemanager = None
    win32api = None
    win32con = None
    win32security = None
    ntsecuritycon = None

from src.logger import get_logger
from src.config import Config

logger = get_logger()


class MonitoringService(win32serviceutil.ServiceFramework if win32serviceutil else object):
    """
    Windows service wrapper for the VibgyorSeek monitoring client.
    
    This class implements the Windows service interface and manages
    the monitoring loop lifecycle.
    """
    
    # Service configuration
    _svc_name_ = "VibgyorSeekMonitoring"
    _svc_display_name_ = "VibgyorSeek Employee Monitoring Service"
    _svc_description_ = "Monitors employee activity and transmits data to the central server"
    
    def __init__(self, args):
        """Initialize the service."""
        if win32serviceutil is None:
            raise RuntimeError("pywin32 is required for Windows service functionality")
        
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = False
        self.monitoring_loop = None
        
    def SvcStop(self):
        """Handle service stop request."""
        logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_running = False
        
    def SvcDoRun(self):
        """Main service execution method."""
        try:
            logger.info("Service starting")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            
            self.is_running = True
            self.main()
            
        except Exception as e:
            logger.error(f"Service error: {e}")
            logger.error(traceback.format_exc())
            servicemanager.LogErrorMsg(f"Service error: {e}")
            
    def main(self):
        """Main service loop."""
        try:
            # Import here to avoid circular dependencies
            from src.monitoring_loop import MonitoringLoop
            
            # Load configuration
            config = Config()
            
            # Create and start monitoring loop
            self.monitoring_loop = MonitoringLoop(config)
            logger.info("Monitoring loop initialized")
            
            # Run monitoring loop in a separate thread-like manner
            # Check stop event periodically
            while self.is_running:
                # Check if stop was requested
                rc = win32event.WaitForSingleObject(self.stop_event, 1000)
                if rc == win32event.WAIT_OBJECT_0:
                    # Stop event was signaled
                    break
                
                # Run one iteration of monitoring
                # The monitoring loop should handle its own timing
                try:
                    if hasattr(self.monitoring_loop, 'run_once'):
                        self.monitoring_loop.run_once()
                    else:
                        # If monitoring loop doesn't have run_once, 
                        # just sleep and let it run in background
                        time.sleep(1)
                except Exception as e:
                    logger.error(f"Error in monitoring loop iteration: {e}")
                    # Continue running despite errors (Requirement 7.5)
                    time.sleep(5)
            
            # Cleanup
            if self.monitoring_loop and hasattr(self.monitoring_loop, 'stop'):
                self.monitoring_loop.stop()
            
            logger.info("Service stopped")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, '')
            )
            
        except Exception as e:
            logger.error(f"Fatal error in service main loop: {e}")
            logger.error(traceback.format_exc())
            raise


class ServiceManager:
    """
    Manager class for Windows service operations.
    
    Provides methods to install, remove, start, stop, and configure
    the monitoring service.
    """
    
    SERVICE_NAME = "VBSeek"
    
    @staticmethod
    def install_service():
        """
        Install the monitoring service.
        
        Configures the service to start automatically on boot and
        sets appropriate security permissions.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        if win32serviceutil is None:
            logger.error("pywin32 not available - cannot install service")
            return False
        
        try:
            # Get the path to the Python executable and this script
            python_exe = sys.executable
            script_path = os.path.abspath(__file__)
            
            # Install the service using win32serviceutil
            # The service class will be registered when this module is run as __main__
            win32serviceutil.InstallService(
                MonitoringService._svc_reg_class_ if hasattr(MonitoringService, '_svc_reg_class_') else None,
                MonitoringService._svc_name_,
                MonitoringService._svc_display_name_,
                startType=win32service.SERVICE_AUTO_START,
                description=MonitoringService._svc_description_
            )
            
            logger.info(f"Service '{ServiceManager.SERVICE_NAME}' installed successfully")
            
            # Configure service to restart on failure
            ServiceManager._configure_service_recovery()
            
            # Set service security to prevent non-admin termination
            ServiceManager._set_service_security()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to install service: {e}")
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def remove_service():
        """
        Remove the monitoring service.
        
        Returns:
            bool: True if removal successful, False otherwise
        """
        if win32serviceutil is None:
            logger.error("pywin32 not available - cannot remove service")
            return False
        
        try:
            # Stop the service if running
            ServiceManager.stop_service()
            
            # Remove the service
            win32serviceutil.RemoveService(ServiceManager.SERVICE_NAME)
            logger.info(f"Service '{ServiceManager.SERVICE_NAME}' removed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove service: {e}")
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def start_service():
        """
        Start the monitoring service.
        
        Returns:
            bool: True if start successful, False otherwise
        """
        if win32serviceutil is None:
            logger.error("pywin32 not available - cannot start service")
            return False
        
        try:
            win32serviceutil.StartService(ServiceManager.SERVICE_NAME)
            logger.info(f"Service '{ServiceManager.SERVICE_NAME}' started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def stop_service():
        """
        Stop the monitoring service.
        
        Returns:
            bool: True if stop successful, False otherwise
        """
        if win32serviceutil is None:
            logger.error("pywin32 not available - cannot stop service")
            return False
        
        try:
            win32serviceutil.StopService(ServiceManager.SERVICE_NAME)
            logger.info(f"Service '{ServiceManager.SERVICE_NAME}' stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def restart_service():
        """
        Restart the monitoring service.
        
        Returns:
            bool: True if restart successful, False otherwise
        """
        if win32serviceutil is None:
            logger.error("pywin32 not available - cannot restart service")
            return False
        
        try:
            win32serviceutil.RestartService(ServiceManager.SERVICE_NAME)
            logger.info(f"Service '{ServiceManager.SERVICE_NAME}' restarted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart service: {e}")
            logger.error(traceback.format_exc())
            return False
    
    @staticmethod
    def get_service_status():
        """
        Get the current status of the monitoring service.
        
        Returns:
            dict: Service status information or None if error
        """
        if win32serviceutil is None:
            logger.error("pywin32 not available - cannot get service status")
            return None
        
        try:
            status = win32serviceutil.QueryServiceStatus(ServiceManager.SERVICE_NAME)
            
            # Map status codes to readable strings
            status_map = {
                win32service.SERVICE_STOPPED: "stopped",
                win32service.SERVICE_START_PENDING: "starting",
                win32service.SERVICE_STOP_PENDING: "stopping",
                win32service.SERVICE_RUNNING: "running",
                win32service.SERVICE_CONTINUE_PENDING: "continuing",
                win32service.SERVICE_PAUSE_PENDING: "pausing",
                win32service.SERVICE_PAUSED: "paused"
            }
            
            return {
                "status": status_map.get(status[1], "unknown"),
                "status_code": status[1],
                "controls_accepted": status[2],
                "exit_code": status[3],
                "service_specific_exit_code": status[4],
                "check_point": status[5],
                "wait_hint": status[6]
            }
            
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return None
    
    @staticmethod
    def _configure_service_recovery():
        """
        Configure service recovery options to restart on failure.
        
        This ensures the service automatically restarts if it crashes.
        """
        if win32api is None or win32con is None:
            return
        
        try:
            # Open service control manager
            hscm = win32service.OpenSCManager(
                None,
                None,
                win32service.SC_MANAGER_ALL_ACCESS
            )
            
            try:
                # Open the service
                hs = win32service.OpenService(
                    hscm,
                    ServiceManager.SERVICE_NAME,
                    win32service.SERVICE_ALL_ACCESS
                )
                
                try:
                    # Configure service to restart on failure
                    # Restart after 1 minute on first failure
                    # Restart after 2 minutes on second failure
                    # Restart after 5 minutes on subsequent failures
                    service_failure_actions = {
                        'ResetPeriod': 86400,  # Reset failure count after 24 hours
                        'RebootMsg': '',
                        'Command': '',
                        'Actions': [
                            (win32service.SC_ACTION_RESTART, 60000),   # 1 minute
                            (win32service.SC_ACTION_RESTART, 120000),  # 2 minutes
                            (win32service.SC_ACTION_RESTART, 300000)   # 5 minutes
                        ]
                    }
                    
                    win32service.ChangeServiceConfig2(
                        hs,
                        win32service.SERVICE_CONFIG_FAILURE_ACTIONS,
                        service_failure_actions
                    )
                    
                    logger.info("Service recovery options configured")
                    
                finally:
                    win32service.CloseServiceHandle(hs)
            finally:
                win32service.CloseServiceHandle(hscm)
                
        except Exception as e:
            logger.warning(f"Failed to configure service recovery: {e}")
    
    @staticmethod
    def _set_service_security():
        """
        Set service security to prevent termination by non-admin users.
        
        This implements Requirement 7.4 by restricting service control
        to administrators only.
        """
        if win32security is None or ntsecuritycon is None:
            return
        
        try:
            # Open service control manager
            hscm = win32service.OpenSCManager(
                None,
                None,
                win32service.SC_MANAGER_ALL_ACCESS
            )
            
            try:
                # Open the service
                hs = win32service.OpenService(
                    hscm,
                    ServiceManager.SERVICE_NAME,
                    win32service.SERVICE_ALL_ACCESS | win32service.READ_CONTROL | win32service.WRITE_DAC
                )
                
                try:
                    # Get current security descriptor
                    sd = win32service.QueryServiceObjectSecurity(
                        hs,
                        win32security.DACL_SECURITY_INFORMATION
                    )
                    
                    # Get the DACL
                    dacl = sd.GetSecurityDescriptorDacl()
                    
                    # Create new DACL with restricted permissions
                    new_dacl = win32security.ACL()
                    
                    # Add ACE for Administrators (full control)
                    admin_sid = win32security.CreateWellKnownSid(
                        win32security.WinBuiltinAdministratorsSid
                    )
                    new_dacl.AddAccessAllowedAce(
                        win32security.ACL_REVISION,
                        win32service.SERVICE_ALL_ACCESS,
                        admin_sid
                    )
                    
                    # Add ACE for SYSTEM (full control)
                    system_sid = win32security.CreateWellKnownSid(
                        win32security.WinLocalSystemSid
                    )
                    new_dacl.AddAccessAllowedAce(
                        win32security.ACL_REVISION,
                        win32service.SERVICE_ALL_ACCESS,
                        system_sid
                    )
                    
                    # Add ACE for Users (read-only, no stop/start)
                    users_sid = win32security.CreateWellKnownSid(
                        win32security.WinBuiltinUsersSid
                    )
                    new_dacl.AddAccessAllowedAce(
                        win32security.ACL_REVISION,
                        win32service.SERVICE_QUERY_STATUS | win32service.SERVICE_INTERROGATE,
                        users_sid
                    )
                    
                    # Set the new DACL
                    sd.SetSecurityDescriptorDacl(1, new_dacl, 0)
                    
                    # Apply the security descriptor
                    win32service.SetServiceObjectSecurity(
                        hs,
                        win32security.DACL_SECURITY_INFORMATION,
                        sd
                    )
                    
                    logger.info("Service security configured - only admins can control service")
                    
                finally:
                    win32service.CloseServiceHandle(hs)
            finally:
                win32service.CloseServiceHandle(hscm)
                
        except Exception as e:
            logger.warning(f"Failed to set service security: {e}")


def main():
    """
    Main entry point for service management.
    
    Handles command-line arguments for service installation,
    removal, and execution.
    """
    if len(sys.argv) == 1:
        # No arguments - try to start the service
        if win32serviceutil is not None:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(MonitoringService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            print("Error: pywin32 not available")
            sys.exit(1)
    else:
        # Handle command-line arguments
        if win32serviceutil is not None:
            win32serviceutil.HandleCommandLine(MonitoringService)
        else:
            print("Error: pywin32 not available")
            sys.exit(1)


if __name__ == '__main__':
    main()

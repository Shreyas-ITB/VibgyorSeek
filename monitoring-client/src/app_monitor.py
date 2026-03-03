"""
Application Monitor Module

This module monitors running applications on the system.
It uses psutil to enumerate processes and platform-specific APIs
to identify the foreground (active) application.

Requirements: 3.1, 3.2, 3.3
"""

import psutil
import logging
from typing import List, Dict, Optional
import platform

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import win32gui
        import win32process
        WINDOWS_API_AVAILABLE = True
    except ImportError:
        WINDOWS_API_AVAILABLE = False
        logging.warning("win32gui/win32process not available. Foreground detection disabled.")
elif platform.system() == "Darwin":  # macOS
    try:
        from AppKit import NSWorkspace
        MACOS_API_AVAILABLE = True
    except ImportError:
        MACOS_API_AVAILABLE = False
        logging.warning("AppKit not available. Foreground detection disabled.")
else:  # Linux
    LINUX_API_AVAILABLE = True


logger = logging.getLogger(__name__)


class ApplicationMonitor:
    """Monitors running applications and identifies the foreground application."""
    
    # System processes to exclude from the application list
    SYSTEM_PROCESS_NAMES = {
        'system', 'registry', 'smss.exe', 'csrss.exe', 'wininit.exe',
        'services.exe', 'lsass.exe', 'svchost.exe', 'winlogon.exe',
        'dwm.exe', 'conhost.exe', 'fontdrvhost.exe', 'taskhostw.exe',
        'systemd', 'kthreadd', 'init', 'kernel', 'kworker',
        'system idle process', 'lsaiso.exe', 'spoolsv.exe', 'wininit.exe',
        'wmiprvse.exe', 'securityhealthservice.exe', 'memcompression',
        'unsecapp.exe', 'officeclick torun.exe', 'rtkaudservice64.exe',
        'mpdefendercoreservice.exe', 'sqlwriter.exe', 'msmpsvc.exe',
        'msmpseng.exe', 'wslservice.exe', 'aggregatorhost.exe',
        'runtimebroker.exe', 'ngciso.exe', 'searchindexer.exe',
        'crossdeviceresume.exe', 'ctfmon.exe', 'sqlceip.exe',
        'nissrv.exe', 'monotificationux.exe', 'windowspackagemanagerserver.exe',
        'widgetservice.exe', 'sqlservr.exe', 'sihost.exe', 'audiodg.exe',
        'wlanext.exe', 'searchhost.exe', 'startmenuexperiencehost.exe',
        'shellexperiencehost.exe', 'textinputhost.exe', 'shellhost.exe',
        'applicationframehost.exe', 'useroobebroker.exe'
    }
    
    def __init__(self):
        """Initialize the application monitor."""
        self.platform = platform.system()
        logger.info(f"ApplicationMonitor initialized for platform: {self.platform}")
    
    def get_running_applications(self) -> List[Dict[str, any]]:
        """
        Get list of currently running user-facing applications.
        
        Returns:
            List of dictionaries containing application information:
            [
                {"name": "Chrome", "active": True},
                {"name": "VSCode", "active": False},
                ...
            ]
        
        Requirements: 3.1, 3.2, 3.3
        """
        try:
            # Get foreground application PID
            foreground_pid = self._get_foreground_pid()
            
            # Get all running processes
            applications = []
            seen_names = set()
            
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name']
                    
                    # Filter out system processes
                    if self._is_user_application(proc, proc_name):
                        # Avoid duplicates (same app name)
                        if proc_name.lower() not in seen_names:
                            seen_names.add(proc_name.lower())
                            
                            applications.append({
                                "name": proc_name,
                                "active": proc_info['pid'] == foreground_pid
                            })
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Skip processes we can't access
                    continue
            
            logger.debug(f"Found {len(applications)} user-facing applications")
            return applications
        
        except Exception as e:
            logger.error(f"Error getting running applications: {e}")
            return []
    
    def _is_user_application(self, proc: psutil.Process, proc_name: str) -> bool:
        """
        Determine if a process is a user-facing application.
        
        Args:
            proc: psutil.Process object
            proc_name: Name of the process
        
        Returns:
            True if the process is a user-facing application, False otherwise
        """
        # Exclude system processes by name
        if proc_name.lower() in self.SYSTEM_PROCESS_NAMES:
            return False
        
        # Exclude processes without a name
        if not proc_name or proc_name.strip() == '':
            return False
        
        try:
            # On Windows, check if process has a window
            if self.platform == "Windows" and WINDOWS_API_AVAILABLE:
                # This is a heuristic: user applications typically have windows
                # We'll consider any process that's not in the system list as a potential app
                pass
            
            # Additional filtering: exclude very short-lived processes
            # and processes with very low CPU usage that are likely background services
            return True
        
        except Exception:
            return False
    
    def _get_foreground_pid(self) -> Optional[int]:
        """
        Get the PID of the foreground (active) application.
        
        Returns:
            PID of foreground application, or None if unable to determine
        
        Requirements: 3.2
        """
        try:
            if self.platform == "Windows":
                return self._get_foreground_pid_windows()
            elif self.platform == "Darwin":
                return self._get_foreground_pid_macos()
            else:  # Linux
                return self._get_foreground_pid_linux()
        
        except Exception as e:
            logger.warning(f"Unable to determine foreground application: {e}")
            return None
    
    def _get_foreground_pid_windows(self) -> Optional[int]:
        """Get foreground PID on Windows."""
        if not WINDOWS_API_AVAILABLE:
            return None
        
        try:
            # Get the foreground window handle
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                logger.debug("GetForegroundWindow returned 0")
                return None
            
            # Get window title for debugging
            try:
                window_title = win32gui.GetWindowText(hwnd)
                logger.debug(f"Foreground window: '{window_title}' (hwnd: {hwnd})")
            except:
                pass
            
            # Get the process ID from the window handle
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            if pid == 0:
                logger.debug("GetWindowThreadProcessId returned PID 0")
                return None
            
            logger.debug(f"Foreground PID: {pid}")
            return pid
        
        except Exception as e:
            logger.debug(f"Error getting foreground window on Windows: {e}")
            return None
    
    def _get_foreground_pid_macos(self) -> Optional[int]:
        """Get foreground PID on macOS."""
        if not MACOS_API_AVAILABLE:
            return None
        
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            if active_app:
                return active_app['NSApplicationProcessIdentifier']
            return None
        
        except Exception as e:
            logger.debug(f"Error getting foreground app on macOS: {e}")
            return None
    
    def _get_foreground_pid_linux(self) -> Optional[int]:
        """Get foreground PID on Linux."""
        try:
            # On Linux, we can use xdotool or similar tools
            # For now, we'll return None as this requires X11 access
            # This can be enhanced with subprocess calls to xdotool
            import subprocess
            
            result = subprocess.run(
                ['xdotool', 'getwindowfocus', 'getwindowpid'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                return int(result.stdout.strip())
            
            return None
        
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            # xdotool not available or command failed
            return None
        except Exception as e:
            logger.debug(f"Error getting foreground window on Linux: {e}")
            return None
    
    def get_application_names(self) -> List[str]:
        """
        Get list of application names only (without active status).
        
        Returns:
            List of application names
        """
        applications = self.get_running_applications()
        return [app['name'] for app in applications]
    
    def get_foreground_application(self) -> Optional[str]:
        """
        Get the name of the foreground (active) application.
        
        Returns:
            Name of foreground application, or None if unable to determine
        """
        # Direct approach: get foreground PID and look up process name
        foreground_pid = self._get_foreground_pid()
        
        if foreground_pid is None:
            return None
        
        try:
            proc = psutil.Process(foreground_pid)
            proc_name = proc.name()
            logger.debug(f"Foreground app: {proc_name} (PID: {foreground_pid})")
            return proc_name
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            logger.debug(f"Could not get process name for PID {foreground_pid}")
            return None

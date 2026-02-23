"""Configuration watcher module for detecting remote configuration changes with hot-reload."""

import os
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .logger import get_logger
from .config import Config, retrieve_client_id

logger = get_logger()


class EnvFileHandler(FileSystemEventHandler):
    """Handler for .env file changes that triggers hot-reload."""
    
    def __init__(self, callback: Callable):
        super().__init__()
        self.callback = callback
        self.last_modified = time.time()
        
    def on_modified(self, event):
        """Called when .env file is modified."""
        if event.src_path.endswith('.env'):
            # Debounce: only trigger if at least 2 seconds have passed
            current_time = time.time()
            if current_time - self.last_modified > 2:
                self.last_modified = current_time
                logger.info("📝 .env file changed, triggering hot-reload...")
                self.callback()


class ConfigWatcher:
    """Watches for configuration changes from the server and triggers hot-reload."""
    
    def __init__(self, config: Config, check_interval_seconds: int = 60, server_env_watcher=None):
        """
        Initialize the configuration watcher.
        
        Args:
            config: Current configuration instance
            check_interval_seconds: How often to check for updates (default: 60 seconds)
            server_env_watcher: ServerEnvWatcher instance to get server config
        """
        self.config = config
        self.check_interval = check_interval_seconds
        self.current_version = 0
        self.client_id = retrieve_client_id()
        self.running = False
        self.reload_callback = None
        self.observer = None
        self.env_path = Path(__file__).parent.parent / '.env'
        self.server_env_watcher = server_env_watcher
        
    def set_reload_callback(self, callback: Callable):
        """
        Set the callback function to be called when configuration needs to be reloaded.
        
        Args:
            callback: Function to call for hot-reload
        """
        self.reload_callback = callback
        logger.info("🔄 Hot-reload callback registered")
        
    def get_config_version(self) -> Optional[int]:
        """
        Fetch the current configuration version from the server.
        
        Returns:
            Configuration version number, or None if fetch failed
        """
        if not self.client_id:
            logger.warning("No client ID configured, skipping config check")
            return None
            
        try:
            # Extract base URL from server_url (remove /api/monitoring/data)
            base_url = self.config.server_url.replace('/api/monitoring/data', '')
            url = f"{base_url}/api/config/client/{self.client_id}/version"
            
            logger.debug(f"🌐 Fetching version from: {url}")
            
            response = requests.get(url, timeout=10)
            
            logger.debug(f"📊 Version response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                version = data.get('version', 0)
                logger.debug(f"✅ Server version: {version}")
                return version
            else:
                logger.warning(f"Failed to fetch config version: {response.status_code}")
                logger.debug(f"Response body: {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching config version: {e}", exc_info=True)
            print(f"❌ CONFIG WATCHER: Error fetching version - {e}")
            return None
    
    def fetch_and_apply_config(self) -> bool:
        """
        Fetch the latest configuration from server and update .env file.
        This will trigger the file watcher which will call the reload callback.
        
        Returns:
            True if configuration was updated, False otherwise
        """
        if not self.client_id:
            logger.error("❌ No client ID configured, cannot fetch config")
            return False
            
        try:
            # Extract base URL from server_url (remove /api/monitoring/data)
            base_url = self.config.server_url.replace('/api/monitoring/data', '')
            url = f"{base_url}/api/config/client/{self.client_id}"
            
            logger.info(f"🌐 Fetching config from: {url}")
            print(f"🌐 CONFIG: Fetching from {url}")
            
            response = requests.get(url, timeout=10)
            
            logger.info(f"📊 CONFIG: Response status: {response.status_code}")
            print(f"📊 CONFIG: Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Failed to fetch config: HTTP {response.status_code}")
                print(f"⚠️ CONFIG: Failed - HTTP {response.status_code}")
                logger.debug(f"Response body: {response.text[:200]}")
                return False
            
            config_data = response.json()
            
            logger.info(f"📦 CONFIG: Received data: {config_data}")
            print(f"📦 CONFIG: Received configuration data")
            print(f"   - Screenshot interval: {config_data.get('screenshot_interval_minutes')} min")
            print(f"   - Data send interval: {config_data.get('data_send_interval_minutes')} min")
            print(f"   - Screenshot quality: {config_data.get('screenshot_quality')}%")
            
            # Update .env file (this will trigger the file watcher)
            logger.info(f"💾 CONFIG: Writing to {self.env_path}")
            print(f"💾 CONFIG: Writing to {self.env_path}")
            
            self._write_env_file(self.env_path, config_data)
            
            logger.info("✅ Configuration file updated successfully")
            print("✅ CONFIG: File updated successfully - waiting for hot-reload...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error fetching and applying config: {e}", exc_info=True)
            print(f"❌ CONFIG: Error - {e}")
            return False
    
    def write_server_config_to_env(self) -> bool:
        """
        Write the server configuration to .env file.
        Gets the config from server_env_watcher.
        
        Returns:
            True if successful, False otherwise
        """
        print(f"📝 CONFIG WATCHER: write_server_config_to_env() called")
        logger.info("write_server_config_to_env() called")
        
        if not self.server_env_watcher:
            logger.error("No server_env_watcher configured")
            print(f"❌ CONFIG WATCHER: No server_env_watcher configured!")
            return False
        
        server_config = self.server_env_watcher.get_server_config()
        if not server_config:
            logger.error("No server config available")
            print(f"❌ CONFIG WATCHER: No server config available!")
            return False
        
        print(f"📦 CONFIG WATCHER: Got server config with {len(server_config)} keys")
        print(f"   Server config keys: {list(server_config.keys())}")
        
        try:
            # Extract file download path to avoid backslash in f-string
            file_download_path = server_config.get('FILE_DOWNLOAD_PATH', 'C:\\Downloads\\CompanyFiles')
            
            # Build .env content from server config
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            env_content = f"""# Auto-generated configuration from server
# Last updated: {timestamp}

SERVER_URL={server_config.get('SERVER_URL', '')}
AUTH_TOKEN={server_config.get('AUTH_TOKEN', '')}

# Intervals
SCREENSHOT_INTERVAL_MINUTES={server_config.get('SCREENSHOT_INTERVAL_MINUTES', 10)}
DATA_SEND_INTERVAL_MINUTES={server_config.get('DATA_SEND_INTERVAL_MINUTES', 10)}
LOCATION_UPDATE_INTERVAL_MINUTES={server_config.get('LOCATION_UPDATE_INTERVAL_MINUTES', 30)}

# Activity Tracking
IDLE_THRESHOLD_SECONDS={server_config.get('IDLE_THRESHOLD_SECONDS', 300)}
APP_USAGE_POLL_INTERVAL_SECONDS={server_config.get('APP_USAGE_POLL_INTERVAL_SECONDS', 10)}

# Screenshot Settings
SCREENSHOT_QUALITY={server_config.get('SCREENSHOT_QUALITY', 75)}

# Logging
LOG_LEVEL={server_config.get('LOG_LEVEL', 'INFO')}

# OTA File Transfer Configuration
FILE_DOWNLOAD_PATH={file_download_path}
"""
            
            print(f"💾 CONFIG WATCHER: Writing to {self.env_path}")
            print(f"   DATA_SEND_INTERVAL_MINUTES: {server_config.get('DATA_SEND_INTERVAL_MINUTES')}")
            print(f"   SCREENSHOT_INTERVAL_MINUTES: {server_config.get('SCREENSHOT_INTERVAL_MINUTES')}")
            
            # Write to file
            with open(self.env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            logger.info(f"✅ Successfully wrote server config to {self.env_path}")
            print(f"✅ CONFIG WATCHER: Server config written to .env")
            
            # IMPORTANT: Manually trigger hot-reload since file watcher might not work reliably on Windows
            print(f"🔄 CONFIG WATCHER: Manually triggering hot-reload (file watcher backup)...")
            if self.reload_callback:
                try:
                    self.reload_callback()
                    print(f"✅ CONFIG WATCHER: Hot-reload completed!")
                except Exception as e:
                    logger.error(f"Error during hot-reload: {e}")
                    print(f"❌ CONFIG WATCHER: Hot-reload error - {e}")
            else:
                print(f"⚠️ CONFIG WATCHER: No reload callback registered!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to write server config to .env: {e}")
            print(f"❌ CONFIG WATCHER: Failed to write .env - {e}")
            return False
    
    def _write_env_file(self, env_path: Path, config_data: Dict[str, Any]) -> None:
        """
        Write configuration data to .env file.
        
        Args:
            env_path: Path to .env file
            config_data: Configuration dictionary from server
        """
        # Extract values to avoid backslash issues in f-strings
        server_url = config_data.get('server_url', 'http://localhost:5000/api/monitoring/data')
        auth_token = config_data.get('auth_token', 'vibgyorseek-client-token-2024')
        file_download_path = config_data.get('file_download_path', 'C:\\Downloads\\CompanyFiles')
        
        # Build complete env content
        env_content = f"""# Auto-generated configuration from server
# Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}

SERVER_URL={server_url}
AUTH_TOKEN={auth_token}

# Intervals
SCREENSHOT_INTERVAL_MINUTES={config_data.get('screenshot_interval_minutes', 10)}
DATA_SEND_INTERVAL_MINUTES={config_data.get('data_send_interval_minutes', 10)}
LOCATION_UPDATE_INTERVAL_MINUTES={config_data.get('location_update_interval_minutes', 30)}

# Activity Tracking
IDLE_THRESHOLD_SECONDS={config_data.get('idle_threshold_seconds', 300)}
APP_USAGE_POLL_INTERVAL_SECONDS={config_data.get('app_usage_poll_interval_seconds', 10)}

# Screenshot Settings
SCREENSHOT_QUALITY={config_data.get('screenshot_quality', 75)}

# Logging
LOG_LEVEL={config_data.get('log_level', 'INFO')}

# OTA File Transfer Configuration
FILE_DOWNLOAD_PATH={file_download_path}
"""
        
        # Write the file
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            logger.info(f"✅ Successfully wrote configuration to {env_path}")
        except Exception as e:
            logger.error(f"❌ Failed to write .env file: {e}")
            raise
    
    def _on_env_file_changed(self):
        """Called when .env file is modified by the file watcher."""
        print(f"\n{'='*60}")
        print(f"📝 CONFIG WATCHER: .env file changed detected by file watcher!")
        print(f"{'='*60}")
        logger.info("_on_env_file_changed() called by file watcher")
        
        # Don't write again - the file was just written by write_server_config_to_env
        # Just trigger the reload callback
        
        if self.reload_callback:
            logger.info("🔄 Triggering hot-reload of configuration...")
            print(f"🔄 CONFIG WATCHER: Triggering hot-reload callback...")
            try:
                self.reload_callback()
                logger.info("✅ Configuration hot-reloaded successfully!")
                print(f"✅ CONFIG WATCHER: Hot-reload completed!")
            except Exception as e:
                logger.error(f"❌ Error during hot-reload: {e}")
                print(f"❌ CONFIG WATCHER: Hot-reload error - {e}")
        else:
            logger.warning("⚠️ No reload callback registered, skipping hot-reload")
            print(f"⚠️ CONFIG WATCHER: No reload callback registered!")
    
    def check_for_updates(self) -> None:
        """
        Check for configuration updates and apply if needed.
        The file watcher will automatically trigger reload when .env changes.
        """
        server_version = self.get_config_version()
        
        if server_version is None:
            logger.debug("Could not get server version")
            return
        
        logger.debug(f"� CONFIG: Current version: {self.current_version}, Server version: {server_version}")
        
        if server_version > self.current_version:
            logger.info(f"🔔 Configuration update detected (v{self.current_version} -> v{server_version})")
            print(f"\n{'='*60}")
            print(f"🔔 CONFIG UPDATE DETECTED!")
            print(f"   Current version: {self.current_version}")
            print(f"   Server version:  {server_version}")
            print(f"{'='*60}\n")
            
            if self.fetch_and_apply_config():
                self.current_version = server_version
                logger.info(f"✅ Config version updated to {server_version}")
                print(f"✅ CONFIG: Version updated to {server_version}")
                # No need to call reload here - file watcher will handle it
                logger.info("⏳ Waiting for file watcher to trigger hot-reload...")
                print("⏳ CONFIG: Waiting for file watcher to trigger hot-reload...")
            else:
                logger.error("❌ Failed to fetch and apply config")
                print("❌ CONFIG: Failed to fetch and apply")
        else:
            logger.debug(f"✓ Config is up to date (version {self.current_version})")
    
    def start(self) -> None:
        """
        Start the configuration watcher and file observer.
        """
        self.running = True
        
        # Get initial version
        initial_version = self.get_config_version()
        if initial_version is not None:
            self.current_version = initial_version
            logger.info(f"🚀 Config watcher started (current version: {self.current_version})")
            print(f"🚀 CONFIG WATCHER: Started (current version: {self.current_version})")
        else:
            logger.warning("⚠️ Could not get initial config version")
            print("⚠️ CONFIG WATCHER: Could not get initial version")
        
        # Start file watcher for .env file
        try:
            event_handler = EnvFileHandler(self._on_env_file_changed)
            self.observer = Observer()
            watch_dir = str(self.env_path.parent)
            self.observer.schedule(event_handler, watch_dir, recursive=False)
            self.observer.start()
            logger.info(f"👁️ File watcher started monitoring: {self.env_path}")
            print(f"👁️ CONFIG WATCHER: File watcher monitoring {self.env_path}")
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}", exc_info=True)
            logger.warning("Continuing without file watcher - hot-reload disabled")
            print(f"⚠️ CONFIG WATCHER: File watcher failed - {e}")
    
    def check_once(self) -> None:
        """
        Perform a single configuration check.
        Called periodically by the monitoring loop.
        """
        if self.running:
            print(f"🔍 CONFIG WATCHER: Checking for updates (current version: {self.current_version})...")
            logger.debug(f"🔍 CONFIG WATCHER: Performing check (version: {self.current_version})")
            self.check_for_updates()
        else:
            logger.debug("Config watcher not running, skipping check")
    
    def stop(self) -> None:
        """Stop the configuration watcher and file observer."""
        self.running = False
        
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=5)
                logger.info("👁️ File watcher stopped")
            except Exception as e:
                logger.error(f"Error stopping file watcher: {e}")
        
        logger.info("🛑 Config watcher stopped")

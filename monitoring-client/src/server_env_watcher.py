"""Server environment watcher - checks for config changes from server every 10 seconds."""

import requests
from typing import Optional, Dict, Any
from .logger import get_logger
from .config import Config

logger = get_logger()


class ServerEnvWatcher:
    """Watches the server for environment configuration changes."""
    
    def __init__(self, config: Config):
        """
        Initialize the server env watcher.
        
        Args:
            config: Current configuration instance
        """
        self.config = config
        self.last_server_config: Optional[Dict[str, Any]] = None
        self.check_counter = 0
        self.on_change_callback = None
        
        print("🚀 SERVER ENV WATCHER: Initialized")
        logger.info("ServerEnvWatcher initialized")
        
    def set_on_change_callback(self, callback):
        """
        Set the callback to be called when changes are detected.
        
        Args:
            callback: Function to call when changes detected
        """
        self.on_change_callback = callback
        logger.info("🔄 Server env change callback registered")
        
    def fetch_server_config(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the current configuration from the server.
        
        Returns:
            Configuration dictionary, or None if fetch failed
        """
        try:
            # Extract base URL from server_url (remove /api/monitoring/data)
            base_url = self.config.server_url.replace('/api/monitoring/data', '')
            url = f"{base_url}/api/client-env"
            
            logger.debug(f"Fetching server config from: {url}")
            print(f"🌐 SERVER ENV: Fetching from {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                config_data = response.json()
                logger.debug(f"Server config fetched successfully")
                print(f"✅ SERVER ENV: Config fetched successfully")
                return config_data
            else:
                logger.warning(f"Failed to fetch server config: HTTP {response.status_code}")
                print(f"❌ SERVER ENV: Failed - HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching server config: {e}")
            print(f"❌ SERVER ENV: Error - {e}")
            return None
    
    def check_for_changes(self) -> bool:
        """
        Check if the server configuration has changed.
        
        Returns:
            True if changes detected, False otherwise
        """
        self.check_counter += 1
        print(f"🔍 SERVER ENV: Checking for changes (check #{self.check_counter})...")
        logger.debug(f"SERVER ENV: Check #{self.check_counter}")
        
        # Fetch current server config
        server_config = self.fetch_server_config()
        
        if server_config is None:
            print(f"❌ SERVER ENV: Failed to fetch config")
            return False
        
        print(f"📦 SERVER ENV: Fetched config with {len(server_config)} keys")
        
        # First time - store it and trigger update to sync with server
        if self.last_server_config is None:
            self.last_server_config = server_config
            logger.info("🔍 SERVER ENV: Initial config fetched - triggering sync")
            print(f"🔍 SERVER ENV: Initial config fetched - triggering sync with server")
            
            # Trigger callback to write server config to local .env
            if self.on_change_callback:
                try:
                    print(f"🔄 SERVER ENV: Calling callback to sync local .env with server")
                    self.on_change_callback()
                    return True  # Return True to indicate sync happened
                except Exception as e:
                    logger.error(f"Error in on_change_callback: {e}")
                    print(f"❌ SERVER ENV: Callback error - {e}")
            else:
                print(f"⚠️ SERVER ENV: No callback registered!")
            
            return False
        
        # Compare with last known config
        changes_detected = False
        changes = []
        
        print(f"🔍 SERVER ENV: Comparing with last known config...")
        for key, value in server_config.items():
            if key not in self.last_server_config:
                changes.append(f"{key} added")
                changes_detected = True
                print(f"   ➕ {key} added: {value}")
            elif self.last_server_config[key] != value:
                old_value = self.last_server_config[key]
                changes.append(f"{key}: {old_value} → {value}")
                changes_detected = True
                print(f"   🔄 {key}: {old_value} → {value}")
        
        if changes_detected:
            logger.info("🔔 SERVER ENV: Configuration changes detected!")
            print(f"\n{'='*60}")
            print("🔔 SERVER ENV: CONFIGURATION CHANGES DETECTED!")
            print(f"{'='*60}")
            for change in changes:
                print(f"   • {change}")
                logger.info(f"   • {change}")
            print(f"{'='*60}\n")
            
            # Update last known config
            self.last_server_config = server_config
            
            # Call the callback if registered
            if self.on_change_callback:
                try:
                    print(f"🔄 SERVER ENV: Calling callback to update local .env")
                    self.on_change_callback()
                except Exception as e:
                    logger.error(f"Error in on_change_callback: {e}")
                    print(f"❌ SERVER ENV: Callback error - {e}")
            else:
                print(f"⚠️ SERVER ENV: No callback registered!")
            
            return True
        else:
            print(f"✓ SERVER ENV: No changes detected")
        
        # Log occasionally to show it's working
        if self.check_counter % 6 == 0:  # Every 60 seconds (6 checks * 10s)
            logger.debug(f"✓ SERVER ENV: No changes (check #{self.check_counter})")
        
        return False
    
    def get_server_config(self) -> Optional[Dict[str, Any]]:
        """
        Get the last fetched server configuration.
        
        Returns:
            Configuration dictionary, or None if not fetched yet
        """
        return self.last_server_config

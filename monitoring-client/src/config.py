"""Configuration module for loading environment variables and providing defaults."""

import os
import json
import uuid
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for the monitoring client."""
    
    # Default values
    DEFAULT_SCREENSHOT_INTERVAL_MINUTES = 10
    DEFAULT_DATA_SEND_INTERVAL_MINUTES = 10
    DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES = 30
    DEFAULT_IDLE_THRESHOLD_SECONDS = 300
    DEFAULT_SCREENSHOT_QUALITY = 75
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_APP_USAGE_POLL_INTERVAL_SECONDS = 10
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration by loading from .env file.
        
        Args:
            env_file: Path to .env file. If None, looks for .env in current directory.
        """
        # Load environment variables from .env file
        # Use override=True to force reload of environment variables (needed for hot-reload)
        if env_file:
            load_dotenv(env_file, override=True)
        else:
            load_dotenv(override=True)
    
    @property
    def server_url(self) -> str:
        """Get the server URL (required)."""
        url = os.getenv("SERVER_URL")
        if not url:
            raise ValueError("SERVER_URL is required in configuration")
        return url
    
    @property
    def auth_token(self) -> str:
        """Get the authentication token (required)."""
        token = os.getenv("AUTH_TOKEN")
        if not token:
            raise ValueError("AUTH_TOKEN is required in configuration")
        return token
    
    @property
    def screenshot_interval_minutes(self) -> int:
        """Get the screenshot capture interval in minutes."""
        value = os.getenv("SCREENSHOT_INTERVAL_MINUTES")
        if value:
            try:
                interval = int(value)
                if interval > 0:
                    return interval
            except ValueError:
                pass
        return self.DEFAULT_SCREENSHOT_INTERVAL_MINUTES
    
    @property
    def data_send_interval_minutes(self) -> int:
        """Get the data transmission interval in minutes."""
        value = os.getenv("DATA_SEND_INTERVAL_MINUTES")
        if value:
            try:
                interval = int(value)
                if interval > 0:
                    return interval
            except ValueError:
                pass
        return self.DEFAULT_DATA_SEND_INTERVAL_MINUTES
    
    @property
    def location_update_interval_minutes(self) -> int:
        """Get the location update interval in minutes."""
        value = os.getenv("LOCATION_UPDATE_INTERVAL_MINUTES")
        if value:
            try:
                interval = int(value)
                if interval > 0:
                    return interval
            except ValueError:
                pass
        return self.DEFAULT_LOCATION_UPDATE_INTERVAL_MINUTES
    
    @property
    def idle_threshold_seconds(self) -> int:
        """Get the idle timeout threshold in seconds."""
        value = os.getenv("IDLE_THRESHOLD_SECONDS")
        if value:
            try:
                threshold = int(value)
                if threshold > 0:
                    return threshold
            except ValueError:
                pass
        return self.DEFAULT_IDLE_THRESHOLD_SECONDS
    
    @property
    def log_level(self) -> str:
        """Get the logging level."""
        level = os.getenv("LOG_LEVEL")
        if level and level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            return level.upper()
        return self.DEFAULT_LOG_LEVEL
    
    @property
    def screenshot_quality(self) -> int:
        """Get the JPEG screenshot quality (1-100)."""
        value = os.getenv("SCREENSHOT_QUALITY")
        if value:
            try:
                quality = int(value)
                if 1 <= quality <= 100:
                    return quality
            except ValueError:
                pass
        return self.DEFAULT_SCREENSHOT_QUALITY
    
    @property
    def app_usage_poll_interval_seconds(self) -> float:
        """Get the application usage polling interval in seconds."""
        value = os.getenv("APP_USAGE_POLL_INTERVAL_SECONDS")
        if value:
            try:
                interval = float(value)
                if interval >= 2.0:  # Minimum 2 seconds
                    return interval
            except ValueError:
                pass
        return float(self.DEFAULT_APP_USAGE_POLL_INTERVAL_SECONDS)
    
    @property
    def file_download_path(self) -> str:
        """Get the file download path for OTA file transfers."""
        return os.getenv("FILE_DOWNLOAD_PATH", "C:\\Downloads\\CompanyFiles")
    
    @property
    def file_sync_interval_seconds(self) -> int:
        """Get the file sync polling interval in seconds."""
        value = os.getenv("FILE_SYNC_INTERVAL")
        if value:
            try:
                interval = int(value)
                if interval > 0:
                    return interval
            except ValueError:
                pass
        return 30  # Default 30 seconds


def get_employee_config_path() -> Path:
    """
    Get the path to the employee configuration file.
    
    Returns:
        Path to the employee config JSON file in user's app data directory.
    """
    # Use APPDATA on Windows, or ~/.config on Unix-like systems
    if os.name == 'nt':  # Windows
        app_data = os.getenv('APPDATA')
        if not app_data:
            raise RuntimeError("APPDATA environment variable not found")
        base_path = Path(app_data)
    else:  # Unix-like systems
        base_path = Path.home() / '.config'
    
    # Create VibgyorSeek directory if it doesn't exist
    config_dir = base_path / 'VibgyorSeek'
    config_dir.mkdir(parents=True, exist_ok=True)
    
    return config_dir / 'employee_config.json'


def store_employee_name(name: str) -> None:
    """
    Store the employee name persistently in a local JSON file.
    
    Args:
        name: The employee name to store.
    
    Raises:
        ValueError: If name is empty or invalid.
        IOError: If unable to write to the configuration file.
    """
    if not name or not name.strip():
        raise ValueError("Employee name cannot be empty")
    
    config_path = get_employee_config_path()
    
    try:
        config_data = {'employee_name': name.strip()}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        raise IOError(f"Failed to store employee name: {e}")


def retrieve_employee_name() -> Optional[str]:
    """
    Retrieve the stored employee name from the local JSON file.
    
    Returns:
        The stored employee name, or None if not found.
    
    Raises:
        IOError: If unable to read the configuration file.
    """
    config_path = get_employee_config_path()
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            return config_data.get('employee_name')
    except json.JSONDecodeError as e:
        raise IOError(f"Failed to parse employee configuration: {e}")
    except Exception as e:
        raise IOError(f"Failed to retrieve employee name: {e}")



def generate_client_id() -> str:
    """
    Generate a unique client ID using UUID4.
    
    Returns:
        A unique client ID string.
    """
    return str(uuid.uuid4())


def store_client_id(client_id: str) -> None:
    """
    Store the client ID persistently in the employee config file.
    
    Args:
        client_id: The client ID to store.
    
    Raises:
        IOError: If unable to write to the configuration file.
    """
    config_path = get_employee_config_path()
    
    try:
        # Read existing config or create new
        config_data = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        
        # Add client_id
        config_data['client_id'] = client_id
        
        # Write back
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        raise IOError(f"Failed to store client ID: {e}")


def retrieve_client_id() -> Optional[str]:
    """
    Retrieve the stored client ID from the local JSON file.
    If no client ID exists, generate and store a new one.
    
    Returns:
        The stored or newly generated client ID.
    
    Raises:
        IOError: If unable to read/write the configuration file.
    """
    config_path = get_employee_config_path()
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                client_id = config_data.get('client_id')
                
                if client_id:
                    return client_id
        
        # No client ID found, generate new one
        new_client_id = generate_client_id()
        store_client_id(new_client_id)
        return new_client_id
        
    except json.JSONDecodeError as e:
        raise IOError(f"Failed to parse employee configuration: {e}")
    except Exception as e:
        raise IOError(f"Failed to retrieve/generate client ID: {e}")

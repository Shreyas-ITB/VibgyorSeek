"""Unit tests for configuration module."""

import os
import pytest
from pathlib import Path
from src.config import Config


class TestConfig:
    """Test cases for Config class."""
    
    def test_default_values(self, tmp_path, monkeypatch):
        """Test that default values are used when env vars are not set."""
        # Clear any existing environment variables
        for key in ["SERVER_URL", "AUTH_TOKEN", "SCREENSHOT_INTERVAL_MINUTES", 
                    "DATA_SEND_INTERVAL_MINUTES", "IDLE_THRESHOLD_SECONDS", "LOG_LEVEL"]:
            monkeypatch.delenv(key, raising=False)
        
        # Create a temporary .env file with only required fields
        env_file = tmp_path / ".env"
        env_file.write_text("SERVER_URL=https://test.com\nAUTH_TOKEN=test-token")
        
        config = Config(str(env_file))
        
        assert config.screenshot_interval_minutes == 10
        assert config.data_send_interval_minutes == 10
        assert config.idle_threshold_seconds == 300
        assert config.log_level == "INFO"
    
    def test_custom_values(self, tmp_path, monkeypatch):
        """Test that custom values from .env are loaded correctly."""
        # Clear any existing environment variables
        for key in ["SERVER_URL", "AUTH_TOKEN", "SCREENSHOT_INTERVAL_MINUTES", 
                    "DATA_SEND_INTERVAL_MINUTES", "IDLE_THRESHOLD_SECONDS", "LOG_LEVEL"]:
            monkeypatch.delenv(key, raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text(
            "SERVER_URL=https://custom.com\n"
            "AUTH_TOKEN=custom-token\n"
            "SCREENSHOT_INTERVAL_MINUTES=15\n"
            "DATA_SEND_INTERVAL_MINUTES=20\n"
            "IDLE_THRESHOLD_SECONDS=600\n"
            "LOG_LEVEL=DEBUG"
        )
        
        config = Config(str(env_file))
        
        assert config.server_url == "https://custom.com"
        assert config.auth_token == "custom-token"
        assert config.screenshot_interval_minutes == 15
        assert config.data_send_interval_minutes == 20
        assert config.idle_threshold_seconds == 600
        assert config.log_level == "DEBUG"
    
    def test_invalid_values_use_defaults(self, tmp_path, monkeypatch):
        """Test that invalid values fall back to defaults."""
        # Clear any existing environment variables
        for key in ["SERVER_URL", "AUTH_TOKEN", "SCREENSHOT_INTERVAL_MINUTES", 
                    "DATA_SEND_INTERVAL_MINUTES", "IDLE_THRESHOLD_SECONDS", "LOG_LEVEL"]:
            monkeypatch.delenv(key, raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text(
            "SERVER_URL=https://test.com\n"
            "AUTH_TOKEN=test-token\n"
            "SCREENSHOT_INTERVAL_MINUTES=invalid\n"
            "DATA_SEND_INTERVAL_MINUTES=-5\n"
            "IDLE_THRESHOLD_SECONDS=0\n"
            "LOG_LEVEL=INVALID"
        )
        
        config = Config(str(env_file))
        
        assert config.screenshot_interval_minutes == 10
        assert config.data_send_interval_minutes == 10
        assert config.idle_threshold_seconds == 300
        assert config.log_level == "INFO"
    
    def test_missing_required_server_url(self, tmp_path, monkeypatch):
        """Test that missing SERVER_URL raises ValueError."""
        # Clear any existing environment variables
        for key in ["SERVER_URL", "AUTH_TOKEN", "SCREENSHOT_INTERVAL_MINUTES", 
                    "DATA_SEND_INTERVAL_MINUTES", "IDLE_THRESHOLD_SECONDS", "LOG_LEVEL"]:
            monkeypatch.delenv(key, raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text("AUTH_TOKEN=test-token")
        
        config = Config(str(env_file))
        
        with pytest.raises(ValueError, match="SERVER_URL is required"):
            _ = config.server_url
    
    def test_missing_required_auth_token(self, tmp_path, monkeypatch):
        """Test that missing AUTH_TOKEN raises ValueError."""
        # Clear any existing environment variables
        for key in ["SERVER_URL", "AUTH_TOKEN", "SCREENSHOT_INTERVAL_MINUTES", 
                    "DATA_SEND_INTERVAL_MINUTES", "IDLE_THRESHOLD_SECONDS", "LOG_LEVEL"]:
            monkeypatch.delenv(key, raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text("SERVER_URL=https://test.com")
        
        config = Config(str(env_file))
        
        with pytest.raises(ValueError, match="AUTH_TOKEN is required"):
            _ = config.auth_token
    
    def test_screenshot_quality_default(self, tmp_path, monkeypatch):
        """Test that screenshot quality uses default when not set."""
        for key in ["SERVER_URL", "AUTH_TOKEN", "SCREENSHOT_QUALITY"]:
            monkeypatch.delenv(key, raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text("SERVER_URL=https://test.com\nAUTH_TOKEN=test-token")
        
        config = Config(str(env_file))
        assert config.screenshot_quality == 75
    
    def test_screenshot_quality_custom(self, tmp_path, monkeypatch):
        """Test that custom screenshot quality is loaded correctly."""
        for key in ["SERVER_URL", "AUTH_TOKEN", "SCREENSHOT_QUALITY"]:
            monkeypatch.delenv(key, raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text("SERVER_URL=https://test.com\nAUTH_TOKEN=test-token\nSCREENSHOT_QUALITY=90")
        
        config = Config(str(env_file))
        assert config.screenshot_quality == 90
    
    def test_screenshot_quality_invalid_uses_default(self, tmp_path, monkeypatch):
        """Test that invalid screenshot quality falls back to default."""
        for key in ["SERVER_URL", "AUTH_TOKEN", "SCREENSHOT_QUALITY"]:
            monkeypatch.delenv(key, raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text("SERVER_URL=https://test.com\nAUTH_TOKEN=test-token\nSCREENSHOT_QUALITY=invalid")
        
        config = Config(str(env_file))
        assert config.screenshot_quality == 75
    
    def test_screenshot_quality_out_of_range_uses_default(self, tmp_path, monkeypatch):
        """Test that out-of-range screenshot quality falls back to default."""
        for key in ["SERVER_URL", "AUTH_TOKEN", "SCREENSHOT_QUALITY"]:
            monkeypatch.delenv(key, raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text("SERVER_URL=https://test.com\nAUTH_TOKEN=test-token\nSCREENSHOT_QUALITY=150")
        
        config = Config(str(env_file))
        assert config.screenshot_quality == 75
        
        env_file.write_text("SERVER_URL=https://test.com\nAUTH_TOKEN=test-token\nSCREENSHOT_QUALITY=0")
        config = Config(str(env_file))
        assert config.screenshot_quality == 75



class TestEmployeeNameStorage:
    """Test cases for employee name storage functions."""
    
    def test_store_and_retrieve_employee_name(self, tmp_path, monkeypatch):
        """Test storing and retrieving employee name."""
        # Mock the config path to use tmp_path
        def mock_get_path():
            return tmp_path / 'employee_config.json'
        
        monkeypatch.setattr('src.config.get_employee_config_path', mock_get_path)
        
        from src.config import store_employee_name, retrieve_employee_name
        
        # Store employee name
        store_employee_name("John Doe")
        
        # Retrieve and verify
        name = retrieve_employee_name()
        assert name == "John Doe"
    
    def test_store_employee_name_strips_whitespace(self, tmp_path, monkeypatch):
        """Test that employee name is stripped of leading/trailing whitespace."""
        def mock_get_path():
            return tmp_path / 'employee_config.json'
        
        monkeypatch.setattr('src.config.get_employee_config_path', mock_get_path)
        
        from src.config import store_employee_name, retrieve_employee_name
        
        # Store with whitespace
        store_employee_name("  Jane Smith  ")
        
        # Retrieve and verify whitespace is stripped
        name = retrieve_employee_name()
        assert name == "Jane Smith"
    
    def test_store_empty_name_raises_error(self, tmp_path, monkeypatch):
        """Test that storing empty name raises ValueError."""
        def mock_get_path():
            return tmp_path / 'employee_config.json'
        
        monkeypatch.setattr('src.config.get_employee_config_path', mock_get_path)
        
        from src.config import store_employee_name
        
        with pytest.raises(ValueError, match="Employee name cannot be empty"):
            store_employee_name("")
        
        with pytest.raises(ValueError, match="Employee name cannot be empty"):
            store_employee_name("   ")
    
    def test_retrieve_nonexistent_returns_none(self, tmp_path, monkeypatch):
        """Test that retrieving from non-existent file returns None."""
        def mock_get_path():
            return tmp_path / 'nonexistent.json'
        
        monkeypatch.setattr('src.config.get_employee_config_path', mock_get_path)
        
        from src.config import retrieve_employee_name
        
        name = retrieve_employee_name()
        assert name is None
    
    def test_retrieve_invalid_json_raises_error(self, tmp_path, monkeypatch):
        """Test that retrieving invalid JSON raises IOError."""
        def mock_get_path():
            config_file = tmp_path / 'employee_config.json'
            config_file.write_text("invalid json {")
            return config_file
        
        monkeypatch.setattr('src.config.get_employee_config_path', mock_get_path)
        
        from src.config import retrieve_employee_name
        
        with pytest.raises(IOError, match="Failed to parse employee configuration"):
            retrieve_employee_name()
    
    def test_overwrite_existing_name(self, tmp_path, monkeypatch):
        """Test that storing a new name overwrites the existing one."""
        def mock_get_path():
            return tmp_path / 'employee_config.json'
        
        monkeypatch.setattr('src.config.get_employee_config_path', mock_get_path)
        
        from src.config import store_employee_name, retrieve_employee_name
        
        # Store first name
        store_employee_name("Alice")
        assert retrieve_employee_name() == "Alice"
        
        # Store second name
        store_employee_name("Bob")
        assert retrieve_employee_name() == "Bob"

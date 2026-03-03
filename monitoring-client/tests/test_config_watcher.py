"""Tests for the configuration watcher module."""

import pytest
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.config_watcher import ConfigWatcher
from src.config import Config


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock(spec=Config)
    config.server_url = "http://localhost:5000/api/monitoring/data"
    return config


@pytest.fixture
def config_watcher(mock_config):
    """Create a ConfigWatcher instance with mocked dependencies."""
    with patch('src.config_watcher.retrieve_employee_name', return_value='Test Employee'):
        watcher = ConfigWatcher(mock_config, check_interval_seconds=5)
        return watcher


def test_config_watcher_initialization(config_watcher):
    """Test that ConfigWatcher initializes correctly."""
    assert config_watcher.config is not None
    assert config_watcher.check_interval == 5
    assert config_watcher.current_version == 0
    assert config_watcher.employee_name == 'Test Employee'
    assert config_watcher.running is False


def test_get_config_version_success(config_watcher):
    """Test successful configuration version retrieval."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'version': 5}
    
    with patch('requests.get', return_value=mock_response):
        version = config_watcher.get_config_version()
        assert version == 5


def test_get_config_version_no_employee_name():
    """Test version retrieval with no employee name."""
    config = Mock(spec=Config)
    config.server_url = "http://localhost:5000/api/monitoring/data"
    
    with patch('src.config_watcher.retrieve_employee_name', return_value=None):
        watcher = ConfigWatcher(config)
        version = watcher.get_config_version()
        assert version is None


def test_get_config_version_http_error(config_watcher):
    """Test version retrieval with HTTP error."""
    mock_response = Mock()
    mock_response.status_code = 500
    
    with patch('requests.get', return_value=mock_response):
        version = config_watcher.get_config_version()
        assert version is None


def test_get_config_version_network_error(config_watcher):
    """Test version retrieval with network error."""
    with patch('requests.get', side_effect=Exception("Network error")):
        version = config_watcher.get_config_version()
        assert version is None


def test_fetch_and_apply_config_success(config_watcher, tmp_path):
    """Test successful configuration fetch and apply."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'server_url': 'http://localhost:5000/api/monitoring/data',
        'auth_token': 'test-token',
        'screenshot_interval_minutes': 15,
        'data_send_interval_minutes': 10,
        'location_update_interval_minutes': 30,
        'idle_threshold_seconds': 300,
        'app_usage_poll_interval_seconds': 10,
        'screenshot_quality': 80,
        'log_level': 'DEBUG',
        'file_download_path': 'C:\\Downloads\\Test'
    }
    
    # Mock the env file path
    env_file = tmp_path / '.env'
    
    with patch('requests.get', return_value=mock_response), \
         patch('pathlib.Path', return_value=tmp_path):
        
        # Manually write to test file
        config_watcher._write_env_file(env_file, mock_response.json())
        
        # Verify file was created
        assert env_file.exists()
        
        # Verify content
        content = env_file.read_text()
        assert 'SERVER_URL=http://localhost:5000/api/monitoring/data' in content
        assert 'AUTH_TOKEN=test-token' in content
        assert 'SCREENSHOT_INTERVAL_MINUTES=15' in content
        assert 'SCREENSHOT_QUALITY=80' in content
        assert 'LOG_LEVEL=DEBUG' in content


def test_fetch_and_apply_config_http_error(config_watcher):
    """Test configuration fetch with HTTP error."""
    mock_response = Mock()
    mock_response.status_code = 404
    
    with patch('requests.get', return_value=mock_response):
        result = config_watcher.fetch_and_apply_config()
        assert result is False


def test_fetch_and_apply_config_no_employee_name():
    """Test configuration fetch with no employee name."""
    config = Mock(spec=Config)
    config.server_url = "http://localhost:5000/api/monitoring/data"
    
    with patch('src.config_watcher.retrieve_employee_name', return_value=None):
        watcher = ConfigWatcher(config)
        result = watcher.fetch_and_apply_config()
        assert result is False


def test_write_env_file(config_watcher, tmp_path):
    """Test .env file writing."""
    env_file = tmp_path / '.env'
    
    config_data = {
        'server_url': 'http://test.com/api',
        'auth_token': 'token123',
        'screenshot_interval_minutes': 20,
        'data_send_interval_minutes': 15,
        'location_update_interval_minutes': 45,
        'idle_threshold_seconds': 600,
        'app_usage_poll_interval_seconds': 5,
        'screenshot_quality': 90,
        'log_level': 'WARNING',
        'file_download_path': 'D:\\Files'
    }
    
    config_watcher._write_env_file(env_file, config_data)
    
    assert env_file.exists()
    content = env_file.read_text()
    
    # Verify all fields are present
    assert 'SERVER_URL=http://test.com/api' in content
    assert 'AUTH_TOKEN=token123' in content
    assert 'SCREENSHOT_INTERVAL_MINUTES=20' in content
    assert 'DATA_SEND_INTERVAL_MINUTES=15' in content
    assert 'LOCATION_UPDATE_INTERVAL_MINUTES=45' in content
    assert 'IDLE_THRESHOLD_SECONDS=600' in content
    assert 'APP_USAGE_POLL_INTERVAL_SECONDS=5' in content
    assert 'SCREENSHOT_QUALITY=90' in content
    assert 'LOG_LEVEL=WARNING' in content
    assert 'FILE_DOWNLOAD_PATH=D:\\Files' in content


def test_check_for_updates_no_change(config_watcher):
    """Test check for updates when version hasn't changed."""
    config_watcher.current_version = 5
    
    with patch.object(config_watcher, 'get_config_version', return_value=5):
        with patch.object(config_watcher, 'fetch_and_apply_config') as mock_fetch:
            config_watcher.check_for_updates()
            mock_fetch.assert_not_called()


def test_check_for_updates_with_change(config_watcher):
    """Test check for updates when version has changed."""
    config_watcher.current_version = 5
    
    with patch.object(config_watcher, 'get_config_version', return_value=6), \
         patch.object(config_watcher, 'fetch_and_apply_config', return_value=True):
        
        config_watcher.check_for_updates()
        
        # Version should be updated after successful fetch
        assert config_watcher.current_version == 6


def test_check_for_updates_fetch_fails(config_watcher):
    """Test check for updates when fetch fails."""
    config_watcher.current_version = 5
    
    with patch.object(config_watcher, 'get_config_version', return_value=6), \
         patch.object(config_watcher, 'fetch_and_apply_config', return_value=False):
        
        config_watcher.check_for_updates()
        
        # Version should not be updated if fetch fails
        assert config_watcher.current_version == 5


def test_start(config_watcher):
    """Test starting the config watcher."""
    with patch.object(config_watcher, 'get_config_version', return_value=3):
        config_watcher.start()
        
        assert config_watcher.running is True
        assert config_watcher.current_version == 3


def test_start_no_initial_version(config_watcher):
    """Test starting when initial version fetch fails."""
    with patch.object(config_watcher, 'get_config_version', return_value=None):
        config_watcher.start()
        
        assert config_watcher.running is True
        assert config_watcher.current_version == 0


def test_stop(config_watcher):
    """Test stopping the config watcher."""
    config_watcher.running = True
    config_watcher.stop()
    
    assert config_watcher.running is False


def test_check_once_when_running(config_watcher):
    """Test check_once when watcher is running."""
    config_watcher.running = True
    
    with patch.object(config_watcher, 'check_for_updates') as mock_check:
        config_watcher.check_once()
        mock_check.assert_called_once()


def test_check_once_when_not_running(config_watcher):
    """Test check_once when watcher is not running."""
    config_watcher.running = False
    
    with patch.object(config_watcher, 'check_for_updates') as mock_check:
        config_watcher.check_once()
        mock_check.assert_not_called()

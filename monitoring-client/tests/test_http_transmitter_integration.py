"""
Integration tests for the HTTP transmission module.

Tests the HTTP transmitter with realistic payload structures and scenarios.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.http_transmitter import HTTPTransmitter
from src.config import Config


class TestHTTPTransmitterIntegration:
    """Integration tests for HTTP transmitter with realistic scenarios."""
    
    @patch('src.http_transmitter.requests.post')
    def test_send_complete_monitoring_payload(self, mock_post):
        """Test sending a complete monitoring payload structure."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test-token-123"
        )
        
        # Create a realistic payload
        payload = {
            "employee_name": "John Doe",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "interval_start": "2024-01-15T10:00:00Z",
            "interval_end": "2024-01-15T10:10:00Z",
            "activity": {
                "work_seconds": 480,
                "idle_seconds": 120
            },
            "applications": [
                {"name": "Visual Studio Code", "active": True},
                {"name": "Google Chrome", "active": False},
                {"name": "Slack", "active": False}
            ],
            "browser_tabs": [
                {
                    "browser": "Chrome",
                    "title": "GitHub - Project Repository",
                    "url": "https://github.com/example/repo"
                },
                {
                    "browser": "Chrome",
                    "title": "Stack Overflow",
                    "url": "https://stackoverflow.com/questions/12345"
                }
            ],
            "screenshot": "base64_encoded_image_data_here"
        }
        
        success, error = transmitter.send_payload(payload)
        
        assert success is True
        assert error is None
        
        # Verify the request was made with correct structure
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify URL
        assert call_args[0][0] == "https://example.com/api/monitoring/data"
        
        # Verify headers
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer test-token-123'
        assert headers['Content-Type'] == 'application/json'
        
        # Verify payload
        sent_payload = call_args[1]['json']
        assert sent_payload['employee_name'] == "John Doe"
        assert sent_payload['activity']['work_seconds'] == 480
        assert len(sent_payload['applications']) == 3
        assert len(sent_payload['browser_tabs']) == 2
    
    @patch('src.http_transmitter.requests.post')
    def test_send_payload_with_empty_screenshot(self, mock_post):
        """Test sending payload when screenshot capture fails."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test-token"
        )
        
        payload = {
            "employee_name": "Jane Smith",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "interval_start": "2024-01-15T10:00:00Z",
            "interval_end": "2024-01-15T10:10:00Z",
            "activity": {
                "work_seconds": 600,
                "idle_seconds": 0
            },
            "applications": [],
            "browser_tabs": [],
            "screenshot": ""  # Empty screenshot
        }
        
        success, error = transmitter.send_payload(payload)
        
        assert success is True
        assert error is None
    
    @patch('src.http_transmitter.requests.post')
    def test_send_payload_with_special_characters(self, mock_post):
        """Test sending payload with special characters in data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test-token"
        )
        
        payload = {
            "employee_name": "José García-López",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "interval_start": "2024-01-15T10:00:00Z",
            "interval_end": "2024-01-15T10:10:00Z",
            "activity": {
                "work_seconds": 300,
                "idle_seconds": 300
            },
            "applications": [
                {"name": "Microsoft® Word™", "active": True}
            ],
            "browser_tabs": [
                {
                    "browser": "Firefox",
                    "title": "Café & Restaurant – Menu",
                    "url": "https://example.com/café?item=crème-brûlée"
                }
            ],
            "screenshot": ""
        }
        
        success, error = transmitter.send_payload(payload)
        
        assert success is True
        assert error is None
    
    @patch('src.http_transmitter.requests.post')
    def test_retry_after_network_failure(self, mock_post):
        """Test retry behavior after network failure."""
        from requests.exceptions import ConnectionError
        
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.side_effect = [
            ConnectionError("Connection refused"),
            mock_response
        ]
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test-token"
        )
        
        payload = {
            "employee_name": "John Doe",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "interval_start": "2024-01-15T10:00:00Z",
            "interval_end": "2024-01-15T10:10:00Z",
            "activity": {"work_seconds": 600, "idle_seconds": 0},
            "applications": [],
            "browser_tabs": [],
            "screenshot": ""
        }
        
        # First attempt fails
        success1, error1 = transmitter.send_payload(payload)
        assert success1 is False
        assert "Network error" in error1
        
        # Second attempt succeeds
        success2, error2 = transmitter.send_payload(payload)
        assert success2 is True
        assert error2 is None
    
    @patch('src.http_transmitter.requests.post')
    def test_large_payload_transmission(self, mock_post):
        """Test transmission of large payload with many applications and tabs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/monitoring/data",
            auth_token="test-token"
        )
        
        # Create payload with many applications and browser tabs
        applications = [
            {"name": f"Application {i}", "active": i == 0}
            for i in range(50)
        ]
        
        browser_tabs = [
            {
                "browser": "Chrome",
                "title": f"Tab {i}",
                "url": f"https://example.com/page{i}"
            }
            for i in range(100)
        ]
        
        payload = {
            "employee_name": "John Doe",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "interval_start": "2024-01-15T10:00:00Z",
            "interval_end": "2024-01-15T10:10:00Z",
            "activity": {"work_seconds": 600, "idle_seconds": 0},
            "applications": applications,
            "browser_tabs": browser_tabs,
            "screenshot": "x" * 10000  # Simulate large screenshot data
        }
        
        success, error = transmitter.send_payload(payload)
        
        assert success is True
        assert error is None
    
    @patch.dict('os.environ', {
        'SERVER_URL': 'https://test-server.com/api/data',
        'AUTH_TOKEN': 'env-token-123'
    })
    @patch('src.http_transmitter.requests.post')
    def test_integration_with_config(self, mock_post):
        """Test integration with Config module."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Load configuration
        config = Config()
        
        # Create transmitter from config
        transmitter = HTTPTransmitter(
            server_url=config.server_url,
            auth_token=config.auth_token
        )
        
        payload = {
            "employee_name": "Test User",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "interval_start": "2024-01-15T10:00:00Z",
            "interval_end": "2024-01-15T10:10:00Z",
            "activity": {"work_seconds": 600, "idle_seconds": 0},
            "applications": [],
            "browser_tabs": [],
            "screenshot": ""
        }
        
        success, error = transmitter.send_payload(payload)
        
        assert success is True
        assert error is None
        
        # Verify correct URL and token were used
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://test-server.com/api/data'
        assert call_args[1]['headers']['Authorization'] == 'Bearer env-token-123'

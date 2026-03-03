"""
Unit tests for the HTTP transmission module.

Tests specific examples and edge cases for HTTP transmission functionality.
"""

import pytest
from unittest.mock import Mock, patch
from requests.exceptions import ConnectionError, Timeout, RequestException

from src.http_transmitter import (
    HTTPTransmitter,
    TransmissionError,
    AuthenticationError,
    ServerError,
    NetworkError
)


class TestHTTPTransmitterInitialization:
    """Test HTTPTransmitter initialization."""
    
    def test_valid_initialization(self):
        """Test initialization with valid parameters."""
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token-123"
        )
        assert transmitter.server_url == "https://example.com/api/data"
        assert transmitter.auth_token == "test-token-123"
    
    def test_initialization_strips_whitespace(self):
        """Test that initialization strips whitespace from parameters."""
        transmitter = HTTPTransmitter(
            server_url="  https://example.com/api/data  ",
            auth_token="  test-token-123  "
        )
        assert transmitter.server_url == "https://example.com/api/data"
        assert transmitter.auth_token == "test-token-123"
    
    def test_empty_server_url_raises_error(self):
        """Test that empty server URL raises ValueError."""
        with pytest.raises(ValueError, match="server_url cannot be empty"):
            HTTPTransmitter(server_url="", auth_token="test-token")
    
    def test_empty_auth_token_raises_error(self):
        """Test that empty auth token raises ValueError."""
        with pytest.raises(ValueError, match="auth_token cannot be empty"):
            HTTPTransmitter(
                server_url="https://example.com/api/data",
                auth_token=""
            )
    
    def test_whitespace_only_server_url_raises_error(self):
        """Test that whitespace-only server URL raises ValueError."""
        with pytest.raises(ValueError, match="server_url cannot be empty"):
            HTTPTransmitter(server_url="   ", auth_token="test-token")
    
    def test_whitespace_only_auth_token_raises_error(self):
        """Test that whitespace-only auth token raises ValueError."""
        with pytest.raises(ValueError, match="auth_token cannot be empty"):
            HTTPTransmitter(
                server_url="https://example.com/api/data",
                auth_token="   "
            )
    
    def test_http_url_logs_warning(self, caplog):
        """Test that non-HTTPS URL logs a warning."""
        transmitter = HTTPTransmitter(
            server_url="http://example.com/api/data",
            auth_token="test-token"
        )
        assert "does not use HTTPS" in caplog.text


class TestSendPayload:
    """Test send_payload method."""
    
    @patch('src.http_transmitter.requests.post')
    def test_successful_transmission(self, mock_post):
        """Test successful payload transmission."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        payload = {
            "employee_name": "John Doe",
            "timestamp": "2024-01-15T10:00:00Z",
            "activity": {"work_seconds": 600, "idle_seconds": 0}
        }
        
        success, error = transmitter.send_payload(payload)
        
        assert success is True
        assert error is None
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json'] == payload
        assert call_args[1]['headers']['Authorization'] == 'Bearer test-token'
        assert call_args[1]['headers']['Content-Type'] == 'application/json'
    
    @patch('src.http_transmitter.requests.post')
    def test_authentication_failure(self, mock_post):
        """Test handling of 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="invalid-token"
        )
        
        payload = {"employee_name": "John Doe"}
        success, error = transmitter.send_payload(payload)
        
        assert success is False
        assert "Authentication failed" in error
    
    @patch('src.http_transmitter.requests.post')
    def test_bad_request_error(self, mock_post):
        """Test handling of 400 bad request error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid payload structure"
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        payload = {"invalid": "data"}
        success, error = transmitter.send_payload(payload)
        
        assert success is False
        assert "Bad request" in error
    
    @patch('src.http_transmitter.requests.post')
    def test_server_error_500(self, mock_post):
        """Test handling of 500 server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        payload = {"employee_name": "John Doe"}
        success, error = transmitter.send_payload(payload)
        
        assert success is False
        assert "Server error" in error
        assert "500" in error
    
    @patch('src.http_transmitter.requests.post')
    def test_server_error_503(self, mock_post):
        """Test handling of 503 service unavailable error."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = "Service unavailable"
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        payload = {"employee_name": "John Doe"}
        success, error = transmitter.send_payload(payload)
        
        assert success is False
        assert "Server error" in error
    
    @patch('src.http_transmitter.requests.post')
    def test_unexpected_status_code(self, mock_post):
        """Test handling of unexpected status codes."""
        mock_response = Mock()
        mock_response.status_code = 418  # I'm a teapot
        mock_response.text = "Unexpected response"
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        payload = {"employee_name": "John Doe"}
        success, error = transmitter.send_payload(payload)
        
        assert success is False
        assert "Unexpected response" in error
        assert "418" in error
    
    @patch('src.http_transmitter.requests.post')
    def test_connection_error(self, mock_post):
        """Test handling of connection errors."""
        mock_post.side_effect = ConnectionError("Connection refused")
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        payload = {"employee_name": "John Doe"}
        success, error = transmitter.send_payload(payload)
        
        assert success is False
        assert "Network error" in error
    
    @patch('src.http_transmitter.requests.post')
    def test_timeout_error(self, mock_post):
        """Test handling of timeout errors."""
        mock_post.side_effect = Timeout("Request timed out")
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        payload = {"employee_name": "John Doe"}
        success, error = transmitter.send_payload(payload)
        
        assert success is False
        assert "Network error" in error
    
    @patch('src.http_transmitter.requests.post')
    def test_request_exception(self, mock_post):
        """Test handling of general request exceptions."""
        mock_post.side_effect = RequestException("Request failed")
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        payload = {"employee_name": "John Doe"}
        success, error = transmitter.send_payload(payload)
        
        assert success is False
        assert "Request failed" in error
    
    @patch('src.http_transmitter.requests.post')
    def test_unexpected_exception(self, mock_post):
        """Test handling of unexpected exceptions."""
        mock_post.side_effect = Exception("Unexpected error")
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        payload = {"employee_name": "John Doe"}
        success, error = transmitter.send_payload(payload)
        
        assert success is False
        assert "Unexpected error" in error
    
    def test_empty_payload_returns_error(self):
        """Test that empty payload returns error."""
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        success, error = transmitter.send_payload({})
        
        assert success is False
        assert "Payload cannot be empty" in error
    
    @patch('src.http_transmitter.requests.post')
    def test_timeout_configuration(self, mock_post):
        """Test that timeout is configured correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        payload = {"employee_name": "John Doe"}
        transmitter.send_payload(payload)
        
        # Verify timeout was set
        call_args = mock_post.call_args
        assert call_args[1]['timeout'] == HTTPTransmitter.REQUEST_TIMEOUT


class TestConnectionTest:
    """Test test_connection method."""
    
    @patch('src.http_transmitter.requests.head')
    def test_successful_connection(self, mock_head):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        success, error = transmitter.test_connection()
        
        assert success is True
        assert error is None
    
    @patch('src.http_transmitter.requests.head')
    def test_connection_with_404_still_succeeds(self, mock_head):
        """Test that 404 response still indicates server is reachable."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        success, error = transmitter.test_connection()
        
        assert success is True
        assert error is None
    
    @patch('src.http_transmitter.requests.head')
    def test_connection_with_405_still_succeeds(self, mock_head):
        """Test that 405 response still indicates server is reachable."""
        mock_response = Mock()
        mock_response.status_code = 405
        mock_head.return_value = mock_response
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        success, error = transmitter.test_connection()
        
        assert success is True
        assert error is None
    
    @patch('src.http_transmitter.requests.head')
    def test_connection_failure(self, mock_head):
        """Test connection failure."""
        mock_head.side_effect = ConnectionError("Connection refused")
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        success, error = transmitter.test_connection()
        
        assert success is False
        assert "Connection test failed" in error
    
    @patch('src.http_transmitter.requests.head')
    def test_connection_timeout(self, mock_head):
        """Test connection timeout."""
        mock_head.side_effect = Timeout("Request timed out")
        
        transmitter = HTTPTransmitter(
            server_url="https://example.com/api/data",
            auth_token="test-token"
        )
        
        success, error = transmitter.test_connection()
        
        assert success is False
        assert "Connection test failed" in error

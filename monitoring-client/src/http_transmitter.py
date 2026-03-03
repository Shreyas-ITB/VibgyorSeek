"""
HTTP Transmission Module

This module handles sending data payloads to the monitoring server via HTTPS POST requests.
Includes authentication token handling and response processing.

Requirements: 6.3, 18.1
"""

import logging
import requests
from typing import Dict, Any, Optional, Tuple
from requests.exceptions import RequestException, Timeout, ConnectionError


logger = logging.getLogger(__name__)


class TransmissionError(Exception):
    """Base exception for transmission errors."""
    pass


class AuthenticationError(TransmissionError):
    """Exception raised when authentication fails."""
    pass


class ServerError(TransmissionError):
    """Exception raised when server returns an error."""
    pass


class NetworkError(TransmissionError):
    """Exception raised when network communication fails."""
    pass


class HTTPTransmitter:
    """Handles HTTP transmission of monitoring data to the server."""
    
    # Request timeout in seconds
    REQUEST_TIMEOUT = 30
    
    def __init__(self, server_url: str, auth_token: str):
        """
        Initialize the HTTP transmitter.
        
        Args:
            server_url: The server endpoint URL for data transmission
            auth_token: Authentication token for server requests
        
        Raises:
            ValueError: If server_url or auth_token is empty
        """
        if not server_url or not server_url.strip():
            raise ValueError("server_url cannot be empty")
        if not auth_token or not auth_token.strip():
            raise ValueError("auth_token cannot be empty")
        
        self.server_url = server_url.strip()
        self.auth_token = auth_token.strip()
        
        # Validate that server_url uses HTTPS
        if not self.server_url.lower().startswith('https://'):
            logger.warning(
                f"Server URL does not use HTTPS: {self.server_url}. "
                "Data transmission may not be secure."
            )
    
    def send_payload(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Send a data payload to the server via HTTPS POST request.
        
        Args:
            payload: The data payload dictionary to send
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            - (True, None) if transmission was successful
            - (False, error_message) if transmission failed
        
        Requirements: 6.3, 18.1
        """
        if not payload:
            error_msg = "Payload cannot be empty"
            logger.error(error_msg)
            return False, error_msg
        
        # Prepare headers with authentication token
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_token}'
        }
        
        try:
            logger.debug(f"Sending payload to {self.server_url}")
            
            # Print what we're sending
            app_count = len(payload.get('applications', []))
            apps_with_duration = [a for a in payload.get('applications', []) if a.get('duration', 0) > 0]
            print(f"\n📤 SENDING TO SERVER:")
            print(f"   • {app_count} total applications")
            print(f"   • {len(apps_with_duration)} apps with duration > 0")
            if apps_with_duration:
                for app in apps_with_duration[:5]:
                    print(f"     - {app['name']}: {app['duration']}s")
                if len(apps_with_duration) > 5:
                    print(f"     ... and {len(apps_with_duration) - 5} more")
            
            # Send HTTPS POST request
            response = requests.post(
                self.server_url,
                json=payload,
                headers=headers,
                timeout=self.REQUEST_TIMEOUT
            )
            
            # Handle response based on status code
            if response.status_code == 200:
                print(f"✅ SUCCESS: Data transmitted to server")
                logger.info("Payload transmitted successfully")
                return True, None
            
            elif response.status_code == 401:
                error_msg = "Authentication failed: Invalid or missing token"
                logger.error(error_msg)
                raise AuthenticationError(error_msg)
            
            elif response.status_code == 400:
                error_msg = f"Bad request: {response.text}"
                logger.error(error_msg)
                raise ServerError(error_msg)
            
            elif 500 <= response.status_code < 600:
                error_msg = f"Server error (status {response.status_code}): {response.text}"
                logger.error(error_msg)
                raise ServerError(error_msg)
            
            else:
                error_msg = f"Unexpected response (status {response.status_code}): {response.text}"
                logger.warning(error_msg)
                return False, error_msg
        
        except AuthenticationError as e:
            # Re-raise authentication errors as they need special handling
            return False, str(e)
        
        except (ConnectionError, Timeout) as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        except RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Unexpected error during transmission: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test the connection to the server with a minimal request.
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        headers = {
            'Authorization': f'Bearer {self.auth_token}'
        }
        
        try:
            # Try a simple GET or HEAD request to check connectivity
            # Note: This assumes the server has a health check endpoint
            # If not, this will just verify network connectivity
            response = requests.head(
                self.server_url,
                headers=headers,
                timeout=5
            )
            
            if response.status_code in [200, 404, 405]:
                # 404/405 means server is reachable even if endpoint doesn't support HEAD
                logger.info("Server connection test successful")
                return True, None
            else:
                error_msg = f"Server returned status {response.status_code}"
                logger.warning(error_msg)
                return False, error_msg
        
        except (ConnectionError, Timeout) as e:
            error_msg = f"Connection test failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Connection test error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

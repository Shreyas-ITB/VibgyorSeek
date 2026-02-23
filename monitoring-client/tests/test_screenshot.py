"""Unit tests for the screenshot capture module."""

import base64
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from src.screenshot import ScreenshotCapture


class TestScreenshotCapture:
    """Test cases for ScreenshotCapture class."""
    
    def test_init_default_quality(self):
        """Test initialization with default JPEG quality."""
        capture = ScreenshotCapture()
        assert capture.jpeg_quality == ScreenshotCapture.DEFAULT_JPEG_QUALITY
    
    def test_init_custom_quality(self):
        """Test initialization with custom JPEG quality."""
        capture = ScreenshotCapture(jpeg_quality=85)
        assert capture.jpeg_quality == 85
    
    def test_init_invalid_quality_too_low(self):
        """Test initialization with invalid quality (too low)."""
        capture = ScreenshotCapture(jpeg_quality=0)
        assert capture.jpeg_quality == ScreenshotCapture.DEFAULT_JPEG_QUALITY
    
    def test_init_invalid_quality_too_high(self):
        """Test initialization with invalid quality (too high)."""
        capture = ScreenshotCapture(jpeg_quality=101)
        assert capture.jpeg_quality == ScreenshotCapture.DEFAULT_JPEG_QUALITY
    
    def test_init_invalid_quality_not_int(self):
        """Test initialization with non-integer quality."""
        capture = ScreenshotCapture(jpeg_quality="75")
        assert capture.jpeg_quality == ScreenshotCapture.DEFAULT_JPEG_QUALITY
    
    @patch('src.screenshot.ImageGrab.grab')
    def test_capture_screenshot_success(self, mock_grab):
        """Test successful screenshot capture."""
        # Create a mock image
        mock_image = Image.new('RGB', (1920, 1080), color='red')
        mock_grab.return_value = mock_image
        
        capture = ScreenshotCapture()
        result = capture.capture_screenshot()
        
        # Verify the result is a base64 string
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify it can be decoded
        decoded = base64.b64decode(result)
        assert len(decoded) > 0
        
        # Verify ImageGrab was called with all_screens=True
        mock_grab.assert_called_once_with(all_screens=True)
    
    @patch('src.screenshot.ImageGrab.grab')
    def test_capture_screenshot_multi_monitor(self, mock_grab):
        """Test screenshot capture with multi-monitor setup."""
        # Create a mock image representing multiple monitors
        mock_image = Image.new('RGB', (3840, 1080), color='blue')
        mock_grab.return_value = mock_image
        
        capture = ScreenshotCapture()
        result = capture.capture_screenshot()
        
        assert result is not None
        assert isinstance(result, str)
        
        # Verify all_screens parameter is used
        mock_grab.assert_called_once_with(all_screens=True)
    
    @patch('src.screenshot.ImageGrab.grab')
    def test_capture_screenshot_compression(self, mock_grab):
        """Test that screenshot is compressed to JPEG."""
        # Create a mock image
        mock_image = Image.new('RGB', (1920, 1080), color='green')
        mock_grab.return_value = mock_image
        
        capture = ScreenshotCapture(jpeg_quality=50)
        result = capture.capture_screenshot()
        
        assert result is not None
        
        # Decode and verify it's a valid JPEG
        decoded = base64.b64decode(result)
        # JPEG files start with FF D8 FF
        assert decoded[:3] == b'\xff\xd8\xff'
    
    @patch('src.screenshot.ImageGrab.grab')
    def test_capture_screenshot_different_qualities(self, mock_grab):
        """Test that different quality settings produce different sizes."""
        mock_image = Image.new('RGB', (1920, 1080), color='yellow')
        mock_grab.return_value = mock_image
        
        # Capture with high quality
        capture_high = ScreenshotCapture(jpeg_quality=95)
        result_high = capture_high.capture_screenshot()
        size_high = len(base64.b64decode(result_high))
        
        # Capture with low quality
        capture_low = ScreenshotCapture(jpeg_quality=30)
        result_low = capture_low.capture_screenshot()
        size_low = len(base64.b64decode(result_low))
        
        # Lower quality should produce smaller file
        assert size_low < size_high
    
    @patch('src.screenshot.ImageGrab.grab')
    def test_capture_screenshot_failure(self, mock_grab):
        """Test screenshot capture when ImageGrab fails."""
        mock_grab.side_effect = Exception("Screen capture failed")
        
        capture = ScreenshotCapture()
        result = capture.capture_screenshot()
        
        # Should return None on failure
        assert result is None
    
    def test_get_screenshot_size(self):
        """Test getting the size of a base64-encoded screenshot."""
        # Create a small test image
        test_data = b"test image data"
        base64_data = base64.b64encode(test_data).decode('utf-8')
        
        capture = ScreenshotCapture()
        size = capture.get_screenshot_size(base64_data)
        
        assert size == len(test_data)
    
    def test_get_screenshot_size_invalid_base64(self):
        """Test getting size with invalid base64 data."""
        capture = ScreenshotCapture()
        size = capture.get_screenshot_size("not valid base64!!!")
        
        # Should return 0 on error
        assert size == 0
    
    @patch('src.screenshot.ImageGrab.grab')
    def test_capture_screenshot_returns_base64_string(self, mock_grab):
        """Test that capture_screenshot returns a valid base64 string."""
        mock_image = Image.new('RGB', (800, 600), color='white')
        mock_grab.return_value = mock_image
        
        capture = ScreenshotCapture()
        result = capture.capture_screenshot()
        
        # Verify it's a valid base64 string by decoding
        try:
            decoded = base64.b64decode(result)
            assert len(decoded) > 0
        except Exception:
            pytest.fail("Result is not valid base64")

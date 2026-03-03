"""Screenshot capture module for the monitoring client."""

import base64
import io
from typing import Optional
from PIL import ImageGrab
from .logger import get_logger

logger = get_logger()


class ScreenshotCapture:
    """Handles desktop screenshot capture with multi-monitor support."""
    
    DEFAULT_JPEG_QUALITY = 75
    
    def __init__(self, jpeg_quality: Optional[int] = None):
        """
        Initialize the screenshot capture module.
        
        Args:
            jpeg_quality: JPEG compression quality (1-100). Defaults to 75.
        """
        if jpeg_quality is None:
            self.jpeg_quality = self.DEFAULT_JPEG_QUALITY
        else:
            if not isinstance(jpeg_quality, int) or jpeg_quality < 1 or jpeg_quality > 100:
                logger.warning(
                    f"Invalid JPEG quality {jpeg_quality}, using default {self.DEFAULT_JPEG_QUALITY}"
                )
                self.jpeg_quality = self.DEFAULT_JPEG_QUALITY
            else:
                self.jpeg_quality = jpeg_quality
    
    def capture_screenshot(self) -> Optional[str]:
        """
        Capture a screenshot of the full desktop including all monitors.
        
        Returns:
            Base64-encoded JPEG image data, or None if capture fails.
        """
        try:
            # Capture all screens (multi-monitor support)
            # ImageGrab.grab() with no arguments captures the entire virtual screen
            screenshot = ImageGrab.grab(all_screens=True)
            
            # Compress to JPEG format
            buffer = io.BytesIO()
            screenshot.save(buffer, format='JPEG', quality=self.jpeg_quality, optimize=True)
            
            # Get the compressed image data
            image_data = buffer.getvalue()
            
            # Encode to base64
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            logger.debug(
                f"Screenshot captured: {screenshot.size[0]}x{screenshot.size[1]}, "
                f"compressed size: {len(image_data)} bytes"
            )
            
            return base64_data
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None
    
    def get_screenshot_size(self, base64_data: str) -> int:
        """
        Get the size of a base64-encoded screenshot in bytes.
        
        Args:
            base64_data: Base64-encoded image data.
        
        Returns:
            Size in bytes of the decoded image data.
        """
        try:
            decoded = base64.b64decode(base64_data)
            return len(decoded)
        except Exception as e:
            logger.error(f"Failed to get screenshot size: {e}")
            return 0

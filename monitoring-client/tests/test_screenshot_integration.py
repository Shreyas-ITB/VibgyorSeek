"""Integration tests for screenshot capture module."""

import base64
import pytest
from PIL import Image
import io
from src.screenshot import ScreenshotCapture


class TestScreenshotIntegration:
    """Integration tests for real screenshot capture."""
    
    def test_capture_real_screenshot(self):
        """Test capturing a real screenshot from the desktop."""
        capture = ScreenshotCapture()
        result = capture.capture_screenshot()
        
        # Verify we got a result
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify it's valid base64
        try:
            decoded = base64.b64decode(result)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Invalid base64 data: {e}")
        
        # Verify it's a valid JPEG image
        try:
            image = Image.open(io.BytesIO(decoded))
            assert image.format == 'JPEG'
            assert image.size[0] > 0
            assert image.size[1] > 0
            print(f"Screenshot captured: {image.size[0]}x{image.size[1]}")
        except Exception as e:
            pytest.fail(f"Invalid JPEG image: {e}")
    
    def test_compression_reduces_size(self):
        """Test that JPEG compression actually reduces file size."""
        capture = ScreenshotCapture(jpeg_quality=75)
        result = capture.capture_screenshot()
        
        assert result is not None
        
        # Decode the compressed image
        compressed_data = base64.b64decode(result)
        compressed_size = len(compressed_data)
        
        # Load the image and estimate uncompressed size
        image = Image.open(io.BytesIO(compressed_data))
        # Uncompressed RGB image size = width * height * 3 bytes
        uncompressed_size = image.size[0] * image.size[1] * 3
        
        # Compressed should be significantly smaller
        assert compressed_size < uncompressed_size
        compression_ratio = uncompressed_size / compressed_size
        print(f"Compression ratio: {compression_ratio:.2f}x")
        print(f"Uncompressed: {uncompressed_size:,} bytes")
        print(f"Compressed: {compressed_size:,} bytes")
        
        # Expect at least 2x compression
        assert compression_ratio >= 2.0
    
    def test_different_quality_settings(self):
        """Test that different quality settings produce different file sizes."""
        # Capture with high quality
        capture_high = ScreenshotCapture(jpeg_quality=95)
        result_high = capture_high.capture_screenshot()
        size_high = len(base64.b64decode(result_high))
        
        # Capture with medium quality
        capture_medium = ScreenshotCapture(jpeg_quality=75)
        result_medium = capture_medium.capture_screenshot()
        size_medium = len(base64.b64decode(result_medium))
        
        # Capture with low quality
        capture_low = ScreenshotCapture(jpeg_quality=30)
        result_low = capture_low.capture_screenshot()
        size_low = len(base64.b64decode(result_low))
        
        print(f"High quality (95): {size_high:,} bytes")
        print(f"Medium quality (75): {size_medium:,} bytes")
        print(f"Low quality (30): {size_low:,} bytes")
        
        # Verify size ordering
        assert size_low < size_medium < size_high
    
    def test_get_screenshot_size_accuracy(self):
        """Test that get_screenshot_size returns accurate size."""
        capture = ScreenshotCapture()
        result = capture.capture_screenshot()
        
        assert result is not None
        
        # Get size using the method
        reported_size = capture.get_screenshot_size(result)
        
        # Get actual size by decoding
        actual_size = len(base64.b64decode(result))
        
        # Should match exactly
        assert reported_size == actual_size
    
    def test_multiple_captures_consistency(self):
        """Test that multiple captures produce consistent results."""
        capture = ScreenshotCapture(jpeg_quality=75)
        
        # Capture multiple screenshots
        results = [capture.capture_screenshot() for _ in range(3)]
        
        # All should succeed
        assert all(r is not None for r in results)
        
        # All should be valid base64
        sizes = []
        for result in results:
            decoded = base64.b64decode(result)
            sizes.append(len(decoded))
        
        # Sizes should be similar (within 10% variance due to screen content changes)
        avg_size = sum(sizes) / len(sizes)
        for size in sizes:
            variance = abs(size - avg_size) / avg_size
            assert variance < 0.1, f"Size variance too high: {variance:.2%}"

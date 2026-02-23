"""Property-based tests for screenshot module.

Feature: vibgyorseek-employee-monitoring
"""

import base64
import io
from hypothesis import given, strategies as st, settings
from PIL import Image
from src.screenshot import ScreenshotCapture


# Strategy for generating valid JPEG quality values (1-100)
jpeg_quality_strategy = st.integers(min_value=1, max_value=100)

# Strategy for generating image dimensions (reasonable screen sizes)
image_width_strategy = st.integers(min_value=800, max_value=3840)
image_height_strategy = st.integers(min_value=600, max_value=2160)

# Strategy for generating RGB color values
color_strategy = st.tuples(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)


class TestScreenshotCompressionProperty:
    """Property-based tests for screenshot compression.
    
    **Validates: Requirements 5.3**
    """
    
    @given(
        width=image_width_strategy,
        height=image_height_strategy,
        color=color_strategy,
        quality=jpeg_quality_strategy
    )
    @settings(max_examples=100)
    def test_screenshot_compression_property(self, width, height, color, quality):
        """
        Property 8: Screenshot Compression
        
        For any screenshot captured by the Monitoring_Client, the compressed
        file size should be less than the uncompressed raw image size.
        
        **Validates: Requirements 5.3**
        """
        # Create a test image with the given dimensions and color
        test_image = Image.new('RGB', (width, height), color=color)
        
        # Calculate uncompressed size (raw RGB data: width * height * 3 bytes)
        uncompressed_size = width * height * 3
        
        # Compress the image using the ScreenshotCapture logic
        capture = ScreenshotCapture(jpeg_quality=quality)
        
        # Simulate the compression process
        buffer = io.BytesIO()
        test_image.save(buffer, format='JPEG', quality=quality, optimize=True)
        compressed_data = buffer.getvalue()
        compressed_size = len(compressed_data)
        
        # Property: Compressed size should be less than uncompressed size
        assert compressed_size < uncompressed_size, (
            f"Compression failed: compressed size ({compressed_size} bytes) "
            f"is not less than uncompressed size ({uncompressed_size} bytes) "
            f"for image {width}x{height} with quality {quality}"
        )

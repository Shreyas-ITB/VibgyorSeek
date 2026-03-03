"""Unit tests for logging module."""

import logging
from pathlib import Path
from src.logger import setup_logging, get_logger


class TestLogger:
    """Test cases for logging configuration."""
    
    def teardown_method(self):
        """Clean up logger handlers after each test."""
        logger = logging.getLogger("vibgyorseek_client")
        # Remove all handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
    
    def test_setup_logging_creates_log_directory(self, tmp_path):
        """Test that setup_logging creates the log directory."""
        log_dir = tmp_path / "test_logs"
        logger = setup_logging(log_level="INFO", log_dir=str(log_dir))
        
        assert log_dir.exists()
        assert log_dir.is_dir()
    
    def test_setup_logging_creates_log_file(self, tmp_path):
        """Test that setup_logging creates a log file."""
        log_dir = tmp_path / "test_logs"
        logger = setup_logging(log_level="INFO", log_dir=str(log_dir))
        
        log_file = log_dir / "monitoring_client.log"
        
        # Write a test message
        logger.info("Test message")
        
        # Flush all handlers to ensure data is written
        for handler in logger.handlers:
            handler.flush()
        
        assert log_file.exists()
        assert log_file.is_file()
    
    def test_logger_writes_messages(self, tmp_path):
        """Test that logger writes messages to file."""
        log_dir = tmp_path / "test_logs"
        logger = setup_logging(log_level="DEBUG", log_dir=str(log_dir))
        
        test_message = "Test log message"
        logger.info(test_message)
        
        # Flush all handlers to ensure data is written
        for handler in logger.handlers:
            handler.flush()
        
        log_file = log_dir / "monitoring_client.log"
        content = log_file.read_text()
        
        assert test_message in content
    
    def test_logger_respects_log_level(self, tmp_path):
        """Test that logger respects the configured log level."""
        log_dir = tmp_path / "test_logs"
        logger = setup_logging(log_level="WARNING", log_dir=str(log_dir))
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        
        # Flush all handlers to ensure data is written
        for handler in logger.handlers:
            handler.flush()
        
        log_file = log_dir / "monitoring_client.log"
        content = log_file.read_text()
        
        assert "Debug message" not in content
        assert "Info message" not in content
        assert "Warning message" in content
    
    def test_get_logger_returns_configured_logger(self, tmp_path):
        """Test that get_logger returns the configured logger."""
        log_dir = tmp_path / "test_logs"
        setup_logging(log_level="INFO", log_dir=str(log_dir))
        
        logger = get_logger()
        
        assert logger.name == "vibgyorseek_client"
        assert logger.level == logging.INFO

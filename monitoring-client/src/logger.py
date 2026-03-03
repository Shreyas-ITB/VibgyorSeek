"""Logging configuration for the monitoring client."""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class SafeStreamHandler(logging.StreamHandler):
    """
    Stream handler that safely handles Unicode characters.
    Replaces characters that can't be encoded with '?' to prevent crashes.
    """
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Try to encode with the stream's encoding, replacing unsupported chars
            if hasattr(stream, 'encoding') and stream.encoding:
                msg = msg.encode(stream.encoding, errors='replace').decode(stream.encoding)
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


class FlushingFileHandler(RotatingFileHandler):
    """File handler that flushes after each write for real-time logging."""
    def emit(self, record):
        super().emit(record)
        self.flush()


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    """
    Set up logging configuration with file and console handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("vibgyorseek_client")
    logger.setLevel(getattr(logging, log_level))
    
    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Daily log file with current date in filename
    current_date = datetime.now().strftime('%Y-%m-%d')
    daily_log_file = log_path / f"logs {current_date}.txt"
    
    # File handler for daily logs with UTF-8 encoding (10MB max, keep 5 backup files)
    daily_file_handler = FlushingFileHandler(
        daily_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'  # Use UTF-8 for file to support emojis
    )
    daily_file_handler.setLevel(logging.DEBUG)
    daily_file_handler.setFormatter(detailed_formatter)
    
    # Console handler with safe Unicode handling
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)
    
    # Add handlers to logger
    logger.addHandler(daily_file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger() -> logging.Logger:
    """Get the configured logger instance."""
    return logging.getLogger("vibgyorseek_client")

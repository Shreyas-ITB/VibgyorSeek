"""
VibgyorSeek Employee Monitoring Client - Main Entry Point

This is the main entry point for the monitoring client application.
Runs in console mode by default, showing real-time monitoring status.

Press Ctrl+C to stop the client.

Requirements: 7.1, 7.2, 14.1, 14.2
"""

import sys
import os
import argparse
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.logger import setup_logging, get_logger
from src.config import Config, retrieve_client_id

# Initialize logging with daily log files
setup_logging(log_level="INFO", log_dir="logs")
logger = get_logger()


def run_console_mode():
    """
    Run the monitoring client in console mode (foreground).
    
    This mode is useful for testing and debugging.
    """
    print("VibgyorSeek Employee Monitoring Client")
    print("=" * 50)
    print()
    
    # Get or generate client ID
    try:
        client_id = retrieve_client_id()
        print(f"Client ID: {client_id}")
        print()
    except Exception as e:
        print(f"Error retrieving client ID: {e}")
        return 1
    
    # Load configuration
    try:
        config = Config()
        print("Configuration loaded:")
        print(f"  Server URL: {config.server_url}")
        print(f"  Data interval: {config.data_send_interval_minutes} minutes")
        print(f"  Screenshot interval: {config.screenshot_interval_minutes} minutes")
        print(f"  Idle threshold: {config.idle_threshold_seconds} seconds")
        print()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        logger.error(f"Configuration error: {e}", exc_info=True)
        return 1
    
    # Start monitoring loop
    try:
        from src.monitoring_loop import MonitoringLoop
        
        print("Starting monitoring loop...")
        print("Press Ctrl+C to stop")
        print()
        
        loop = MonitoringLoop(config)
        loop.start()
        
        # Keep running until interrupted
        while loop.is_running():
            time.sleep(1)
            
            # Print status every 30 seconds
            if int(time.time()) % 30 == 0:
                status = loop.get_status()
                print(f"Status: {status['current_state']} | "
                      f"Work: {status['work_seconds']}s | "
                      f"Idle: {status['idle_seconds']}s | "
                      f"Queue: {status['queue_size']}")
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        if 'loop' in locals():
            loop.stop()
        print("Stopped.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


def main():
    """
    Main entry point for the application.
    
    Runs the monitoring client directly in console mode.
    """
    parser = argparse.ArgumentParser(
        description='VibgyorSeek Employee Monitoring Client'
    )
    parser.add_argument(
        '--show-id',
        action='store_true',
        help='Show client ID and exit'
    )
    
    args = parser.parse_args()
    
    # Handle show ID
    if args.show_id:
        try:
            client_id = retrieve_client_id()
            print(f"Client ID: {client_id}")
            return 0
        except Exception as e:
            print(f"Error retrieving client ID: {e}")
            return 1
    
    # Run in console mode by default
    return run_console_mode()


if __name__ == '__main__':
    sys.exit(main())

"""
VibgyorSeek Employee Monitoring Client - Main Entry Point

This is the main entry point for the monitoring client application.
It can run in two modes:
1. Service mode: Runs as a Windows service (default)
2. Console mode: Runs in the foreground for testing

Requirements: 7.1, 7.2, 14.1, 14.2
"""

import sys
import os
import argparse
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.logger import get_logger
from src.config import Config, retrieve_client_id
from src.service_manager import ServiceManager, MonitoringService, main as service_main

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
    
    Handles command-line arguments and dispatches to appropriate mode.
    """
    parser = argparse.ArgumentParser(
        description='VibgyorSeek Employee Monitoring Client'
    )
    parser.add_argument(
        '--console',
        action='store_true',
        help='Run in console mode (foreground) instead of as a service'
    )
    parser.add_argument(
        '--install',
        action='store_true',
        help='Install as Windows service'
    )
    parser.add_argument(
        '--remove',
        action='store_true',
        help='Remove Windows service'
    )
    parser.add_argument(
        '--start',
        action='store_true',
        help='Start Windows service'
    )
    parser.add_argument(
        '--stop',
        action='store_true',
        help='Stop Windows service'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Get Windows service status'
    )
    parser.add_argument(
        '--show-id',
        action='store_true',
        help='Show client ID'
    )
    
    # If no arguments, check if we're being run by the service control manager
    if len(sys.argv) == 1:
        # Try to run as service
        try:
            service_main()
            return 0
        except Exception as e:
            # If service mode fails, show help
            print(f"Error starting service: {e}")
            print()
            parser.print_help()
            return 1
    
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
    
    # Handle service management commands
    if args.install:
        print("Installing Windows service...")
        if ServiceManager.install_service():
            print("Service installed successfully.")
            print("Use --start to start the service.")
            return 0
        else:
            print("Service installation failed.")
            return 1
    
    if args.remove:
        print("Removing Windows service...")
        if ServiceManager.remove_service():
            print("Service removed successfully.")
            return 0
        else:
            print("Service removal failed.")
            return 1
    
    if args.start:
        print("Starting Windows service...")
        if ServiceManager.start_service():
            print("Service started successfully.")
            return 0
        else:
            print("Service start failed.")
            return 1
    
    if args.stop:
        print("Stopping Windows service...")
        if ServiceManager.stop_service():
            print("Service stopped successfully.")
            return 0
        else:
            print("Service stop failed.")
            return 1
    
    if args.status:
        print("Checking service status...")
        status = ServiceManager.get_service_status()
        if status:
            print(f"Service status: {status['status']}")
            print(f"Status code: {status['status_code']}")
            return 0
        else:
            print("Failed to get service status.")
            return 1
    
    # Handle console mode
    if args.console:
        return run_console_mode()
    
    # Default: show help
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())

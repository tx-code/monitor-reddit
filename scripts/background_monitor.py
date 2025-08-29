#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reddit Monitor - Background Monitoring Script
Background process for continuous Reddit monitoring
"""

import os
import sys
import signal
import time
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def setup_environment():
    """Setup Python path and environment"""
    project_root = get_project_root()
    
    # Add project root to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Change to project root directory
    os.chdir(project_root)
    
    return project_root

class BackgroundMonitor:
    """Background monitoring service"""
    
    def __init__(self):
        self.project_root = setup_environment()
        self.running = True
        
        # Import after setting up environment
        from src.core.config_manager import ConfigManager
        from src.core.reddit_monitor import RedditMonitor
        from src.utils.logger import get_logger
        
        self.config_manager = ConfigManager()
        self.logger = get_logger("background_monitor", log_dir="logs")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info("Background monitor initialized")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def create_monitor_instance(self):
        """Create a Reddit monitor instance with current config"""
        from src.core.reddit_monitor import RedditMonitor
        
        config = self.config_manager.get_monitor_config()
        
        return RedditMonitor(
            url=config.get('url', 'https://www.reddit.com/r/CNC/'),
            interval=config.get('interval_minutes', 5) * 60,
            data_dir=config.get('data_directory', 'data'),
            config_manager=self.config_manager
        )
    
    def run(self):
        """Main monitoring loop"""
        self.logger.info("Starting background monitoring service")
        
        # Start monitoring session
        self.config_manager.start_session()
        
        try:
            while self.running:
                # Check if monitoring is enabled
                if not self.config_manager.get_monitor_config().get('enabled', False):
                    self.logger.info("Monitoring disabled, stopping background service")
                    break
                
                # Check if it's time to monitor
                if self.config_manager.should_check_now():
                    monitor = self.create_monitor_instance()
                    
                    self.logger.info("Performing scheduled check...")
                    success = monitor.monitor_once()
                    
                    if success:
                        self.logger.info("Check completed successfully")
                    else:
                        self.logger.warning("Check failed")
                    
                    # Calculate wait time until next check
                    wait_time = self.config_manager.get_time_until_next_check()
                    if wait_time <= 0:
                        wait_time = self.config_manager.get_interval_seconds()
                    
                    self.logger.info(f"Next check in {wait_time} seconds")
                    
                    # Wait with periodic checks for shutdown signal
                    start_wait = time.time()
                    while self.running and (time.time() - start_wait) < wait_time:
                        time.sleep(min(10, wait_time))  # Check every 10 seconds or remaining time
                else:
                    # Not time yet, check again in 30 seconds
                    time.sleep(30)
                    
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {e}")
            raise
        finally:
            # Clean shutdown
            self.config_manager.end_session()
            self.config_manager.update_monitor_config({'enabled': False})
            self.logger.info("Background monitoring service stopped")
    
    def status(self):
        """Get current monitoring status"""
        config = self.config_manager.get_monitor_config()
        stats = self.config_manager.get_session_stats()
        
        status_info = {
            'enabled': config.get('enabled', False),
            'url': config.get('url', 'N/A'),
            'interval_minutes': config.get('interval_minutes', 5),
            'data_directory': config.get('data_directory', 'data'),
            'total_checks': stats['total_checks'],
            'failed_checks': stats['failed_checks'],
            'success_rate': stats['success_rate'],
            'last_check': stats['last_check'],
            'next_check': stats['next_check']
        }
        
        return status_info

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reddit Monitor Background Service")
    parser.add_argument('--status', action='store_true', help='Show monitoring status')
    parser.add_argument('--stop', action='store_true', help='Stop monitoring service')
    
    args = parser.parse_args()
    
    monitor = BackgroundMonitor()
    
    if args.status:
        # Show status and exit
        status = monitor.status()
        print("📊 Reddit Monitor Status:")
        print(f"  Enabled: {'✅ Yes' if status['enabled'] else '❌ No'}")
        print(f"  URL: {status['url']}")
        print(f"  Interval: {status['interval_minutes']} minutes")
        print(f"  Data Directory: {status['data_directory']}")
        print(f"  Total Checks: {status['total_checks']}")
        print(f"  Failed Checks: {status['failed_checks']}")
        print(f"  Success Rate: {status['success_rate']:.1f}%")
        if status['last_check']:
            print(f"  Last Check: {status['last_check']}")
        if status['next_check']:
            print(f"  Next Check: {status['next_check']}")
        return
    
    if args.stop:
        # Stop monitoring service
        monitor.config_manager.update_monitor_config({'enabled': False})
        print("🛑 Monitoring service stopped")
        return
    
    # Run monitoring service
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\n👋 Background monitor stopped by user")
    except Exception as e:
        print(f"❌ Background monitor error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
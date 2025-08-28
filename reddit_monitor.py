import requests
import time
import json
import os
from datetime import datetime
from hashlib import md5
import logging
from config_manager import ConfigManager

class RedditMonitor:
    def __init__(self, url="https://www.reddit.com/r/CNC/", interval=600, data_dir="data", config_manager=None):
        self.url = url
        self.interval = interval  # 10 minutes = 600 seconds
        self.data_dir = data_dir
        self.config_manager = config_manager or ConfigManager()
        
        # Load settings from config if available
        self._load_from_config()
        
        self.setup_logging()
        self.ensure_data_directory()
        
    def _load_from_config(self):
        """Load settings from config manager"""
        try:
            monitor_config = self.config_manager.get_monitor_config()
            # 只在配置存在且不为空时覆盖默认值
            if monitor_config.get('url'):
                self.url = monitor_config['url']
            if monitor_config.get('interval_minutes'):
                self.interval = monitor_config['interval_minutes'] * 60
            if monitor_config.get('data_directory'):
                self.data_dir = monitor_config['data_directory']
        except Exception as e:
            # Logger might not be initialized yet
            print(f"Warning: Failed to load config: {e}")
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('reddit_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def fetch_website_data(self):
        """Fetch website content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            # Try with SSL verification first, then without
            try:
                response = requests.get(self.url, headers=headers, timeout=30)
            except requests.exceptions.SSLError:
                self.logger.warning("SSL error, trying without verification...")
                response = requests.get(self.url, headers=headers, timeout=30, verify=False)
            
            response.raise_for_status()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'content': response.text,
                'headers': dict(response.headers),
                'url': self.url
            }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch website data: {e}")
            return None
    
    def save_data(self, data):
        """Save fetched data to file"""
        if not data:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.data_dir}/data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return filename
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            return None
    
    def get_content_hash(self, content):
        """Generate hash for content comparison"""
        if not content:
            return None
        return md5(content.encode('utf-8')).hexdigest()
    
    def check_for_changes(self, new_data):
        """Check if content has changed since last fetch"""
        latest_file = self.get_latest_data_file()
        if not latest_file:
            return True  # First time running
            
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                
            old_hash = self.get_content_hash(old_data.get('content', ''))
            new_hash = self.get_content_hash(new_data.get('content', ''))
            
            return old_hash != new_hash
        except Exception as e:
            self.logger.error(f"Error checking for changes: {e}")
            return True
    
    def get_latest_data_file(self):
        """Get the most recent data file"""
        try:
            data_files = [f for f in os.listdir(self.data_dir) if f.startswith('data_') and f.endswith('.json')]
            if not data_files:
                return None
            return os.path.join(self.data_dir, sorted(data_files)[-1])
        except Exception as e:
            self.logger.error(f"Error finding latest data file: {e}")
            return None
    
    def monitor_once(self):
        """Perform one monitoring cycle with smart scheduling"""
        success = False
        try:
            self.logger.info("Starting monitoring cycle...")
            
            data = self.fetch_website_data()
            if not data:
                self.logger.warning("No data fetched")
                self.config_manager.update_check_time(success=False)
                return False
            
            # Check for changes
            has_changes = self.check_for_changes(data)
            if has_changes:
                self.logger.info("Changes detected! Saving new data...")
                saved_file = self.save_data(data)
                if saved_file:
                    self.logger.info(f"Data saved to: {saved_file}")
                    success = True
            else:
                self.logger.info("No changes detected")
                success = True
                
            # Update check time and statistics
            self.config_manager.update_check_time(success=success)
            
            # Log statistics
            stats = self.config_manager.get_session_stats()
            self.logger.info(f"Total checks: {stats['total_checks']}, Success rate: {stats['success_rate']:.1f}%")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")
            self.config_manager.update_check_time(success=False)
            return False
    
    def start_monitoring(self):
        """Start intelligent continuous monitoring with resume capability"""
        # Start a new session
        self.config_manager.start_session()
        
        self.logger.info(f"Starting Reddit monitor for {self.url}")
        self.logger.info(f"Monitoring interval: {self.interval} seconds")
        
        # Check if we should resume from a previous session
        last_check = self.config_manager.get_last_check_time()
        if last_check:
            self.logger.info(f"Resuming from last check: {last_check}")
            
            # Calculate if we need to check now or wait
            time_until_next = self.config_manager.get_time_until_next_check()
            if time_until_next > 0:
                self.logger.info(f"Next check scheduled in {time_until_next} seconds")
                if time_until_next < self.interval:  # Don't wait more than one interval
                    self.logger.info(f"Waiting {time_until_next} seconds to resume schedule...")
                    time.sleep(time_until_next)
        else:
            self.logger.info("Starting fresh monitoring session")
        
        try:
            while True:
                # Check if it's time to monitor
                if self.config_manager.should_check_now():
                    self.monitor_once()
                    
                    # Calculate intelligent wait time
                    wait_time = self.config_manager.get_time_until_next_check()
                    if wait_time <= 0:
                        wait_time = self.interval
                        
                    self.logger.info(f"Next check scheduled in {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    # Not time yet, wait a bit and check again
                    time.sleep(10)  # Check every 10 seconds if it's time
                    
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            # End session and log final statistics
            self.config_manager.end_session()
            final_stats = self.config_manager.get_session_stats()
            self.logger.info("Session completed:")
            self.logger.info(f"  Session checks: {final_stats['session_checks']}")
            self.logger.info(f"  Total checks: {final_stats['total_checks']}")
            self.logger.info(f"  Success rate: {final_stats['success_rate']:.1f}%")
    
    def get_status(self):
        """Get current monitoring status"""
        stats = self.config_manager.get_session_stats()
        return {
            'url': self.url,
            'interval': self.interval,
            'data_directory': self.data_dir,
            'last_check': stats['last_check'],
            'next_check': stats['next_check'],
            'time_until_next': stats['time_until_next'],
            'session_checks': stats['session_checks'],
            'total_checks': stats['total_checks'],
            'failed_checks': stats['failed_checks'],
            'success_rate': stats['success_rate']
        }

if __name__ == "__main__":
    import sys
    
    monitor = RedditMonitor()
    
    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Running in test mode - single monitoring cycle")
        monitor.monitor_once()
    else:
        monitor.start_monitoring()
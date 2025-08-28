import requests
import time
import json
import os
from datetime import datetime
from hashlib import md5
import logging

class RedditMonitor:
    def __init__(self, url="https://www.reddit.com/r/CNC/", interval=600, data_dir="data"):
        self.url = url
        self.interval = interval  # 10 minutes = 600 seconds
        self.data_dir = data_dir
        self.setup_logging()
        self.ensure_data_directory()
        
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
        """Perform one monitoring cycle"""
        self.logger.info("Starting monitoring cycle...")
        
        data = self.fetch_website_data()
        if not data:
            self.logger.warning("No data fetched")
            return
        
        # Check for changes
        has_changes = self.check_for_changes(data)
        if has_changes:
            self.logger.info("Changes detected! Saving new data...")
            saved_file = self.save_data(data)
            if saved_file:
                self.logger.info(f"Data saved to: {saved_file}")
        else:
            self.logger.info("No changes detected")
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.logger.info(f"Starting Reddit monitor for {self.url}")
        self.logger.info(f"Monitoring interval: {self.interval} seconds")
        
        try:
            while True:
                self.monitor_once()
                self.logger.info(f"Waiting {self.interval} seconds until next check...")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")

if __name__ == "__main__":
    import sys
    
    monitor = RedditMonitor()
    
    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Running in test mode - single monitoring cycle")
        monitor.monitor_once()
    else:
        monitor.start_monitoring()
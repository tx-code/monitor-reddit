import requests
import time
import json
import os
import csv
import re
from datetime import datetime
from hashlib import md5
import logging
from config_manager import ConfigManager
from bs4 import BeautifulSoup

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
            
    def fetch_reddit_online_count(self):
        """Fetch Reddit subreddit online user count"""
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
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract subreddit name from URL
            subreddit_match = re.search(r'/r/([^/]+)', self.url)
            subreddit_name = subreddit_match.group(1) if subreddit_match else 'unknown'
            
            # Try different methods to find online count
            online_count = self._extract_online_count(soup, response.text)
            
            # Get member count as well
            member_count = self._extract_member_count(soup, response.text)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'subreddit': subreddit_name,
                'url': self.url,
                'online_count': online_count,
                'member_count': member_count,
                'status_code': response.status_code,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Reddit data: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'subreddit': 'unknown',
                'url': self.url,
                'online_count': None,
                'member_count': None,
                'status_code': None,
                'success': False,
                'error': str(e)
            }
    
    def _extract_online_count(self, soup, html_text):
        """Extract online user count from Reddit page"""
        # Method 1: Look for Reddit-specific HTML attributes
        attribute_patterns = [
            r'active="(\d+)"',
            r'activeUsers["\']:\s*(\d+)',
            r'activeUserCount["\']:\s*(\d+)',
            r'data-active["\']="(\d+)"',
            r'data-online["\']="(\d+)"'
        ]
        
        for pattern in attribute_patterns:
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        # Method 2: Look for "online" text patterns
        online_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s+(?:users?\s+)?online',
            r'(\d{1,3}(?:,\d{3})*)\s+(?:members?\s+)?online',
            r'(\d{1,3}(?:,\d{3})*)\s+currently\s+viewing',
            r'(\d{1,3}(?:,\d{3})*)\s+active\s+users?',
            r'(\d{1,3}(?:,\d{3})*)\s+here\s+now',
            r'"activeUserCount"[^:]*:\s*(\d+)',
            r'"activeUsers"[^:]*:\s*(\d+)'
        ]
        
        for pattern in online_patterns:
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(',', '')
                try:
                    return int(count_str)
                except ValueError:
                    continue
        
        # Method 2: Look in specific HTML elements
        if soup:
            # Try common selectors for online count
            selectors = [
                '[data-testid="online-count"]',
                '.online-count',
                '.active-users',
                '.subscribers-online'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text()
                    match = re.search(r'(\d{1,3}(?:,\d{3})*)', text)
                    if match:
                        try:
                            return int(match.group(1).replace(',', ''))
                        except ValueError:
                            continue
        
        self.logger.warning("Could not extract online count")
        return None
    
    def _extract_member_count(self, soup, html_text):
        """Extract total member count from Reddit page"""
        # Method 1: Look for Reddit-specific HTML attributes
        attribute_patterns = [
            r'subscribers="(\d+)"',
            r'subscriberCount["\']:\s*(\d+)',
            r'memberCount["\']:\s*(\d+)',
            r'data-subscribers["\']="(\d+)"'
        ]
        
        for pattern in attribute_patterns:
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        # Method 2: Look for member count patterns with suffixes
        member_patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?[kKmM]?)\s+(?:members?|subscribers?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?[kKmM]?)\s+joined',
            r'"subscriberCount"[^:]*:\s*(\d+)',
            r'"subscribers"[^:]*:\s*(\d+)'
        ]
        
        for pattern in member_patterns:
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(',', '')
                try:
                    # Handle k/K, m/M suffixes
                    if count_str.lower().endswith('k'):
                        return int(float(count_str[:-1]) * 1000)
                    elif count_str.lower().endswith('m'):
                        return int(float(count_str[:-1]) * 1000000)
                    else:
                        return int(float(count_str))
                except ValueError:
                    continue
        
        return None
    
    def save_data_to_csv(self, data):
        """Save Reddit online count data to CSV file"""
        if not data:
            return None
            
        csv_filename = f"{self.data_dir}/reddit_online_count.csv"
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(csv_filename)
        
        try:
            with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ['timestamp', 'subreddit', 'online_count', 'member_count', 'success', 'error']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                # Prepare row data
                row_data = {
                    'timestamp': data.get('timestamp'),
                    'subreddit': data.get('subreddit'),
                    'online_count': data.get('online_count'),
                    'member_count': data.get('member_count'),
                    'success': data.get('success'),
                    'error': data.get('error', '')
                }
                
                writer.writerow(row_data)
                
            self.logger.info(f"Data saved to CSV: {csv_filename}")
            return csv_filename
            
        except Exception as e:
            self.logger.error(f"Failed to save CSV data: {e}")
            return None
    
    def save_data(self, data):
        """Legacy method - redirects to CSV saving"""
        return self.save_data_to_csv(data)
    
    def get_content_hash(self, content):
        """Generate hash for content comparison"""
        if not content:
            return None
        return md5(content.encode('utf-8')).hexdigest()
    
    def check_for_changes(self, new_data):
        """Check if online count has changed since last fetch"""
        csv_filename = f"{self.data_dir}/reddit_online_count.csv"
        
        if not os.path.exists(csv_filename):
            return True  # First time running
        
        try:
            # Read the last row from CSV to get previous online count
            with open(csv_filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if not rows:
                    return True  # No previous data
                
                last_row = rows[-1]
                old_online_count = last_row.get('online_count')
                new_online_count = new_data.get('online_count')
                
                # Convert to int for comparison, handle None values
                try:
                    old_count = int(old_online_count) if old_online_count else 0
                    new_count = int(new_online_count) if new_online_count else 0
                    
                    # Always record data, but log if there's a significant change
                    change = abs(new_count - old_count)
                    if change > 0:
                        self.logger.info(f"Online count changed: {old_count} → {new_count} (Δ{new_count-old_count:+d})")
                        return True
                    else:
                        self.logger.info(f"Online count unchanged: {new_count}")
                        return False  # For CSV, we might want to record every data point
                        
                except ValueError:
                    # If we can't parse the numbers, assume there's a change
                    return True
                
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
            
            data = self.fetch_reddit_online_count()
            if not data or not data.get('success'):
                self.logger.warning("Failed to fetch Reddit data")
                self.config_manager.update_check_time(success=False)
                # Still save the failed attempt to CSV for completeness
                if data:
                    self.save_data_to_csv(data)
                return False
            
            # For Reddit online count monitoring, save data every time (to track trends)
            # But still check for changes for logging purposes
            has_changes = self.check_for_changes(data)
            
            # Always save to CSV for continuous monitoring
            saved_file = self.save_data_to_csv(data)
            if saved_file:
                online_count = data.get('online_count', 'N/A')
                member_count = data.get('member_count', 'N/A')
                subreddit = data.get('subreddit', 'unknown')
                self.logger.info(f"r/{subreddit}: {online_count} online, {member_count} members")
                success = True
            else:
                self.logger.error("Failed to save data")
                success = False
                
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
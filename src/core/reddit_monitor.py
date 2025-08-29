import requests
import time
import json
import os
import csv
import re
from datetime import datetime
from hashlib import md5
import logging
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup

from .config_manager import ConfigManager

class RedditMonitor:
    """Reddit online count monitoring system with intelligent scheduling"""
    
    def __init__(self, url: str = "https://www.reddit.com/r/CNC/", 
                 interval: int = 600, data_dir: str = "data", 
                 config_manager: Optional[ConfigManager] = None):
        self.url = url
        self.interval = interval
        self.data_dir = data_dir
        self.config_manager = config_manager or ConfigManager()
        
        self._load_from_config()
        self.setup_logging()
        self.ensure_data_directory()
        
    def _load_from_config(self) -> None:
        """Load settings from config manager"""
        try:
            monitor_config = self.config_manager.get_monitor_config()
            if monitor_config.get('url'):
                self.url = monitor_config['url']
            if monitor_config.get('interval_minutes'):
                self.interval = monitor_config['interval_minutes'] * 60
            if monitor_config.get('data_directory'):
                self.data_dir = monitor_config['data_directory']
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
        
    def setup_logging(self) -> None:
        """Setup logging configuration"""
        # Ensure logs directory exists
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{logs_dir}/reddit_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def ensure_data_directory(self) -> None:
        """Create data directory if it doesn't exist"""
        os.makedirs(self.data_dir, exist_ok=True)
            
    def fetch_reddit_online_count(self) -> Dict[str, Any]:
        """Fetch Reddit subreddit online user count"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            try:
                response = requests.get(self.url, headers=headers, timeout=30)
            except requests.exceptions.SSLError:
                self.logger.warning("SSL error, trying without verification...")
                response = requests.get(self.url, headers=headers, timeout=30, verify=False)
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract subreddit name from URL
            subreddit_match = re.search(r'/r/([^/]+)', self.url)
            subreddit_name = subreddit_match.group(1) if subreddit_match else 'unknown'
            
            online_count = self._extract_online_count(soup, response.text)
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
    
    def _extract_online_count(self, soup: BeautifulSoup, html_text: str) -> Optional[int]:
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
        
        # Method 3: Look in specific HTML elements
        if soup:
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
    
    def _extract_member_count(self, soup: BeautifulSoup, html_text: str) -> Optional[int]:
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
                    if count_str.lower().endswith('k'):
                        return int(float(count_str[:-1]) * 1000)
                    elif count_str.lower().endswith('m'):
                        return int(float(count_str[:-1]) * 1000000)
                    else:
                        return int(float(count_str))
                except ValueError:
                    continue
        
        return None
    
    def save_data_to_csv(self, data: Dict[str, Any]) -> Optional[str]:
        """Save Reddit online count data to CSV file"""
        if not data:
            return None
            
        csv_filename = f"{self.data_dir}/reddit_online_count.csv"
        file_exists = os.path.exists(csv_filename)
        
        try:
            with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ['timestamp', 'subreddit', 'online_count', 'member_count', 'success', 'error']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
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
    
    def check_for_changes(self, new_data: Dict[str, Any]) -> bool:
        """Check if online count has changed since last fetch"""
        csv_filename = f"{self.data_dir}/reddit_online_count.csv"
        
        if not os.path.exists(csv_filename):
            return True
        
        try:
            with open(csv_filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if not rows:
                    return True
                
                last_row = rows[-1]
                old_online_count = last_row.get('online_count')
                new_online_count = new_data.get('online_count')
                
                try:
                    old_count = int(old_online_count) if old_online_count else 0
                    new_count = int(new_online_count) if new_online_count else 0
                    
                    change = abs(new_count - old_count)
                    if change > 0:
                        self.logger.info(f"Online count changed: {old_count} → {new_count} (Δ{new_count-old_count:+d})")
                        return True
                    else:
                        self.logger.info(f"Online count unchanged: {new_count}")
                        return False
                        
                except ValueError:
                    return True
                
        except Exception as e:
            self.logger.error(f"Error checking for changes: {e}")
            return True
    
    def monitor_once(self) -> bool:
        """Perform one monitoring cycle"""
        success = False
        try:
            self.logger.info("Starting monitoring cycle...")
            
            data = self.fetch_reddit_online_count()
            if not data or not data.get('success'):
                self.logger.warning("Failed to fetch Reddit data")
                self.config_manager.update_check_time(success=False)
                if data:
                    self.save_data_to_csv(data)
                return False
            
            # Check for changes (for logging purposes)
            self.check_for_changes(data)
            
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
                
            self.config_manager.update_check_time(success=success)
            
            stats = self.config_manager.get_session_stats()
            self.logger.info(f"Total checks: {stats['total_checks']}, Success rate: {stats['success_rate']:.1f}%")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")
            self.config_manager.update_check_time(success=False)
            return False
    
    def start_monitoring(self) -> None:
        """Start continuous monitoring with intelligent scheduling"""
        self.config_manager.start_session()
        
        self.logger.info(f"Starting Reddit monitor for {self.url}")
        self.logger.info(f"Monitoring interval: {self.interval} seconds")
        
        last_check = self.config_manager.get_last_check_time()
        if last_check:
            self.logger.info(f"Resuming from last check: {last_check}")
            time_until_next = self.config_manager.get_time_until_next_check()
            if time_until_next > 0 and time_until_next < self.interval:
                self.logger.info(f"Waiting {time_until_next} seconds to resume schedule...")
                time.sleep(time_until_next)
        else:
            self.logger.info("Starting fresh monitoring session")
        
        try:
            while True:
                if self.config_manager.should_check_now():
                    self.monitor_once()
                    
                    wait_time = self.config_manager.get_time_until_next_check()
                    if wait_time <= 0:
                        wait_time = self.interval
                        
                    self.logger.info(f"Next check scheduled in {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    time.sleep(10)
                    
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            self.config_manager.end_session()
            final_stats = self.config_manager.get_session_stats()
            self.logger.info("Session completed:")
            self.logger.info(f"  Session checks: {final_stats['session_checks']}")
            self.logger.info(f"  Total checks: {final_stats['total_checks']}")
            self.logger.info(f"  Success rate: {final_stats['success_rate']:.1f}%")
    
    def get_status(self) -> Dict[str, Any]:
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
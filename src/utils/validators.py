import re
from typing import List, Tuple, Optional
from urllib.parse import urlparse

class URLValidator:
    """URL validation utilities"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def is_reddit_url(url: str) -> bool:
        """Check if URL is a Reddit URL"""
        try:
            parsed = urlparse(url)
            return 'reddit.com' in parsed.netloc.lower()
        except Exception:
            return False
    
    @staticmethod
    def extract_subreddit_from_url(url: str) -> Optional[str]:
        """Extract subreddit name from Reddit URL"""
        try:
            match = re.search(r'/r/([^/]+)', url)
            return match.group(1) if match else None
        except Exception:
            return None
    
    @staticmethod
    def validate_reddit_url(url: str) -> Tuple[bool, str]:
        """
        Validate Reddit URL and return status with message
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not url:
            return False, "URL cannot be empty"
        
        if not URLValidator.is_valid_url(url):
            return False, "Invalid URL format"
        
        if not URLValidator.is_reddit_url(url):
            return False, "URL must be a Reddit URL"
        
        subreddit = URLValidator.extract_subreddit_from_url(url)
        if not subreddit:
            return False, "Could not extract subreddit from URL"
        
        return True, f"Valid Reddit URL for r/{subreddit}"

class ConfigValidator:
    """Configuration validation utilities"""
    
    @staticmethod
    def validate_interval(interval_minutes: int) -> Tuple[bool, str]:
        """Validate monitoring interval"""
        if not isinstance(interval_minutes, (int, float)):
            return False, "Interval must be a number"
        
        if interval_minutes < 1:
            return False, "Interval must be at least 1 minute"
        
        if interval_minutes > 1440:  # 24 hours
            return False, "Interval cannot exceed 24 hours"
        
        return True, f"Valid interval: {interval_minutes} minutes"
    
    @staticmethod
    def validate_data_directory(data_dir: str) -> Tuple[bool, str]:
        """Validate data directory path"""
        if not data_dir:
            return False, "Data directory cannot be empty"
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in data_dir for char in invalid_chars):
            return False, "Data directory contains invalid characters"
        
        return True, f"Valid data directory: {data_dir}"
    
    @staticmethod
    def validate_config(config: dict) -> List[str]:
        """
        Validate entire configuration dictionary
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Validate monitor config
        monitor_config = config.get('monitor', {})
        
        # Validate URL
        url = monitor_config.get('url', '')
        is_valid, msg = URLValidator.validate_reddit_url(url)
        if not is_valid:
            errors.append(f"URL validation failed: {msg}")
        
        # Validate interval
        interval = monitor_config.get('interval_minutes', 0)
        is_valid, msg = ConfigValidator.validate_interval(interval)
        if not is_valid:
            errors.append(f"Interval validation failed: {msg}")
        
        # Validate data directory
        data_dir = monitor_config.get('data_directory', '')
        is_valid, msg = ConfigValidator.validate_data_directory(data_dir)
        if not is_valid:
            errors.append(f"Data directory validation failed: {msg}")
        
        return errors

def get_suggested_reddit_urls() -> List[dict]:
    """Get a list of suggested Reddit URLs for common subreddits"""
    return [
        {
            "name": "r/Python",
            "url": "https://www.reddit.com/r/Python/",
            "description": "Python programming language community"
        },
        {
            "name": "r/programming",
            "url": "https://www.reddit.com/r/programming/",
            "description": "Programming discussions and news"
        },
        {
            "name": "r/technology",
            "url": "https://www.reddit.com/r/technology/",
            "description": "Technology news and discussions"
        },
        {
            "name": "r/datascience",
            "url": "https://www.reddit.com/r/datascience/",
            "description": "Data science community"
        },
        {
            "name": "r/MachineLearning",
            "url": "https://www.reddit.com/r/MachineLearning/",
            "description": "Machine learning research and applications"
        },
        {
            "name": "r/webdev",
            "url": "https://www.reddit.com/r/webdev/",
            "description": "Web development community"
        }
    ]
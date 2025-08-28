import json
import os
from datetime import datetime

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "monitor": {
                "url": "https://www.reddit.com/r/CNC/",
                "interval_minutes": 10,
                "data_directory": "data",
                "enabled": False
            },
            "notifications": {
                "enable_changes": True,
                "enable_errors": True
            },
            "storage": {
                "max_files": 100,
                "auto_cleanup": True
            },
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat()
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_config(self.default_config, config)
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            self.config['last_modified'] = datetime.now().isoformat()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_config(self):
        """Get current configuration"""
        return self.config.copy()
    
    def update_config(self, updates):
        """Update configuration with new values"""
        try:
            self.config = self._merge_config(self.config, updates)
            return self.save_config()
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def get_monitor_config(self):
        """Get monitor-specific configuration"""
        return self.config.get('monitor', {})
    
    def update_monitor_config(self, url=None, interval_minutes=None, data_directory=None):
        """Update monitor configuration"""
        monitor_config = self.config.get('monitor', {})
        
        if url is not None:
            monitor_config['url'] = url
        if interval_minutes is not None:
            monitor_config['interval_minutes'] = max(1, int(interval_minutes))
        if data_directory is not None:
            monitor_config['data_directory'] = data_directory
            
        self.config['monitor'] = monitor_config
        return self.save_config()
    
    def get_interval_seconds(self):
        """Get monitoring interval in seconds"""
        return self.config.get('monitor', {}).get('interval_minutes', 10) * 60
    
    def get_monitor_url(self):
        """Get monitoring URL"""
        return self.config.get('monitor', {}).get('url', 'https://www.reddit.com/r/CNC/')
    
    def get_data_directory(self):
        """Get data directory"""
        return self.config.get('monitor', {}).get('data_directory', 'data')
    
    def validate_config(self):
        """Validate configuration values"""
        errors = []
        
        monitor_config = self.config.get('monitor', {})
        
        # Validate URL
        url = monitor_config.get('url', '')
        if not url or not url.startswith(('http://', 'https://')):
            errors.append("监控URL必须是有效的HTTP/HTTPS地址")
        
        # Validate interval
        interval = monitor_config.get('interval_minutes', 0)
        if not isinstance(interval, (int, float)) or interval < 1:
            errors.append("监控间隔必须大于0分钟")
        
        # Validate data directory
        data_dir = monitor_config.get('data_directory', '')
        if not data_dir:
            errors.append("数据目录不能为空")
        
        return errors
    
    def _merge_config(self, base, updates):
        """Deep merge configuration dictionaries"""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self.default_config.copy()
        self.config['created_at'] = datetime.now().isoformat()
        self.config['last_modified'] = datetime.now().isoformat()
        return self.save_config()
    
    def get_predefined_urls(self):
        """Get list of predefined popular URLs"""
        return [
            {
                "name": "Reddit - CNC",
                "url": "https://www.reddit.com/r/CNC/",
                "description": "CNC加工和数控机床讨论"
            },
            {
                "name": "Reddit - 3D打印",
                "url": "https://www.reddit.com/r/3Dprinting/",
                "description": "3D打印技术和项目"
            },
            {
                "name": "Reddit - 编程",
                "url": "https://www.reddit.com/r/programming/",
                "description": "编程技术讨论"
            },
            {
                "name": "Reddit - 技术",
                "url": "https://www.reddit.com/r/technology/",
                "description": "科技新闻和讨论"
            },
            {
                "name": "Reddit - Python",
                "url": "https://www.reddit.com/r/Python/",
                "description": "Python编程语言"
            },
            {
                "name": "Reddit - 机器学习",
                "url": "https://www.reddit.com/r/MachineLearning/",
                "description": "机器学习和人工智能"
            }
        ]

if __name__ == "__main__":
    # Test the config manager
    config_manager = ConfigManager()
    print("Default config:", json.dumps(config_manager.get_config(), indent=2, ensure_ascii=False))
    
    # Test validation
    errors = config_manager.validate_config()
    if errors:
        print("Validation errors:", errors)
    else:
        print("Configuration is valid")
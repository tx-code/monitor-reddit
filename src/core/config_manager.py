import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class ConfigManager:
    """Configuration manager for Reddit monitoring system"""
    
    def __init__(self, config_file: str = "config/config.json"):
        self.config_file = config_file
        self.default_config = {
            "monitor": {
                "url": "https://www.reddit.com/r/CNC/",
                "interval_minutes": 10,
                "data_directory": "data",
                "enabled": False,
                "last_check_time": None,
                "last_successful_check": None,
                "next_scheduled_check": None,
                "total_checks": 0,
                "failed_checks": 0,
                "continuous_mode": True
            },
            "notifications": {
                "enable_changes": True,
                "enable_errors": True
            },
            "storage": {
                "max_files": 100,
                "auto_cleanup": True
            },
            "session": {
                "start_time": None,
                "end_time": None,
                "session_duration": 0,
                "checks_this_session": 0
            },
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat()
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return self._merge_config(self.default_config, config)
            else:
                # Ensure config directory exists
                os.makedirs(os.path.dirname(self.config_file) if os.path.dirname(self.config_file) else ".", exist_ok=True)
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file) if os.path.dirname(self.config_file) else ".", exist_ok=True)
            
            self.config['last_modified'] = datetime.now().isoformat()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            self.config = self._merge_config(self.config, updates)
            return self.save_config()
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def get_monitor_config(self) -> Dict[str, Any]:
        """Get monitor-specific configuration"""
        return self.config.get('monitor', {})
    
    def update_monitor_config(self, updates: Dict[str, Any]) -> bool:
        """Update monitor configuration"""
        monitor_config = self.config.get('monitor', {}).copy()
        
        # Handle both dict and individual parameters
        if isinstance(updates, dict):
            for key, value in updates.items():
                if key == 'interval_minutes' and value is not None:
                    monitor_config['interval_minutes'] = max(1, int(value))
                elif value is not None:
                    monitor_config[key] = value
        
        self.config['monitor'] = monitor_config
        return self.save_config()
    
    def get_interval_seconds(self) -> int:
        """Get monitoring interval in seconds"""
        return self.config.get('monitor', {}).get('interval_minutes', 10) * 60
    
    def get_monitor_url(self) -> str:
        """Get monitoring URL"""
        return self.config.get('monitor', {}).get('url', 'https://www.reddit.com/r/CNC/')
    
    def get_data_directory(self) -> str:
        """Get data directory"""
        return self.config.get('monitor', {}).get('data_directory', 'data')
    
    def validate_config(self) -> List[str]:
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
    
    def _merge_config(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge configuration dictionaries"""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        self.config = self.default_config.copy()
        self.config['created_at'] = datetime.now().isoformat()
        self.config['last_modified'] = datetime.now().isoformat()
        return self.save_config()
    
    def get_predefined_urls(self) -> List[Dict[str, str]]:
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
    
    def update_check_time(self, success: bool = True) -> bool:
        """Update the last check time and statistics"""
        now = datetime.now().isoformat()
        monitor_config = self.config.get('monitor', {})
        
        monitor_config['last_check_time'] = now
        if success:
            monitor_config['last_successful_check'] = now
        
        monitor_config['total_checks'] = monitor_config.get('total_checks', 0) + 1
        if not success:
            monitor_config['failed_checks'] = monitor_config.get('failed_checks', 0) + 1
        
        # Calculate next scheduled check
        interval_minutes = monitor_config.get('interval_minutes', 10)
        next_time = datetime.now() + timedelta(minutes=interval_minutes)
        monitor_config['next_scheduled_check'] = next_time.isoformat()
        
        # Update session stats
        session_config = self.config.get('session', {})
        session_config['checks_this_session'] = session_config.get('checks_this_session', 0) + 1
        
        self.config['monitor'] = monitor_config
        self.config['session'] = session_config
        return self.save_config()
    
    def get_last_check_time(self) -> Optional[datetime]:
        """Get the last check time as datetime object"""
        last_check = self.config.get('monitor', {}).get('last_check_time')
        if last_check:
            try:
                return datetime.fromisoformat(last_check.replace('Z', '+00:00'))
            except Exception:
                return None
        return None
    
    def get_next_scheduled_check(self) -> Optional[datetime]:
        """Get the next scheduled check time as datetime object"""
        next_check = self.config.get('monitor', {}).get('next_scheduled_check')
        if next_check:
            try:
                return datetime.fromisoformat(next_check.replace('Z', '+00:00'))
            except Exception:
                return None
        return None
    
    def should_check_now(self) -> bool:
        """Determine if we should check now based on schedule"""
        if not self.config.get('monitor', {}).get('continuous_mode', True):
            return True
            
        next_check = self.get_next_scheduled_check()
        if next_check is None:
            return True
            
        return datetime.now() >= next_check
    
    def get_time_until_next_check(self) -> int:
        """Get seconds until next scheduled check"""
        next_check = self.get_next_scheduled_check()
        if next_check is None:
            return 0
            
        delta = next_check - datetime.now()
        return max(0, int(delta.total_seconds()))
    
    def start_session(self) -> bool:
        """Start a new monitoring session"""
        session_config = self.config.get('session', {})
        session_config['start_time'] = datetime.now().isoformat()
        session_config['end_time'] = None
        session_config['checks_this_session'] = 0
        
        self.config['session'] = session_config
        return self.save_config()
    
    def end_session(self) -> bool:
        """End the current monitoring session"""
        session_config = self.config.get('session', {})
        start_time_str = session_config.get('start_time')
        
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                session_config['end_time'] = end_time.isoformat()
                session_config['session_duration'] = duration
            except Exception:
                pass
        
        self.config['session'] = session_config
        return self.save_config()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        session = self.config.get('session', {})
        monitor = self.config.get('monitor', {})
        
        stats = {
            'session_start': session.get('start_time'),
            'session_checks': session.get('checks_this_session', 0),
            'total_checks': monitor.get('total_checks', 0),
            'failed_checks': monitor.get('failed_checks', 0),
            'success_rate': 0.0,
            'last_check': monitor.get('last_check_time'),
            'last_successful_check': monitor.get('last_successful_check'),
            'next_check': monitor.get('next_scheduled_check'),
            'time_until_next': self.get_time_until_next_check()
        }
        
        total = monitor.get('total_checks', 0)
        if total > 0:
            failed = monitor.get('failed_checks', 0)
            stats['success_rate'] = ((total - failed) / total) * 100
            
        return stats
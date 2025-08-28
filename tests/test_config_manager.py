import pytest
import json
import os
import tempfile
from datetime import datetime
from unittest.mock import patch, mock_open
from config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
    def teardown_method(self):
        """Clean up after each test method"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init_with_default_config(self):
        """Test initialization with default configuration"""
        config_manager = ConfigManager(self.config_file)
        config = config_manager.get_config()
        
        assert "monitor" in config
        assert "notifications" in config
        assert "storage" in config
        assert config["monitor"]["url"] == "https://www.reddit.com/r/CNC/"
        assert config["monitor"]["interval_minutes"] == 10
        assert config["monitor"]["data_directory"] == "data"
        
    def test_load_existing_config(self):
        """Test loading existing configuration file"""
        test_config = {
            "monitor": {
                "url": "https://test.com",
                "interval_minutes": 5,
                "data_directory": "test_data"
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
            
        config_manager = ConfigManager(self.config_file)
        config = config_manager.get_config()
        
        assert config["monitor"]["url"] == "https://test.com"
        assert config["monitor"]["interval_minutes"] == 5
        
    def test_save_config(self):
        """Test saving configuration to file"""
        config_manager = ConfigManager(self.config_file)
        result = config_manager.save_config()
        
        assert result is True
        assert os.path.exists(self.config_file)
        
        with open(self.config_file, 'r') as f:
            saved_config = json.load(f)
            
        assert "monitor" in saved_config
        assert "last_modified" in saved_config
        
    def test_update_config(self):
        """Test updating configuration"""
        config_manager = ConfigManager(self.config_file)
        
        updates = {
            "monitor": {
                "url": "https://updated.com",
                "interval_minutes": 15
            }
        }
        
        result = config_manager.update_config(updates)
        assert result is True
        
        config = config_manager.get_config()
        assert config["monitor"]["url"] == "https://updated.com"
        assert config["monitor"]["interval_minutes"] == 15
        # Should preserve other fields
        assert config["monitor"]["data_directory"] == "data"
        
    def test_get_interval_seconds(self):
        """Test getting interval in seconds"""
        config_manager = ConfigManager(self.config_file)
        config_manager.update_monitor_config(interval_minutes=20)
        
        seconds = config_manager.get_interval_seconds()
        assert seconds == 1200  # 20 * 60
        
    def test_validate_config_valid(self):
        """Test validation with valid configuration"""
        config_manager = ConfigManager(self.config_file)
        errors = config_manager.validate_config()
        
        assert len(errors) == 0
        
    def test_validate_config_invalid_url(self):
        """Test validation with invalid URL"""
        config_manager = ConfigManager(self.config_file)
        config_manager.update_monitor_config(url="invalid-url")
        
        errors = config_manager.validate_config()
        assert len(errors) > 0
        assert any("URL" in error for error in errors)
        
    def test_validate_config_invalid_interval(self):
        """Test validation with invalid interval"""
        config_manager = ConfigManager(self.config_file)
        config_manager.update_monitor_config(interval_minutes=0)
        
        errors = config_manager.validate_config()
        assert len(errors) > 0
        assert any("间隔" in error for error in errors)
        
    def test_validate_config_empty_directory(self):
        """Test validation with empty data directory"""
        config_manager = ConfigManager(self.config_file)
        config_manager.update_monitor_config(data_directory="")
        
        errors = config_manager.validate_config()
        assert len(errors) > 0
        assert any("目录" in error for error in errors)
        
    def test_get_predefined_urls(self):
        """Test getting predefined URLs"""
        config_manager = ConfigManager(self.config_file)
        urls = config_manager.get_predefined_urls()
        
        assert isinstance(urls, list)
        assert len(urls) > 0
        
        for url_info in urls:
            assert "name" in url_info
            assert "url" in url_info
            assert "description" in url_info
            assert url_info["url"].startswith(("http://", "https://"))
            
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults"""
        config_manager = ConfigManager(self.config_file)
        
        # Modify config first
        config_manager.update_monitor_config(url="https://changed.com", interval_minutes=99)
        
        # Reset to defaults
        result = config_manager.reset_to_defaults()
        assert result is True
        
        config = config_manager.get_config()
        assert config["monitor"]["url"] == "https://www.reddit.com/r/CNC/"
        assert config["monitor"]["interval_minutes"] == 10
        
    def test_merge_config(self):
        """Test deep merge functionality"""
        config_manager = ConfigManager(self.config_file)
        
        base = {
            "a": {"x": 1, "y": 2},
            "b": 3
        }
        
        updates = {
            "a": {"y": 99, "z": 4},
            "c": 5
        }
        
        result = config_manager._merge_config(base, updates)
        
        assert result["a"]["x"] == 1  # preserved
        assert result["a"]["y"] == 99  # updated
        assert result["a"]["z"] == 4   # added
        assert result["b"] == 3        # preserved
        assert result["c"] == 5        # added
        
    @patch('builtins.open', side_effect=IOError("Test error"))
    def test_load_config_error_handling(self, mock_file):
        """Test error handling during config loading"""
        config_manager = ConfigManager(self.config_file)
        config = config_manager.get_config()
        
        # Should fall back to default config
        assert "monitor" in config
        assert config["monitor"]["url"] == "https://www.reddit.com/r/CNC/"
        
    @patch('builtins.open', side_effect=IOError("Test error"))
    def test_save_config_error_handling(self, mock_file):
        """Test error handling during config saving"""
        with patch('os.path.exists', return_value=False):
            config_manager = ConfigManager(self.config_file)
            result = config_manager.save_config()
            
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
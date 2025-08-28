import pytest
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_interface import app, WebMonitor, config_manager


class TestWebInterface:
    """Test cases for Web Interface"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up after each test method"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_index_page(self):
        """Test main index page loads"""
        response = self.client.get('/')
        
        assert response.status_code == 200
        assert b'Reddit\xe7\x9b\x91\xe6\x8e\xa7\xe7\xb3\xbb\xe7\xbb\x9f' in response.data  # "Reddit监控系统" in UTF-8
        
    def test_settings_page(self):
        """Test settings page loads"""
        response = self.client.get('/settings')
        
        assert response.status_code == 200
        assert b'\xe8\xae\xbe\xe7\xbd\xae' in response.data  # "设置" in UTF-8
        
    def test_api_status_not_running(self):
        """Test status API when not running"""
        response = self.client.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['running'] is False
        assert data['total_checks'] == 0
        
    def test_api_config_get(self):
        """Test getting configuration"""
        response = self.client.get('/api/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'config' in data
        assert 'predefined_urls' in data
        assert 'monitor' in data['config']
        
    def test_api_config_post_valid(self):
        """Test updating configuration with valid data"""
        valid_config = {
            "monitor": {
                "url": "https://test.com",
                "interval_minutes": 15,
                "data_directory": "test_data"
            }
        }
        
        response = self.client.post(
            '/api/config',
            data=json.dumps(valid_config),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('success') is True
        
    def test_api_config_post_invalid_url(self):
        """Test updating configuration with invalid URL"""
        invalid_config = {
            "monitor": {
                "url": "invalid-url",
                "interval_minutes": 10,
                "data_directory": "data"
            }
        }
        
        response = self.client.post(
            '/api/config',
            data=json.dumps(invalid_config),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'error' in data
        assert 'URL' in data['error']
        
    def test_api_config_post_invalid_interval(self):
        """Test updating configuration with invalid interval"""
        invalid_config = {
            "monitor": {
                "url": "https://test.com",
                "interval_minutes": 0,
                "data_directory": "data"
            }
        }
        
        response = self.client.post(
            '/api/config',
            data=json.dumps(invalid_config),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'error' in data
        assert '间隔' in data['error']
        
    def test_api_config_validate_valid(self):
        """Test configuration validation with valid data"""
        valid_config = {
            "monitor": {
                "url": "https://test.com",
                "interval_minutes": 10,
                "data_directory": "data"
            }
        }
        
        response = self.client.post(
            '/api/config/validate',
            data=json.dumps(valid_config),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('valid') is True
        
    @patch('os.path.exists')
    def test_api_logs_no_file(self, mock_exists):
        """Test logs API when log file doesn't exist"""
        mock_exists.return_value = False
        
        response = self.client.get('/api/logs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['logs'] == []
        
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_api_logs_with_file(self, mock_open, mock_exists):
        """Test logs API when log file exists"""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.readlines.return_value = ['line 1\n', 'line 2\n', 'line 3\n']
        mock_open.return_value.__enter__.return_value = mock_file
        
        response = self.client.get('/api/logs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['logs']) == 3
        assert data['logs'][0] == 'line 1'
        
    def test_api_data_no_files(self):
        """Test data API when no data files exist"""
        with patch('data_analyzer.DataAnalyzer') as mock_analyzer:
            mock_instance = mock_analyzer.return_value
            mock_instance.get_all_data_files.return_value = []
            
            response = self.client.get('/api/data')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'error' in data
            
    @patch('web_interface.is_monitoring', False)
    def test_api_start_monitoring(self):
        """Test starting monitoring"""
        with patch('web_interface.WebMonitor') as mock_monitor:
            with patch('threading.Thread') as mock_thread:
                response = self.client.post('/api/start')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data.get('success') is True
                
    def test_api_start_monitoring_already_running(self):
        """Test starting monitoring when already running"""
        with patch('web_interface.is_monitoring', True):
            response = self.client.post('/api/start')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'error' in data
            assert 'already running' in data['error']
            
    def test_api_stop_monitoring_not_running(self):
        """Test stopping monitoring when not running"""
        with patch('web_interface.is_monitoring', False):
            response = self.client.post('/api/stop')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'error' in data
            assert 'not running' in data['error']


class TestWebMonitor:
    """Test cases for WebMonitor class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = WebMonitor(
            url="https://httpbin.org/json",
            interval=1,  # Short interval for testing
            data_dir=self.temp_dir
        )
        
    def teardown_method(self):
        """Clean up after each test method"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_init(self):
        """Test WebMonitor initialization"""
        assert hasattr(self.monitor, 'status')
        assert self.monitor.status['running'] is False
        assert self.monitor.status['total_checks'] == 0
        assert self.monitor.status['changes_detected'] == 0
        assert self.monitor.status['errors'] == 0
        
    @patch.object(WebMonitor, 'fetch_website_data')
    @patch.object(WebMonitor, 'check_for_changes')
    @patch.object(WebMonitor, 'save_data')
    def test_monitor_once_with_status_success(self, mock_save, mock_check, mock_fetch):
        """Test single monitoring cycle with status tracking"""
        test_data = {"content": "test", "timestamp": "2023-01-01T00:00:00"}
        mock_fetch.return_value = test_data
        mock_check.return_value = True
        mock_save.return_value = "test_file.json"
        
        initial_checks = self.monitor.status['total_checks']
        initial_changes = self.monitor.status['changes_detected']
        
        self.monitor.monitor_once_with_status()
        
        assert self.monitor.status['total_checks'] == initial_checks + 1
        assert self.monitor.status['changes_detected'] == initial_changes + 1
        assert self.monitor.status['last_check'] is not None
        
    @patch.object(WebMonitor, 'fetch_website_data')
    def test_monitor_once_with_status_no_data(self, mock_fetch):
        """Test single monitoring cycle with no data"""
        mock_fetch.return_value = None
        
        initial_errors = self.monitor.status['errors']
        
        self.monitor.monitor_once_with_status()
        
        assert self.monitor.status['errors'] == initial_errors + 1
        
    @patch.object(WebMonitor, 'fetch_website_data')
    @patch.object(WebMonitor, 'check_for_changes')
    def test_monitor_once_with_status_no_changes(self, mock_check, mock_fetch):
        """Test single monitoring cycle with no changes"""
        test_data = {"content": "test"}
        mock_fetch.return_value = test_data
        mock_check.return_value = False
        
        initial_changes = self.monitor.status['changes_detected']
        
        self.monitor.monitor_once_with_status()
        
        assert self.monitor.status['changes_detected'] == initial_changes
        
    @patch.object(WebMonitor, 'monitor_once_with_status')
    def test_start_monitoring_thread(self, mock_monitor_once):
        """Test monitoring thread starts correctly"""
        with patch('web_interface.is_monitoring', True):
            with patch('time.sleep') as mock_sleep:
                # Mock the monitoring to stop after first iteration
                def side_effect():
                    import web_interface
                    web_interface.is_monitoring = False
                    
                mock_monitor_once.side_effect = side_effect
                
                self.monitor.start_monitoring_thread()
                
                mock_monitor_once.assert_called_once()
                assert self.monitor.status['running'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
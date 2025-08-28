import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
from reddit_monitor import RedditMonitor


class TestRedditMonitor:
    """Test cases for RedditMonitor class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_url = "https://httpbin.org/json"
        self.monitor = RedditMonitor(
            url=self.test_url,
            interval=5,  # Short interval for testing
            data_dir=self.temp_dir
        )
        
    def teardown_method(self):
        """Clean up after each test method"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_init(self):
        """Test monitor initialization"""
        assert self.monitor.url == self.test_url
        assert self.monitor.interval == 5
        assert self.monitor.data_dir == self.temp_dir
        assert os.path.exists(self.temp_dir)
        
    def test_ensure_data_directory(self):
        """Test data directory creation"""
        new_dir = os.path.join(self.temp_dir, "new_data")
        monitor = RedditMonitor(data_dir=new_dir)
        
        assert os.path.exists(new_dir)
        
    @patch('requests.get')
    def test_fetch_website_data_success(self, mock_get):
        """Test successful website data fetching"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"test": "data"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.monitor.fetch_website_data()
        
        assert result is not None
        assert result["status_code"] == 200
        assert result["content"] == '{"test": "data"}'
        assert "timestamp" in result
        assert "headers" in result
        
    @patch('requests.get')
    def test_fetch_website_data_http_error(self, mock_get):
        """Test handling of HTTP errors"""
        mock_get.side_effect = Exception("Connection error")
        
        result = self.monitor.fetch_website_data()
        
        assert result is None
        
    @patch('requests.get')
    def test_fetch_website_data_ssl_error(self, mock_get):
        """Test SSL error handling with fallback"""
        from requests.exceptions import SSLError
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"test": "data"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status.return_value = None
        
        # First call raises SSL error, second succeeds
        mock_get.side_effect = [SSLError("SSL Error"), mock_response]
        
        result = self.monitor.fetch_website_data()
        
        assert result is not None
        assert result["status_code"] == 200
        # Verify it tried twice (with and without SSL verification)
        assert mock_get.call_count == 2
        
    def test_save_data(self):
        """Test saving data to file"""
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "content": "test content",
            "status_code": 200
        }
        
        filename = self.monitor.save_data(test_data)
        
        assert filename is not None
        assert os.path.exists(filename)
        
        with open(filename, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            
        assert saved_data["content"] == "test content"
        assert saved_data["status_code"] == 200
        
    def test_save_data_none(self):
        """Test saving None data"""
        result = self.monitor.save_data(None)
        assert result is None
        
    def test_get_content_hash(self):
        """Test content hash generation"""
        content1 = "test content"
        content2 = "different content"
        content3 = "test content"  # Same as content1
        
        hash1 = self.monitor.get_content_hash(content1)
        hash2 = self.monitor.get_content_hash(content2)
        hash3 = self.monitor.get_content_hash(content3)
        
        assert hash1 != hash2
        assert hash1 == hash3
        assert self.monitor.get_content_hash(None) is None
        assert self.monitor.get_content_hash("") is not None
        
    def test_check_for_changes_first_run(self):
        """Test change detection on first run (no existing files)"""
        test_data = {"content": "test content"}
        
        has_changes = self.monitor.check_for_changes(test_data)
        
        assert has_changes is True  # First run should always return True
        
    def test_check_for_changes_with_existing_data(self):
        """Test change detection with existing data"""
        # Create initial data file
        initial_data = {"content": "initial content"}
        self.monitor.save_data(initial_data)
        
        # Test with same content
        same_data = {"content": "initial content"}
        has_changes = self.monitor.check_for_changes(same_data)
        assert has_changes is False
        
        # Test with different content
        different_data = {"content": "changed content"}
        has_changes = self.monitor.check_for_changes(different_data)
        assert has_changes is True
        
    def test_get_latest_data_file(self):
        """Test getting the latest data file"""
        # Initially no files
        latest = self.monitor.get_latest_data_file()
        assert latest is None
        
        # Create some test files
        test_data = {"content": "test"}
        self.monitor.save_data(test_data)
        
        import time
        time.sleep(0.1)  # Small delay to ensure different timestamps
        
        self.monitor.save_data(test_data)
        
        latest = self.monitor.get_latest_data_file()
        assert latest is not None
        assert os.path.exists(latest)
        
    @patch.object(RedditMonitor, 'fetch_website_data')
    @patch.object(RedditMonitor, 'check_for_changes')
    @patch.object(RedditMonitor, 'save_data')
    def test_monitor_once_success(self, mock_save, mock_check, mock_fetch):
        """Test single monitoring cycle with changes"""
        test_data = {"content": "test", "timestamp": datetime.now().isoformat()}
        mock_fetch.return_value = test_data
        mock_check.return_value = True
        mock_save.return_value = "test_file.json"
        
        self.monitor.monitor_once()
        
        mock_fetch.assert_called_once()
        mock_check.assert_called_once_with(test_data)
        mock_save.assert_called_once_with(test_data)
        
    @patch.object(RedditMonitor, 'fetch_website_data')
    def test_monitor_once_no_data(self, mock_fetch):
        """Test single monitoring cycle with no data"""
        mock_fetch.return_value = None
        
        self.monitor.monitor_once()
        
        mock_fetch.assert_called_once()
        
    @patch.object(RedditMonitor, 'fetch_website_data')
    @patch.object(RedditMonitor, 'check_for_changes')
    def test_monitor_once_no_changes(self, mock_check, mock_fetch):
        """Test single monitoring cycle with no changes"""
        test_data = {"content": "test"}
        mock_fetch.return_value = test_data
        mock_check.return_value = False
        
        self.monitor.monitor_once()
        
        mock_fetch.assert_called_once()
        mock_check.assert_called_once_with(test_data)
        
    @patch('os.listdir')
    def test_get_latest_data_file_error(self, mock_listdir):
        """Test error handling in get_latest_data_file"""
        mock_listdir.side_effect = OSError("Permission denied")
        
        result = self.monitor.get_latest_data_file()
        assert result is None
        
    @patch('builtins.open', side_effect=IOError("Write error"))
    def test_save_data_error(self, mock_file):
        """Test error handling during data saving"""
        test_data = {"content": "test"}
        
        result = self.monitor.save_data(test_data)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
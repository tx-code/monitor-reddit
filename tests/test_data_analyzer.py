import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, mock_open
from data_analyzer import DataAnalyzer


class TestDataAnalyzer:
    """Test cases for DataAnalyzer class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = DataAnalyzer(data_dir=self.temp_dir)
        
    def teardown_method(self):
        """Clean up after each test method"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def create_test_data_file(self, timestamp_str, content="test content", filename=None):
        """Helper method to create test data files"""
        if filename is None:
            timestamp_formatted = datetime.fromisoformat(timestamp_str).strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp_formatted}.json"
            
        filepath = os.path.join(self.temp_dir, filename)
        test_data = {
            "timestamp": timestamp_str,
            "content": content,
            "status_code": 200,
            "headers": {"Content-Type": "text/html"}
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
            
        return filepath
        
    def test_init(self):
        """Test DataAnalyzer initialization"""
        assert self.analyzer.data_dir == self.temp_dir
        
    def test_get_all_data_files_empty(self):
        """Test getting data files from empty directory"""
        files = self.analyzer.get_all_data_files()
        assert files == []
        
    def test_get_all_data_files_with_files(self):
        """Test getting data files with existing files"""
        # Create some test files
        self.create_test_data_file("2023-01-01T10:00:00", filename="data_20230101_100000.json")
        self.create_test_data_file("2023-01-01T11:00:00", filename="data_20230101_110000.json")
        self.create_test_data_file("2023-01-01T12:00:00", filename="data_20230101_120000.json")
        
        # Create a non-data file that should be ignored
        non_data_file = os.path.join(self.temp_dir, "other_file.txt")
        with open(non_data_file, 'w') as f:
            f.write("not a data file")
            
        files = self.analyzer.get_all_data_files()
        
        assert len(files) == 3
        assert all(f.endswith('.json') for f in files)
        assert all('data_' in os.path.basename(f) for f in files)
        # Files should be sorted
        assert files[0] < files[1] < files[2]
        
    @patch('os.listdir')
    def test_get_all_data_files_error(self, mock_listdir):
        """Test error handling when reading data directory"""
        mock_listdir.side_effect = OSError("Permission denied")
        
        files = self.analyzer.get_all_data_files()
        assert files == []
        
    def test_load_data_file_success(self):
        """Test loading data from file successfully"""
        test_content = "test content for loading"
        filepath = self.create_test_data_file("2023-01-01T10:00:00", content=test_content)
        
        data = self.analyzer.load_data_file(filepath)
        
        assert data is not None
        assert data["content"] == test_content
        assert data["timestamp"] == "2023-01-01T10:00:00"
        assert data["status_code"] == 200
        
    def test_load_data_file_not_found(self):
        """Test loading data from non-existent file"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")
        
        data = self.analyzer.load_data_file(nonexistent_file)
        assert data is None
        
    @patch('builtins.open', side_effect=IOError("Read error"))
    def test_load_data_file_error(self, mock_file):
        """Test error handling during file loading"""
        filepath = os.path.join(self.temp_dir, "test.json")
        
        data = self.analyzer.load_data_file(filepath)
        assert data is None
        
    def test_analyze_changes_no_files(self):
        """Test change analysis with no files"""
        with patch('builtins.print') as mock_print:
            self.analyzer.analyze_changes()
            mock_print.assert_called_with("Need at least 2 data files to analyze changes")
            
    def test_analyze_changes_one_file(self):
        """Test change analysis with only one file"""
        self.create_test_data_file("2023-01-01T10:00:00")
        
        with patch('builtins.print') as mock_print:
            self.analyzer.analyze_changes()
            mock_print.assert_called_with("Need at least 2 data files to analyze changes")
            
    def test_analyze_changes_with_changes(self):
        """Test change analysis with actual changes"""
        self.create_test_data_file("2023-01-01T10:00:00", content="content 1")
        self.create_test_data_file("2023-01-01T11:00:00", content="content 2")
        self.create_test_data_file("2023-01-01T12:00:00", content="content 3")
        
        with patch('builtins.print') as mock_print:
            self.analyzer.analyze_changes()
            
            # Should print total changes detected
            calls = [call.args[0] for call in mock_print.call_args_list]
            total_changes_call = next((call for call in calls if "Total changes detected:" in call), None)
            assert total_changes_call is not None
            assert "2" in total_changes_call  # Should detect 2 changes
            
    def test_analyze_changes_no_changes(self):
        """Test change analysis with no changes"""
        same_content = "same content"
        self.create_test_data_file("2023-01-01T10:00:00", content=same_content)
        self.create_test_data_file("2023-01-01T11:00:00", content=same_content)
        self.create_test_data_file("2023-01-01T12:00:00", content=same_content)
        
        with patch('builtins.print') as mock_print:
            self.analyzer.analyze_changes()
            
            calls = [call.args[0] for call in mock_print.call_args_list]
            total_changes_call = next((call for call in calls if "Total changes detected:" in call), None)
            assert total_changes_call is not None
            assert "0" in total_changes_call  # Should detect 0 changes
            
    def test_show_latest_data_no_files(self):
        """Test showing latest data with no files"""
        with patch('builtins.print') as mock_print:
            self.analyzer.show_latest_data()
            mock_print.assert_called_with("No data files found")
            
    def test_show_latest_data_with_files(self):
        """Test showing latest data with existing files"""
        self.create_test_data_file("2023-01-01T10:00:00", content="old content")
        self.create_test_data_file("2023-01-01T12:00:00", content="latest content")
        
        with patch('builtins.print') as mock_print:
            self.analyzer.show_latest_data()
            
            calls = [call.args[0] for call in mock_print.call_args_list]
            
            # Should show latest timestamp
            timestamp_call = next((call for call in calls if "Latest data from:" in call), None)
            assert timestamp_call is not None
            assert "2023-01-01T12:00:00" in timestamp_call
            
            # Should show content length
            content_call = next((call for call in calls if "Content length:" in call), None)
            assert content_call is not None
            assert "14" in content_call  # Length of "latest content"
            
    def test_generate_report_no_files(self):
        """Test generating report with no files"""
        with patch('builtins.print') as mock_print:
            self.analyzer.generate_report()
            
            calls = [call.args[0] for call in mock_print.call_args_list]
            
            # Should show report header
            header_call = next((call for call in calls if "Reddit Monitor Data Analysis Report" in call), None)
            assert header_call is not None
            
            # Should show no data files
            total_call = next((call for call in calls if "Total monitoring sessions:" in call), None)
            assert total_call is not None
            assert "0" in total_call
            
    def test_generate_report_with_files(self):
        """Test generating report with existing files"""
        self.create_test_data_file("2023-01-01T10:00:00", content="content 1")
        self.create_test_data_file("2023-01-01T11:00:00", content="content 2")
        self.create_test_data_file("2023-01-01T12:00:00", content="content 3")
        
        with patch('builtins.print') as mock_print:
            self.analyzer.generate_report()
            
            calls = [call.args[0] for call in mock_print.call_args_list]
            
            # Should show total files
            total_call = next((call for call in calls if "Total monitoring sessions:" in call), None)
            assert total_call is not None
            assert "3" in total_call
            
            # Should show monitoring period
            period_call = next((call for call in calls if "Monitoring period:" in call), None)
            assert period_call is not None
            assert "2023-01-01 10:00" in period_call
            assert "2023-01-01 12:00" in period_call
            
            # Should show duration
            duration_call = next((call for call in calls if "Total duration:" in call), None)
            assert duration_call is not None
            assert "2:00:00" in duration_call


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
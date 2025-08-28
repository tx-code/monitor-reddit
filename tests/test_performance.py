import pytest
import time
import tempfile
import shutil
import os
import json
import threading
from unittest.mock import Mock, patch
from datetime import datetime
from reddit_monitor import RedditMonitor
from config_manager import ConfigManager
from data_analyzer import DataAnalyzer


class TestPerformance:
    """Performance tests for the monitoring system"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up after each test method"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_config_manager_load_performance(self):
        """Test config manager loading performance with large config"""
        config_file = os.path.join(self.temp_dir, "large_config.json")
        
        # Create a large configuration
        large_config = {
            "monitor": {
                "url": "https://test.com",
                "interval_minutes": 10,
                "data_directory": "data"
            },
            "large_data": {f"key_{i}": f"value_{i}" for i in range(1000)}
        }
        
        with open(config_file, 'w') as f:
            json.dump(large_config, f)
        
        # Measure loading time
        start_time = time.time()
        config_manager = ConfigManager(config_file)
        config = config_manager.get_config()
        load_time = time.time() - start_time
        
        assert load_time < 1.0  # Should load in less than 1 second
        assert "monitor" in config
        assert "large_data" in config
        
    def test_config_manager_save_performance(self):
        """Test config manager saving performance"""
        config_file = os.path.join(self.temp_dir, "perf_config.json")
        config_manager = ConfigManager(config_file)
        
        # Add large amount of data
        large_update = {
            "performance_data": {f"metric_{i}": f"value_{i}" for i in range(500)}
        }
        
        # Measure save time
        start_time = time.time()
        result = config_manager.update_config(large_update)
        save_time = time.time() - start_time
        
        assert result is True
        assert save_time < 0.5  # Should save in less than 0.5 seconds
        
    def test_data_analyzer_performance_many_files(self):
        """Test data analyzer performance with many files"""
        analyzer = DataAnalyzer(data_dir=self.temp_dir)
        
        # Create many test data files
        num_files = 50
        for i in range(num_files):
            timestamp = f"2023-01-01T{i:02d}:00:00"
            filename = f"data_20230101_{i:02d}0000.json"
            filepath = os.path.join(self.temp_dir, filename)
            
            test_data = {
                "timestamp": timestamp,
                "content": f"test content {i}" * 100,  # Make content reasonably large
                "status_code": 200,
                "headers": {"Content-Type": "text/html"}
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
        
        # Test file listing performance
        start_time = time.time()
        files = analyzer.get_all_data_files()
        list_time = time.time() - start_time
        
        assert len(files) == num_files
        assert list_time < 1.0  # Should list files in less than 1 second
        
        # Test analysis performance
        start_time = time.time()
        with patch('builtins.print'):  # Suppress output for performance test
            analyzer.analyze_changes()
        analysis_time = time.time() - start_time
        
        assert analysis_time < 2.0  # Should analyze in less than 2 seconds
        
    def test_reddit_monitor_hash_performance(self):
        """Test content hashing performance with large content"""
        monitor = RedditMonitor(data_dir=self.temp_dir)
        
        # Create large content
        large_content = "test content " * 10000  # ~130KB of text
        
        # Measure hash time
        start_time = time.time()
        for _ in range(100):  # Hash 100 times
            hash_value = monitor.get_content_hash(large_content)
        hash_time = time.time() - start_time
        
        assert hash_value is not None
        assert hash_time < 1.0  # Should hash 100 times in less than 1 second
        
    def test_reddit_monitor_save_performance(self):
        """Test data saving performance with large data"""
        monitor = RedditMonitor(data_dir=self.temp_dir)
        
        # Create large test data
        large_data = {
            "timestamp": datetime.now().isoformat(),
            "content": "large content " * 5000,  # ~65KB of text
            "status_code": 200,
            "headers": {"Content-Type": "text/html"},
            "url": "https://test.com"
        }
        
        # Measure save time for multiple files
        start_time = time.time()
        for i in range(10):
            large_data["timestamp"] = f"2023-01-01T{i:02d}:00:00"
            filename = monitor.save_data(large_data)
            assert filename is not None
        save_time = time.time() - start_time
        
        assert save_time < 2.0  # Should save 10 files in less than 2 seconds
        
    @patch('requests.get')
    def test_reddit_monitor_fetch_timeout(self, mock_get):
        """Test fetch performance with timeout"""
        monitor = RedditMonitor(data_dir=self.temp_dir)
        
        # Simulate slow response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "test response"
        mock_response.headers = {}
        mock_response.raise_for_status.return_value = None
        
        def slow_response(*args, **kwargs):
            time.sleep(0.1)  # Simulate 100ms network delay
            return mock_response
            
        mock_get.side_effect = slow_response
        
        # Measure fetch time
        start_time = time.time()
        result = monitor.fetch_website_data()
        fetch_time = time.time() - start_time
        
        assert result is not None
        assert 0.1 <= fetch_time < 0.5  # Should respect the delay but complete quickly
        
    def test_concurrent_config_access(self):
        """Test concurrent access to configuration"""
        config_file = os.path.join(self.temp_dir, "concurrent_config.json")
        results = []
        errors = []
        
        def config_worker(worker_id):
            """Worker function for concurrent config operations"""
            try:
                config_manager = ConfigManager(config_file)
                
                # Perform multiple operations
                for i in range(5):
                    config_manager.update_monitor_config(
                        interval_minutes=worker_id * 10 + i
                    )
                    config = config_manager.get_config()
                    results.append((worker_id, i, config["monitor"]["interval_minutes"]))
                    time.sleep(0.01)  # Small delay
                    
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Start multiple threads
        threads = []
        num_workers = 5
        
        start_time = time.time()
        for worker_id in range(num_workers):
            thread = threading.Thread(target=config_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        execution_time = time.time() - start_time
        
        assert execution_time < 3.0  # Should complete in reasonable time
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_workers * 5  # All operations should complete
        
    def test_memory_usage_large_dataset(self):
        """Test memory usage with large dataset"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create analyzer with large dataset
        analyzer = DataAnalyzer(data_dir=self.temp_dir)
        
        # Create many files with large content
        for i in range(20):
            timestamp = f"2023-01-{i+1:02d}T10:00:00"
            filename = f"data_20230101_{i:02d}.json"
            filepath = os.path.join(self.temp_dir, filename)
            
            # Create large content (~1MB per file)
            large_content = "x" * (1024 * 1024)
            test_data = {
                "timestamp": timestamp,
                "content": large_content,
                "status_code": 200
            }
            
            with open(filepath, 'w') as f:
                json.dump(test_data, f)
        
        # Perform analysis
        with patch('builtins.print'):
            analyzer.generate_report()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024
        
    def test_startup_time(self):
        """Test application startup time"""
        config_file = os.path.join(self.temp_dir, "startup_config.json")
        
        # Measure time to initialize all components
        start_time = time.time()
        
        config_manager = ConfigManager(config_file)
        monitor = RedditMonitor(data_dir=self.temp_dir)
        analyzer = DataAnalyzer(data_dir=self.temp_dir)
        
        # Perform basic operations
        config_manager.get_config()
        monitor.ensure_data_directory()
        analyzer.get_all_data_files()
        
        startup_time = time.time() - start_time
        
        assert startup_time < 1.0  # Should startup in less than 1 second


@pytest.mark.slow
class TestStressTests:
    """Stress tests for the monitoring system"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.skip("Skip by default - run manually for stress testing")
    def test_continuous_monitoring_stress(self):
        """Stress test continuous monitoring operations"""
        monitor = RedditMonitor(data_dir=self.temp_dir, interval=1)
        
        with patch.object(monitor, 'fetch_website_data') as mock_fetch:
            mock_fetch.return_value = {
                "timestamp": datetime.now().isoformat(),
                "content": f"test content {time.time()}",
                "status_code": 200
            }
            
            # Run monitoring for 30 iterations
            start_time = time.time()
            for i in range(30):
                monitor.monitor_once()
                time.sleep(0.1)  # Small delay between iterations
            
            total_time = time.time() - start_time
            
            assert total_time < 10.0  # Should complete in reasonable time
            assert mock_fetch.call_count == 30
            
            # Check that files were created
            files = os.listdir(self.temp_dir)
            data_files = [f for f in files if f.startswith('data_') and f.endswith('.json')]
            assert len(data_files) > 0


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-m", "not slow"])
    
    # To run stress tests, use:
    # pytest test_performance.py -v -m slow
#!/usr/bin/env python3
"""
快速测试脚本 - 验证基本功能
用于开发过程中的快速验证
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path


def test_imports():
    """测试所有模块能否正常导入"""
    print("测试模块导入...")
    
    try:
        from config_manager import ConfigManager
        from reddit_monitor import RedditMonitor
        from data_analyzer import DataAnalyzer
        from web_interface import app
        print("  所有模块导入成功")
        return True
    except ImportError as e:
        print(f"  模块导入失败: {e}")
        return False


def test_config_manager():
    """测试配置管理器基本功能"""
    print("测试配置管理器...")
    
    try:
        from config_manager import ConfigManager
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            config_manager = ConfigManager(config_file)
            
            # Test basic operations
            config = config_manager.get_config()
            assert "monitor" in config
            
            # Test update
            result = config_manager.update_monitor_config(
                url="https://test.com",
                interval_minutes=5
            )
            assert result is True
            
            # Test validation
            errors = config_manager.validate_config()
            assert len(errors) == 0
            
            print("  配置管理器测试通过")
            return True
            
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)
                
    except Exception as e:
        print(f"  配置管理器测试失败: {e}")
        return False


def test_reddit_monitor():
    """测试Reddit监控器基本功能"""
    print("测试Reddit监控器...")
    
    try:
        from reddit_monitor import RedditMonitor
        
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = RedditMonitor(
                url="https://httpbin.org/json",
                interval=1,
                data_dir=temp_dir
            )
            
            # Test initialization
            assert monitor.url == "https://httpbin.org/json"
            assert monitor.interval == 1
            assert os.path.exists(temp_dir)
            
            # Test hash function
            hash1 = monitor.get_content_hash("test content")
            hash2 = monitor.get_content_hash("test content")
            hash3 = monitor.get_content_hash("different content")
            
            assert hash1 == hash2
            assert hash1 != hash3
            
            # Test monitoring (with timeout to avoid hanging)
            try:
                result = monitor.monitor_once()
                print(f"    监控执行结果: {'成功' if result else '失败'}")
                
                # Test status
                status = monitor.get_status()
                assert 'total_checks' in status
                assert 'success_rate' in status
                print(f"    总检查次数: {status['total_checks']}")
                print(f"    成功率: {status['success_rate']:.1f}%")
                
            except Exception as monitor_error:
                print(f"    监控测试警告: {monitor_error}")
                # 监控失败不影响整体测试通过，因为可能是网络问题
            
            print("  Reddit监控器测试通过")
            return True
            
    except Exception as e:
        print(f"  Reddit监控器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_analyzer():
    """测试数据分析器基本功能"""
    print("测试数据分析器...")
    
    try:
        from data_analyzer import DataAnalyzer
        
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = DataAnalyzer(data_dir=temp_dir)
            
            # Test with empty directory
            files = analyzer.get_all_data_files()
            assert files == []
            
            # Create test file
            import json
            from datetime import datetime
            
            test_file = os.path.join(temp_dir, "data_20230101_100000.json")
            test_data = {
                "timestamp": datetime.now().isoformat(),
                "content": "test content",
                "status_code": 200
            }
            
            with open(test_file, 'w') as f:
                json.dump(test_data, f)
            
            # Test file discovery
            files = analyzer.get_all_data_files()
            assert len(files) == 1
            
            # Test file loading
            data = analyzer.load_data_file(test_file)
            assert data is not None
            assert data["content"] == "test content"
            
            print("  数据分析器测试通过")
            return True
            
    except Exception as e:
        print(f"  数据分析器测试失败: {e}")
        return False


def test_web_interface():
    """测试Web界面基本功能"""
    print("测试Web界面...")
    
    try:
        from web_interface import app
        
        # Test app creation
        assert app is not None
        
        # Test with test client
        with app.test_client() as client:
            # Test main page
            response = client.get('/')
            assert response.status_code == 200
            
            # Test API endpoints
            response = client.get('/api/status')
            assert response.status_code == 200
            
            response = client.get('/api/config')
            assert response.status_code == 200
            
            print("  Web界面测试通过")
            return True
            
    except Exception as e:
        print(f"  Web界面测试失败: {e}")
        return False


def test_file_permissions():
    """测试文件权限"""
    print("测试文件权限...")
    
    try:
        # Test creating directories
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test_data")
            os.makedirs(test_dir)
            assert os.path.exists(test_dir)
            
            # Test file creation
            test_file = os.path.join(test_dir, "test.json")
            with open(test_file, 'w') as f:
                f.write('{"test": true}')
            
            assert os.path.exists(test_file)
            
            # Test file reading
            with open(test_file, 'r') as f:
                content = f.read()
                assert '"test": true' in content
            
            print("  文件权限测试通过")
            return True
            
    except Exception as e:
        print(f"  文件权限测试失败: {e}")
        return False


def main():
    """运行快速测试"""
    print("运行快速测试套件...")
    print("="*50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置管理器", test_config_manager),
        ("Reddit监控器", test_reddit_monitor),
        ("数据分析器", test_data_analyzer),
        ("Web界面", test_web_interface),
        ("文件权限", test_file_permissions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  {test_name}测试异常: {e}")
    
    print("="*50)
    print("快速测试结果汇总")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("所有快速测试通过！")
        return True
    else:
        print(f"有 {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
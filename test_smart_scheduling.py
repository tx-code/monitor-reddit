#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能调度和时间恢复功能
"""

import time
import os
import sys
from datetime import datetime, timedelta
from config_manager import ConfigManager
from reddit_monitor import RedditMonitor

# 设置输出编码
if sys.platform == "win32":
    import locale
    import codecs
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout.detach())

def test_smart_scheduling():
    """测试智能调度功能"""
    print("测试智能调度功能...")
    
    # 使用临时配置文件
    config_file = "test_smart_config.json"
    try:
        # 清理之前的测试文件
        if os.path.exists(config_file):
            os.remove(config_file)
        
        # 创建配置管理器
        config_manager = ConfigManager(config_file)
        
        print("\n1. 测试首次运行...")
        # 首次运行应该立即检查
        should_check = config_manager.should_check_now()
        print(f"  首次运行是否应该检查: {should_check}")
        assert should_check == True, "首次运行应该立即检查"
        
        print("\n2. 测试检查时间更新...")
        # 模拟成功检查
        config_manager.update_check_time(success=True)
        
        # 检查时间是否正确更新
        last_check = config_manager.get_last_check_time()
        next_check = config_manager.get_next_scheduled_check()
        
        print(f"  最后检查时间: {last_check}")
        print(f"  下次检查时间: {next_check}")
        
        assert last_check is not None, "最后检查时间应该被设置"
        assert next_check is not None, "下次检查时间应该被设置"
        
        print("\n3. 测试调度逻辑...")
        # 刚刚检查完，现在不应该再检查
        should_check = config_manager.should_check_now()
        print(f"  刚检查完是否应该再检查: {should_check}")
        assert should_check == False, "刚检查完不应该立即再检查"
        
        # 检查等待时间
        wait_time = config_manager.get_time_until_next_check()
        print(f"  距离下次检查还有: {wait_time} 秒")
        assert wait_time > 0, "应该有等待时间"
        
        print("\n4. 测试统计信息...")
        stats = config_manager.get_session_stats()
        print(f"  总检查次数: {stats['total_checks']}")
        print(f"  成功率: {stats['success_rate']:.1f}%")
        
        assert stats['total_checks'] == 1, "应该有1次检查"
        assert stats['success_rate'] == 100.0, "成功率应该是100%"
        
        print("\n5. 测试失败统计...")
        # 模拟失败检查
        config_manager.update_check_time(success=False)
        stats = config_manager.get_session_stats()
        
        print(f"  总检查次数: {stats['total_checks']}")
        print(f"  失败次数: {stats['failed_checks']}")
        print(f"  成功率: {stats['success_rate']:.1f}%")
        
        assert stats['total_checks'] == 2, "应该有2次检查"
        assert stats['failed_checks'] == 1, "应该有1次失败"
        assert stats['success_rate'] == 50.0, "成功率应该是50%"
        
        print("\n6. 测试会话管理...")
        config_manager.start_session()
        session_stats = config_manager.get_session_stats()
        print(f"  会话开始时间: {session_stats['session_start']}")
        
        # 等待一小段时间
        time.sleep(1)
        
        config_manager.end_session()
        session_stats = config_manager.get_session_stats()
        print(f"  会话检查次数: {session_stats['session_checks']}")
        
        print("\nOK: 智能调度功能测试通过！")
        return True
        
    except Exception as e:
        print(f"ERROR: 测试失败: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(config_file):
            os.remove(config_file)

def test_monitor_integration():
    """测试监控器集成"""
    print("\n测试监控器集成...")
    
    config_file = "test_monitor_config.json"
    try:
        # 清理之前的测试文件
        if os.path.exists(config_file):
            os.remove(config_file)
        
        # 创建配置管理器
        config_manager = ConfigManager(config_file)
        
        # 设置短的检查间隔用于测试
        config_manager.update_monitor_config(
            url="https://www.reddit.com/r/CNC/",
            interval_minutes=1  # 1分钟间隔
        )
        
        # 创建监控器
        monitor = RedditMonitor(config_manager=config_manager)
        
        print(f"  监控器URL: {monitor.url}")
        print(f"  检查间隔: {monitor.interval} 秒")
        
        # 测试单次监控
        print("\n  执行单次监控...")
        success = monitor.monitor_once()
        print(f"  监控结果: {'成功' if success else '失败'}")
        
        # 检查状态
        status = monitor.get_status()
        print(f"  总检查次数: {status['total_checks']}")
        print(f"  成功率: {status['success_rate']:.1f}%")
        print(f"  距离下次检查: {status['time_until_next']} 秒")
        
        assert status['total_checks'] >= 1, "应该至少有1次检查"
        
        print("\nOK: 监控器集成测试通过！")
        return True
        
    except Exception as e:
        print(f"ERROR: 集成测试失败: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(config_file):
            os.remove(config_file)

def main():
    """主测试函数"""
    print("智能调度和时间恢复功能测试")
    print("=" * 50)
    
    tests = [
        ("智能调度功能", test_smart_scheduling),
        ("监控器集成", test_monitor_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}测试:")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"ERROR: {test_name}测试异常: {e}")
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("OK: 所有测试通过！智能调度功能可以正常使用")
        return True
    else:
        print(f"WARN: 有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    import sys
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
#!/usr/bin/env python3
"""
Reddit监控系统 - 测试运行脚本
运行各种类型的测试并生成报告
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tests_dir = self.project_root / "tests"
        
    def install_dependencies(self):
        """安装测试依赖"""
        print("📦 安装测试依赖...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True, cwd=self.project_root)
            
            # Install additional test dependencies
            test_deps = ["psutil"]  # For performance tests
            for dep in test_deps:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], check=True)
                
            print("✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            return False
    
    def run_unit_tests(self, verbose=False, coverage=False):
        """运行单元测试"""
        print("\n🧪 运行单元测试...")
        
        cmd = [sys.executable, "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
            
        if coverage:
            cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
            
        cmd.extend([
            "tests/test_config_manager.py",
            "tests/test_reddit_monitor.py",
            "tests/test_data_analyzer.py",
            "tests/test_web_interface.py"
        ])
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            success = result.returncode == 0
            
            if success:
                print("✅ 单元测试通过")
            else:
                print("❌ 单元测试失败")
                
            return success
        except Exception as e:
            print(f"❌ 运行单元测试时出错: {e}")
            return False
    
    def run_performance_tests(self, verbose=False):
        """运行性能测试"""
        print("\n⚡ 运行性能测试...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_performance.py",
            "-m", "not slow"
        ]
        
        if verbose:
            cmd.append("-v")
            
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            success = result.returncode == 0
            
            if success:
                print("✅ 性能测试通过")
            else:
                print("❌ 性能测试失败")
                
            return success
        except Exception as e:
            print(f"❌ 运行性能测试时出错: {e}")
            return False
    
    def run_stress_tests(self, verbose=False):
        """运行压力测试"""
        print("\n💪 运行压力测试...")
        print("⚠️  警告: 压力测试可能需要较长时间")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_performance.py",
            "-m", "slow", "-s"
        ]
        
        if verbose:
            cmd.append("-v")
            
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            success = result.returncode == 0
            
            if success:
                print("✅ 压力测试通过")
            else:
                print("❌ 压力测试失败")
                
            return success
        except Exception as e:
            print(f"❌ 运行压力测试时出错: {e}")
            return False
    
    def run_integration_tests(self, verbose=False):
        """运行集成测试"""
        print("\n🔧 运行集成测试...")
        
        # Test basic functionality integration
        print("  📋 测试基本功能集成...")
        
        try:
            # Test config manager integration
            from config_manager import ConfigManager
            config_manager = ConfigManager("test_config.json")
            assert config_manager.get_config() is not None
            
            # Test monitor integration  
            from reddit_monitor import RedditMonitor
            monitor = RedditMonitor(url="https://httpbin.org/json", data_dir="test_data")
            assert monitor.data_dir == "test_data"
            
            # Test analyzer integration
            from data_analyzer import DataAnalyzer
            analyzer = DataAnalyzer("test_data")
            files = analyzer.get_all_data_files()
            assert isinstance(files, list)
            
            # Clean up
            import shutil
            if os.path.exists("test_config.json"):
                os.remove("test_config.json")
            if os.path.exists("test_data"):
                shutil.rmtree("test_data")
                
            print("✅ 集成测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 集成测试失败: {e}")
            return False
    
    def run_linting(self):
        """运行代码检查"""
        print("\n📝 运行代码检查...")
        
        # Check if flake8 is available
        try:
            subprocess.run([sys.executable, "-m", "flake8", "--version"], 
                         capture_output=True, check=True)
        except subprocess.CalledProcessError:
            print("⚠️  flake8 未安装，跳过代码检查")
            return True
            
        cmd = [
            sys.executable, "-m", "flake8",
            "--max-line-length=100",
            "--ignore=E203,W503",
            "*.py", "tests/"
        ]
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 代码检查通过")
                return True
            else:
                print("❌ 代码检查发现问题:")
                print(result.stdout)
                return False
                
        except Exception as e:
            print(f"❌ 运行代码检查时出错: {e}")
            return False
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n📊 生成测试报告...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "--html=test_report.html",
            "--self-contained-html",
            "tests/"
        ]
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            
            if result.returncode == 0:
                report_path = self.project_root / "test_report.html"
                print(f"✅ 测试报告已生成: {report_path}")
                return True
            else:
                print("❌ 生成测试报告失败")
                return False
                
        except Exception as e:
            print(f"❌ 生成测试报告时出错: {e}")
            return False
    
    def run_all_tests(self, verbose=False, coverage=False, skip_stress=False):
        """运行所有测试"""
        print("🚀 开始运行完整测试套件...")
        start_time = time.time()
        
        results = {
            "dependencies": self.install_dependencies(),
            "unit_tests": self.run_unit_tests(verbose, coverage),
            "integration_tests": self.run_integration_tests(verbose),
            "performance_tests": self.run_performance_tests(verbose),
            "linting": self.run_linting()
        }
        
        if not skip_stress:
            results["stress_tests"] = self.run_stress_tests(verbose)
        
        # Generate report
        self.generate_test_report()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Print summary
        print("\n" + "="*50)
        print("📋 测试结果汇总")
        print("="*50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name:<20}: {status}")
        
        print(f"\n总计: {passed}/{total} 测试通过")
        print(f"耗时: {total_time:.2f} 秒")
        
        if passed == total:
            print("\n🎉 所有测试通过！")
            return True
        else:
            print(f"\n⚠️  有 {total - passed} 个测试失败")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Reddit监控系统测试运行器")
    parser.add_argument("--type", "-t", 
                       choices=["all", "unit", "integration", "performance", "stress", "lint"],
                       default="all",
                       help="要运行的测试类型")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出")
    parser.add_argument("--coverage", "-c", action="store_true",
                       help="生成覆盖率报告")
    parser.add_argument("--skip-stress", action="store_true",
                       help="跳过压力测试")
    parser.add_argument("--install-deps", action="store_true",
                       help="仅安装依赖")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.install_deps:
        return runner.install_dependencies()
    
    success = True
    
    if args.type == "all":
        success = runner.run_all_tests(args.verbose, args.coverage, args.skip_stress)
    elif args.type == "unit":
        success = runner.run_unit_tests(args.verbose, args.coverage)
    elif args.type == "integration":
        success = runner.run_integration_tests(args.verbose)
    elif args.type == "performance":
        success = runner.run_performance_tests(args.verbose)
    elif args.type == "stress":
        success = runner.run_stress_tests(args.verbose)
    elif args.type == "lint":
        success = runner.run_linting()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
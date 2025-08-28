#!/usr/bin/env python3
"""
Reddit监控系统 - 完整验证脚本
验证uv环境、依赖、功能和打包是否都能正常工作
"""

import subprocess
import sys
from pathlib import Path

def check_step(name, func):
    """执行验证步骤"""
    print(f"检查 {name}...")
    try:
        result = func()
        if result:
            print(f"  OK: {name} 正常")
            return True
        else:
            print(f"  ERROR: {name} 失败")
            return False
    except Exception as e:
        print(f"  ERROR: {name} 错误: {e}")
        return False

def check_uv():
    """检查uv安装"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_dependencies():
    """检查依赖同步"""
    try:
        result = subprocess.run(['uv', 'sync', '--dev'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def check_main_import():
    """检查主模块导入"""
    try:
        result = subprocess.run(['uv', 'run', 'python', '-c', 'import main; print("OK")'], 
                              capture_output=True, text=True)
        return result.returncode == 0 and "OK" in result.stdout
    except Exception:
        return False

def check_quick_test():
    """检查快速测试"""
    try:
        result = subprocess.run(['uv', 'run', 'python', 'test_quick.py'], 
                              capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception:
        return False

def check_pytest():
    """检查pytest运行"""
    try:
        result = subprocess.run(['uv', 'run', 'pytest', '--version'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def check_build_script():
    """检查打包脚本"""
    try:
        result = subprocess.run(['uv', 'run', 'python', 'build_exe.py', '--help'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def check_files_structure():
    """检查文件结构"""
    project_root = Path(__file__).parent
    required_files = [
        'main.py',
        'run.py', 
        'build_exe.py',
        'pyproject.toml',
        'README.md',
        'uv-setup.md'
    ]
    
    for file_name in required_files:
        if not (project_root / file_name).exists():
            return False
    return True

def main():
    """主验证函数"""
    print("Reddit监控系统 - 完整验证")
    print("=" * 50)
    
    steps = [
        ("文件结构", check_files_structure),
        ("uv安装", check_uv),
        ("依赖同步", check_dependencies),
        ("主模块导入", check_main_import), 
        ("快速测试", check_quick_test),
        ("pytest工具", check_pytest),
        ("打包脚本", check_build_script),
    ]
    
    passed = 0
    total = len(steps)
    
    for step_name, step_func in steps:
        if check_step(step_name, step_func):
            passed += 1
            
    print("\n" + "=" * 50)
    print("验证结果汇总")
    print("=" * 50)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("OK: 所有验证通过！系统已准备就绪")
        print("\n快速命令:")
        print("  uv run python main.py        # 运行主程序")
        print("  uv run python run.py         # 便捷启动")
        print("  uv run pytest                # 运行测试")
        print("  uv run python build_exe.py   # 打包exe")
        return True
    else:
        print(f"ERROR: 有 {total - passed} 个验证失败")
        print("\n请检查:")
        print("1. uv是否正确安装")
        print("2. 项目依赖是否正确同步")
        print("3. 所有必需文件是否存在")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Reddit监控系统 - 统一启动入口
使用uv环境运行程序
"""

import subprocess
import sys
from pathlib import Path

def check_uv():
    """检查uv是否安装"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def main():
    """主函数"""
    if not check_uv():
        print("ERROR: uv未安装")
        print("\n安装uv:")
        print("  Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        print("  Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)
    
    # 确保依赖已同步
    print("同步项目依赖...")
    try:
        subprocess.run(['uv', 'sync', '--dev'], check=True)
        print("依赖同步完成")
    except subprocess.CalledProcessError:
        print("WARN: 依赖同步失败，尝试继续运行")
    
    # 运行主程序
    print("启动Reddit监控系统...")
    try:
        subprocess.run(['uv', 'run', 'python', 'main.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: 程序运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
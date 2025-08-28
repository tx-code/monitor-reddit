#!/usr/bin/env python3
"""
Reddit监控系统 - Web界面启动脚本
使用方法: python start_web.py
"""

import os
import sys
import webbrowser
import time
from threading import Timer
from web_interface import app

def open_browser():
    """延迟打开浏览器"""
    time.sleep(1.5)  # 等待服务器启动
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("=" * 50)
    print("Reddit监控系统 Web界面")
    print("=" * 50)
    print(f"工作目录: {os.getcwd()}")
    print("Web服务器启动中...")
    print("界面地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 自动打开浏览器
    Timer(1, open_browser).start()
    
    try:
        # 启动Flask应用
        app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0)
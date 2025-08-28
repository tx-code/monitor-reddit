#!/usr/bin/env python3
"""
打包测试脚本 - 验证打包前的准备工作
"""

import os
import sys
import importlib
from pathlib import Path


def test_main_module():
    """测试主模块是否可以导入"""
    print("🔍 测试主模块导入...")
    
    try:
        # 测试导入所有必需模块
        modules_to_test = [
            'main',
            'config_manager', 
            'reddit_monitor',
            'web_interface',
            'data_analyzer'
        ]
        
        for module_name in modules_to_test:
            try:
                importlib.import_module(module_name)
                print(f"  ✅ {module_name}")
            except ImportError as e:
                print(f"  ❌ {module_name}: {e}")
                return False
                
        print("  ✅ 所有主模块导入成功")
        return True
        
    except Exception as e:
        print(f"  ❌ 模块测试失败: {e}")
        return False


def test_dependencies():
    """测试依赖库"""
    print("📦 测试依赖库...")
    
    dependencies = [
        ('requests', 'HTTP请求库'),
        ('flask', 'Web框架'),
        ('tkinter', 'GUI库（系统自带）'),
        ('json', 'JSON处理（系统自带）'),
        ('threading', '多线程（系统自带）'),
        ('webbrowser', '浏览器控制（系统自带）'),
    ]
    
    optional_deps = [
        ('pyinstaller', 'PyInstaller打包工具'),
        ('PIL', 'PIL图像处理库'),
        ('pytest', 'pytest测试框架'),
    ]
    
    # 测试必需依赖
    for module_name, description in dependencies:
        try:
            importlib.import_module(module_name)
            print(f"  ✅ {module_name} - {description}")
        except ImportError:
            print(f"  ❌ {module_name} - {description} (必需)")
            return False
    
    # 测试可选依赖
    for module_name, description in optional_deps:
        try:
            importlib.import_module(module_name)
            print(f"  ✅ {module_name} - {description}")
        except ImportError:
            print(f"  ⚠️  {module_name} - {description} (可选)")
    
    return True


def test_files_structure():
    """测试文件结构"""
    print("📁 测试文件结构...")
    
    required_files = [
        'main.py',
        'config_manager.py',
        'reddit_monitor.py', 
        'web_interface.py',
        'data_analyzer.py',
        'reddit_monitor.spec',
        'build_exe.py',
        'version_info.txt',
        'requirements.txt',
    ]
    
    required_dirs = [
        'templates',
        'tests',
    ]
    
    project_root = Path(__file__).parent
    
    # 检查必需文件
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} (缺失)")
            return False
    
    # 检查必需目录
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ (缺失)")
            return False
            
    return True


def test_gui_components():
    """测试GUI组件"""
    print("🖥️  测试GUI组件...")
    
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext, filedialog
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        # 测试各个组件
        components = [
            ('Label', lambda: ttk.Label(root, text="test")),
            ('Button', lambda: ttk.Button(root, text="test")),
            ('Entry', lambda: ttk.Entry(root)),
            ('Listbox', lambda: tk.Listbox(root)),
            ('ScrolledText', lambda: scrolledtext.ScrolledText(root)),
            ('Notebook', lambda: ttk.Notebook(root)),
        ]
        
        for comp_name, comp_func in components:
            try:
                widget = comp_func()
                widget.destroy()
                print(f"  ✅ {comp_name}")
            except Exception as e:
                print(f"  ❌ {comp_name}: {e}")
                return False
        
        root.destroy()
        print("  ✅ GUI组件测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ GUI测试失败: {e}")
        return False


def test_web_components():
    """测试Web组件"""
    print("🌐 测试Web组件...")
    
    try:
        from flask import Flask
        from web_interface import app
        
        # 测试Flask应用创建
        if app is None:
            print("  ❌ Flask应用创建失败")
            return False
            
        # 测试客户端
        with app.test_client() as client:
            response = client.get('/api/status')
            if response.status_code == 200:
                print("  ✅ API端点正常")
            else:
                print(f"  ⚠️  API响应异常: {response.status_code}")
        
        print("  ✅ Web组件测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ Web组件测试失败: {e}")
        return False


def test_config_system():
    """测试配置系统"""
    print("⚙️  测试配置系统...")
    
    try:
        from config_manager import ConfigManager
        
        # 创建临时配置管理器
        config_manager = ConfigManager("test_config.json")
        
        # 测试基本操作
        config = config_manager.get_config()
        if not config or 'monitor' not in config:
            print("  ❌ 配置加载失败")
            return False
            
        # 测试配置更新
        success = config_manager.update_monitor_config(
            url="https://test.com",
            interval_minutes=5
        )
        
        if not success:
            print("  ❌ 配置更新失败")
            return False
            
        # 测试验证
        errors = config_manager.validate_config()
        if errors:
            print(f"  ⚠️  配置验证警告: {errors}")
        
        # 清理测试文件
        if os.path.exists("test_config.json"):
            os.remove("test_config.json")
            
        print("  ✅ 配置系统测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 配置系统测试失败: {e}")
        return False


def show_packaging_instructions():
    """显示打包说明"""
    print("\n" + "=" * 60)
    print("📦 打包说明")
    print("=" * 60)
    
    instructions = """
🚀 自动打包（推荐）:
   python build_exe.py --install-deps    # 安装依赖
   python build_exe.py                   # 执行打包

🛠️  手动打包:
   pip install pyinstaller pillow        # 安装依赖
   pyinstaller reddit_monitor.spec       # 执行打包

📁 输出位置:
   dist/RedditMonitor.exe                # 打包后的exe文件
   release/                              # 发布包目录

💡 使用提示:
   1. 确保所有测试都通过
   2. 在干净的Python环境中打包
   3. 打包后在无Python环境的机器上测试
   4. 检查exe文件大小（通常30-50MB）

🐛 常见问题:
   - 如果打包失败，检查hiddenimports配置
   - 如果exe太大，检查excludes配置  
   - 如果运行时找不到模块，添加到hiddenimports
   - 如果找不到模板文件，检查datas配置

📖 详细文档: BUILD_README.md
"""
    
    print(instructions)


def main():
    """主测试函数"""
    print("🧪 Reddit监控系统 - 打包前测试")
    print("=" * 60)
    
    tests = [
        ("文件结构", test_files_structure),
        ("依赖库", test_dependencies),
        ("主模块", test_main_module), 
        ("GUI组件", test_gui_components),
        ("Web组件", test_web_components),
        ("配置系统", test_config_system),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}测试:")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ {test_name}测试异常: {e}")
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！系统已准备好打包")
        show_packaging_instructions()
        return True
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，请修复后再打包")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⛔ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
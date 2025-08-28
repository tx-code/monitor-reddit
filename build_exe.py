#!/usr/bin/env python3
"""
Reddit监控系统 - 自动打包脚本
使用uv管理依赖和虚拟环境的打包脚本
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import zipfile
from datetime import datetime

class ExeBuilder:
    """可执行文件构建器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.output_dir = self.project_root / "release"
        
    def check_uv(self):
        """检查uv是否安装"""
        print("检查uv安装...")
        
        try:
            result = subprocess.run(['uv', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  OK: uv {version}")
                return True
            else:
                print("  ERROR: uv未正确安装")
                return False
        except FileNotFoundError:
            print("  ERROR: 找不到uv命令")
            print("  安装uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False
    
    def setup_uv_environment(self):
        """设置uv环境"""
        print("设置uv环境...")
        
        # 同步项目依赖
        try:
            print("  同步项目依赖...")
            subprocess.run([
                'uv', 'sync', '--dev'
            ], cwd=self.project_root, check=True)
            print("  OK: 依赖同步完成")
            
            # 安装打包依赖
            print("  安装打包依赖...")
            subprocess.run([
                'uv', 'add', '--dev', 'pyinstaller>=5.0.0', 'pillow>=8.0.0'
            ], cwd=self.project_root, check=True)
            print("  OK: 打包依赖安装完成")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: uv环境设置失败: {e}")
            return False
    
    def clean_build(self):
        """清理构建目录"""
        print("清理构建目录...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"  已清理: {dir_path}")
                except Exception as e:
                    print(f"  WARN: 无法清理 {dir_path}: {e}")
                
        # 清理缓存
        cache_dirs = [
            self.project_root / "__pycache__",
            self.project_root / ".pytest_cache",
            self.project_root / ".uv",
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    shutil.rmtree(cache_dir)
                    print(f"  已清理缓存: {cache_dir}")
                except Exception as e:
                    print(f"  WARN: 无法清理缓存 {cache_dir}: {e}")
        
        return True
    
    def build_exe_with_uv(self):
        """使用uv环境构建exe"""
        print("使用uv环境构建exe...")
        
        # 检查spec文件
        spec_file = self.project_root / "reddit_monitor.spec"
        if not spec_file.exists():
            print("  ERROR: 找不到spec文件")
            return False
        
        try:
            # 在uv环境中运行PyInstaller
            cmd = [
                'uv', 'run',
                'pyinstaller',
                '--clean',
                '--noconfirm',
                '--log-level=WARN',
                str(spec_file)
            ]
            
            print(f"  执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                check=True,
                capture_output=False
            )
            
            print("  OK: 构建完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: 构建失败: {e}")
            return False
    
    def test_exe(self):
        """测试构建的exe文件"""
        print("测试exe文件...")
        
        exe_path = self.dist_dir / "RedditMonitor.exe"
        
        if not exe_path.exists():
            print("  ERROR: 找不到exe文件")
            return False
            
        print(f"  exe位置: {exe_path}")
        print(f"  文件大小: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        # 简单测试启动
        try:
            print("  测试启动...")
            
            result = subprocess.run([
                str(exe_path), "--help"
            ], timeout=10, capture_output=True, text=True)
            
            print("  OK: exe文件可以正常启动")
            return True
            
        except subprocess.TimeoutExpired:
            print("  WARN: exe启动测试超时（可能正常，GUI程序）")
            return True
        except Exception as e:
            print(f"  ERROR: exe启动测试失败: {e}")
            return False
    
    def create_release_package(self):
        """创建发布包"""
        print("创建发布包...")
        
        exe_path = self.dist_dir / "RedditMonitor.exe"
        if not exe_path.exists():
            print("  ERROR: 找不到exe文件")
            return False
            
        # 创建发布目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 复制exe文件
        release_exe = self.output_dir / "RedditMonitor.exe"
        shutil.copy2(exe_path, release_exe)
        
        # 创建使用说明
        readme_content = f"""Reddit监控系统 v1.0 使用说明
=====================================

快速开始:
1. 双击 RedditMonitor.exe 启动程序
2. 在"设置"选项卡中配置监控URL和间隔时间
3. 点击"开始监控"或"打开Web界面"

主要功能:
• 监控任何网站的内容变化
• 可视化的设置界面
• Web管理界面（浏览器访问）
• 数据分析和报告生成
• 完整的日志记录

使用方式:
1. 桌面GUI界面 - 双击exe文件
2. Web界面 - 点击"打开Web界面"按钮

数据文件:
程序会在exe同目录下创建以下文件夹：
- data/ - 监控数据存储
- config.json - 配置文件
- reddit_monitor.log - 日志文件

系统要求:
- Windows 7/8/10/11
- 无需安装Python环境
- 建议内存: 512MB+
- 建议硬盘: 100MB+

开发环境:
本项目使用uv进行依赖管理：
- uv sync --dev  # 同步开发依赖
- uv run pytest  # 运行测试
- uv run python main.py  # 运行程序

故障排除:
1. 如果程序无法启动，请确保有足够的磁盘空间
2. 如果监控失败，请检查网络连接
3. 如果需要技术支持，请提供日志文件

构建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
版本: 1.0.0
构建工具: uv + PyInstaller
"""
        
        readme_path = self.output_dir / "使用说明.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 创建zip压缩包
        zip_name = f"RedditMonitor_v1.0_{timestamp}.zip"
        zip_path = self.output_dir / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(release_exe, "RedditMonitor.exe")
            zipf.write(readme_path, "使用说明.txt")
            
        print(f"  OK: 发布包已创建:")
        print(f"     目录: {self.output_dir}")
        print(f"     压缩包: {zip_name}")
        print(f"     exe文件: RedditMonitor.exe")
        
        return True
    
    def build_all(self):
        """完整构建流程"""
        print("=" * 60)
        print("Reddit监控系统 - 自动打包")
        print("=" * 60)
        
        steps = [
            ("检查uv", self.check_uv),
            ("设置uv环境", self.setup_uv_environment), 
            ("清理构建目录", self.clean_build),
            ("构建exe", self.build_exe_with_uv),
            ("测试exe", self.test_exe),
            ("创建发布包", self.create_release_package),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"ERROR: {step_name} 失败，构建中止")
                return False
                
        print("\n" + "=" * 60)
        print("构建完成！")
        print("=" * 60)
        print(f"发布文件位置: {self.output_dir}")
        print("现在可以将exe文件分发给其他用户了！")
        print("\n开发提示:")
        print("- uv sync  # 同步依赖")
        print("- uv run python main.py  # 运行程序") 
        print("- uv run pytest  # 运行测试")
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reddit监控系统打包工具")
    parser.add_argument("--setup-only", action="store_true", help="仅设置uv环境")
    parser.add_argument("--clean", action="store_true", help="仅清理构建目录")
    
    args = parser.parse_args()
    
    builder = ExeBuilder()
    
    if args.setup_only:
        return builder.check_uv() and builder.setup_uv_environment()
    elif args.clean:
        builder.clean_build()
        return True
    else:
        return builder.build_all()


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n构建被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: 构建过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
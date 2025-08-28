#!/usr/bin/env python3
"""
Reddit监控系统 - 主启动程序
Portable版本的入口点，支持多种启动模式
"""

import os
import sys
import threading
import webbrowser
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
from pathlib import Path
import json

# 添加当前目录到Python路径，确保能导入模块
if hasattr(sys, '_MEIPASS'):
    # PyInstaller打包后的临时目录
    BASE_DIR = sys._MEIPASS
    REAL_DIR = os.path.dirname(sys.executable)
else:
    # 开发环境
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    REAL_DIR = BASE_DIR

sys.path.insert(0, BASE_DIR)

# 设置工作目录为exe所在目录
os.chdir(REAL_DIR)

try:
    from config_manager import ConfigManager
    from reddit_monitor import RedditMonitor
    from web_interface import app
    from data_analyzer import DataAnalyzer
except ImportError as e:
    print(f"导入模块失败: {e}")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"REAL_DIR: {REAL_DIR}")
    print(f"Python路径: {sys.path}")
    sys.exit(1)


class RedditMonitorGUI:
    """Reddit监控系统的图形界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Reddit监控系统 v1.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置图标（如果有的话）
        try:
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.config_manager = ConfigManager()
        self.monitor = None
        self.monitor_thread = None
        self.web_server_process = None
        self.is_monitoring = False
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        
        title_label = ttk.Label(title_frame, text="Reddit监控系统", font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        version_label = ttk.Label(title_frame, text="v1.0", font=('Arial', 10))
        version_label.pack(side=tk.RIGHT)
        
        # 创建选项卡
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 主控制面板
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="主控制")
        self.setup_main_tab(main_frame)
        
        # 设置面板
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="设置")
        self.setup_settings_tab(settings_frame)
        
        # 日志面板
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="日志")
        self.setup_log_tab(log_frame)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def setup_main_tab(self, parent):
        """设置主控制选项卡"""
        # 当前配置显示
        config_frame = ttk.LabelFrame(parent, text="当前配置")
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.url_var = tk.StringVar()
        self.interval_var = tk.StringVar()
        self.status_text_var = tk.StringVar(value="未运行")
        
        ttk.Label(config_frame, text="监控URL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.url_label = ttk.Label(config_frame, textvariable=self.url_var, font=('Arial', 9))
        self.url_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(config_frame, text="监控间隔:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.interval_label = ttk.Label(config_frame, textvariable=self.interval_var)
        self.interval_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(config_frame, text="运行状态:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.status_label = ttk.Label(config_frame, textvariable=self.status_text_var, foreground='red')
        self.status_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 控制按钮
        control_frame = ttk.LabelFrame(parent, text="控制")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=10)
        
        self.web_btn = ttk.Button(button_frame, text="打开Web界面", command=self.open_web_interface)
        self.web_btn.pack(side=tk.LEFT, padx=5)
        
        self.test_btn = ttk.Button(button_frame, text="测试单次监控", command=self.test_monitoring)
        self.test_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = ttk.Button(button_frame, text="开始监控", command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="停止监控", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 数据分析
        analysis_frame = ttk.LabelFrame(parent, text="数据分析")
        analysis_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(analysis_frame, text="生成分析报告", command=self.generate_report).pack(pady=10)
        
    def setup_settings_tab(self, parent):
        """设置配置选项卡"""
        # URL设置
        url_frame = ttk.LabelFrame(parent, text="监控设置")
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(url_frame, text="监控URL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(url_frame, text="间隔(分钟):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.interval_entry = ttk.Entry(url_frame, width=10)
        self.interval_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(url_frame, text="数据目录:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.data_dir_entry = ttk.Entry(url_frame, width=40)
        self.data_dir_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 预设URL
        preset_frame = ttk.LabelFrame(parent, text="预设URL")
        preset_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.preset_listbox = tk.Listbox(preset_frame)
        self.preset_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.preset_listbox.bind('<Double-Button-1>', self.select_preset_url)
        
        # 控制按钮
        settings_btn_frame = ttk.Frame(parent)
        settings_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(settings_btn_frame, text="保存设置", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(settings_btn_frame, text="重置默认", command=self.reset_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(settings_btn_frame, text="测试连接", command=self.test_connection).pack(side=tk.RIGHT, padx=5)
        
    def setup_log_tab(self, parent):
        """设置日志选项卡"""
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=20, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        log_btn_frame = ttk.Frame(parent)
        log_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_btn_frame, text="刷新日志", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_btn_frame, text="清空日志", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_btn_frame, text="导出日志", command=self.export_logs).pack(side=tk.RIGHT, padx=5)
        
    def load_config(self):
        """加载配置"""
        config = self.config_manager.get_config()
        monitor_config = config.get('monitor', {})
        
        self.url_var.set(monitor_config.get('url', ''))
        self.interval_var.set(f"{monitor_config.get('interval_minutes', 10)} 分钟")
        
        # 加载到设置界面
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, monitor_config.get('url', ''))
        
        self.interval_entry.delete(0, tk.END)
        self.interval_entry.insert(0, str(monitor_config.get('interval_minutes', 10)))
        
        self.data_dir_entry.delete(0, tk.END)
        self.data_dir_entry.insert(0, monitor_config.get('data_directory', 'data'))
        
        # 加载预设URL
        self.load_preset_urls()
        
        # 刷新日志
        self.refresh_logs()
        
    def load_preset_urls(self):
        """加载预设URL列表"""
        self.preset_listbox.delete(0, tk.END)
        urls = self.config_manager.get_predefined_urls()
        for url_info in urls:
            display_text = f"{url_info['name']} - {url_info['description']}"
            self.preset_listbox.insert(tk.END, display_text)
            
    def select_preset_url(self, event):
        """选择预设URL"""
        selection = self.preset_listbox.curselection()
        if selection:
            index = selection[0]
            urls = self.config_manager.get_predefined_urls()
            if index < len(urls):
                url = urls[index]['url']
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, url)
                
    def save_settings(self):
        """保存设置"""
        try:
            url = self.url_entry.get().strip()
            interval = int(self.interval_entry.get().strip())
            data_dir = self.data_dir_entry.get().strip()
            
            if not url.startswith(('http://', 'https://')):
                messagebox.showerror("错误", "URL必须以http://或https://开头")
                return
                
            if interval < 1:
                messagebox.showerror("错误", "监控间隔必须大于0分钟")
                return
                
            success = self.config_manager.update_monitor_config(
                url=url,
                interval_minutes=interval,
                data_directory=data_dir
            )
            
            if success:
                messagebox.showinfo("成功", "设置已保存")
                self.load_config()
                self.status_var.set("设置已更新")
            else:
                messagebox.showerror("错误", "保存设置失败")
                
        except ValueError:
            messagebox.showerror("错误", "监控间隔必须是数字")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置时出错: {e}")
            
    def reset_settings(self):
        """重置为默认设置"""
        if messagebox.askyesno("确认", "确定要重置为默认设置吗？"):
            self.config_manager.reset_to_defaults()
            self.load_config()
            messagebox.showinfo("成功", "已重置为默认设置")
            
    def test_connection(self):
        """测试连接"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入URL")
            return
            
        self.status_var.set("测试连接中...")
        
        def test_thread():
            try:
                import requests
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.root.after(0, lambda: messagebox.showinfo("成功", f"连接测试成功\n状态码: {response.status_code}"))
                    self.root.after(0, lambda: self.status_var.set("连接测试成功"))
                else:
                    self.root.after(0, lambda: messagebox.showwarning("警告", f"连接成功但状态码异常: {response.status_code}"))
                    self.root.after(0, lambda: self.status_var.set("连接测试完成"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"连接测试失败: {e}"))
                self.root.after(0, lambda: self.status_var.set("连接测试失败"))
                
        threading.Thread(target=test_thread, daemon=True).start()
        
    def open_web_interface(self):
        """打开Web界面"""
        if self.web_server_process and self.web_server_process.poll() is None:
            # 服务器已运行，直接打开浏览器
            webbrowser.open('http://127.0.0.1:5000')
            return
            
        # 启动Web服务器
        def start_web_server():
            try:
                from web_interface import app
                app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"启动Web服务器失败: {e}"))
                
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        
        # 等待服务器启动后打开浏览器
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://127.0.0.1:5000')
            
        threading.Thread(target=open_browser, daemon=True).start()
        
        self.status_var.set("Web服务器已启动")
        messagebox.showinfo("成功", "Web界面已启动，浏览器将自动打开\n地址: http://127.0.0.1:5000")
        
    def test_monitoring(self):
        """测试单次监控"""
        config = self.config_manager.get_monitor_config()
        url = config.get('url')
        data_dir = config.get('data_directory', 'data')
        
        if not url:
            messagebox.showerror("错误", "请先配置监控URL")
            return
            
        self.status_var.set("执行单次监控测试...")
        
        def test_thread():
            try:
                monitor = RedditMonitor(url=url, data_dir=data_dir)
                monitor.monitor_once()
                self.root.after(0, lambda: messagebox.showinfo("成功", "单次监控测试完成，请查看数据目录"))
                self.root.after(0, lambda: self.status_var.set("单次监控测试完成"))
                self.root.after(0, self.refresh_logs)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"监控测试失败: {e}"))
                self.root.after(0, lambda: self.status_var.set("监控测试失败"))
                
        threading.Thread(target=test_thread, daemon=True).start()
        
    def start_monitoring(self):
        """开始持续监控"""
        if self.is_monitoring:
            messagebox.showwarning("警告", "监控已在运行中")
            return
            
        config = self.config_manager.get_monitor_config()
        url = config.get('url')
        interval_minutes = config.get('interval_minutes', 10)
        data_dir = config.get('data_directory', 'data')
        
        if not url:
            messagebox.showerror("错误", "请先配置监控URL")
            return
            
        self.is_monitoring = True
        self.status_text_var.set("运行中")
        self.status_label.configure(foreground='green')
        
        # 启动状态更新定时器
        self.update_status_display()
        
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        
        def monitoring_thread():
            try:
                self.monitor = RedditMonitor(
                    url=url,
                    interval=interval_minutes * 60,
                    data_dir=data_dir,
                    config_manager=self.config_manager
                )
                
                # 使用智能监控
                self.monitor.start_monitoring()
                        
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"监控过程中出错: {e}"))
            finally:
                self.is_monitoring = False
                self.root.after(0, self.update_monitoring_ui)
                
        self.monitor_thread = threading.Thread(target=monitoring_thread, daemon=True)
        self.monitor_thread.start()
        
        self.status_var.set("持续监控已启动")
        
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        self.update_monitoring_ui()
        self.status_var.set("监控已停止")
        
    def update_monitoring_ui(self):
        """更新监控相关UI状态"""
        if not self.is_monitoring:
            self.status_text_var.set("未运行")
            self.status_label.configure(foreground='red')
            self.start_btn.configure(state=tk.NORMAL)
            self.stop_btn.configure(state=tk.DISABLED)
            
    def generate_report(self):
        """生成分析报告"""
        def report_thread():
            try:
                config = self.config_manager.get_monitor_config()
                data_dir = config.get('data_directory', 'data')
                analyzer = DataAnalyzer(data_dir)
                
                # 重定向输出到字符串
                import io
                from contextlib import redirect_stdout
                
                output = io.StringIO()
                with redirect_stdout(output):
                    analyzer.generate_report()
                    
                report_text = output.getvalue()
                
                def show_report():
                    report_window = tk.Toplevel(self.root)
                    report_window.title("监控数据分析报告")
                    report_window.geometry("800x600")
                    
                    text_widget = scrolledtext.ScrolledText(report_window, font=('Consolas', 10))
                    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                    text_widget.insert(tk.END, report_text)
                    text_widget.configure(state=tk.DISABLED)
                    
                self.root.after(0, show_report)
                self.root.after(0, lambda: self.status_var.set("分析报告已生成"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"生成报告失败: {e}"))
                
        threading.Thread(target=report_thread, daemon=True).start()
        
    def refresh_logs(self):
        """刷新日志显示"""
        try:
            if os.path.exists('reddit_monitor.log'):
                with open('reddit_monitor.log', 'r', encoding='utf-8') as f:
                    logs = f.read()
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, logs)
                self.log_text.see(tk.END)
        except Exception as e:
            print(f"读取日志失败: {e}")
            
    def clear_logs(self):
        """清空日志"""
        if messagebox.askyesno("确认", "确定要清空日志吗？"):
            try:
                if os.path.exists('reddit_monitor.log'):
                    os.remove('reddit_monitor.log')
                self.log_text.delete(1.0, tk.END)
                self.status_var.set("日志已清空")
            except Exception as e:
                messagebox.showerror("错误", f"清空日志失败: {e}")
                
    def export_logs(self):
        """导出日志"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if filename:
                content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"日志已导出到: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出日志失败: {e}")
    
    def update_status_display(self):
        """更新状态显示"""
        if self.is_monitoring and hasattr(self, 'monitor') and self.monitor:
            try:
                stats = self.config_manager.get_session_stats()
                
                # 构建状态文本
                status_text = "运行中"
                if stats['total_checks'] > 0:
                    status_text += f" (检查: {stats['total_checks']}, 成功率: {stats['success_rate']:.1f}%)"
                    
                if stats['time_until_next'] > 0:
                    minutes = stats['time_until_next'] // 60
                    seconds = stats['time_until_next'] % 60
                    if minutes > 0:
                        status_text += f", 下次: {minutes}分{seconds}秒"
                    else:
                        status_text += f", 下次: {seconds}秒"
                
                self.status_text_var.set(status_text)
                
            except Exception as e:
                print(f"更新状态显示错误: {e}")
        
        # 如果仍在监控中，继续定时更新
        if self.is_monitoring:
            self.root.after(5000, self.update_status_display)  # 每5秒更新一次
    
    def update_monitoring_ui(self):
        """更新监控UI状态"""
        self.status_text_var.set("已停止")
        self.status_label.configure(foreground='red')
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
            
    def run(self):
        """运行GUI"""
        self.root.mainloop()
        
    def on_closing(self):
        """程序关闭时的清理"""
        self.is_monitoring = False
        if self.web_server_process:
            self.web_server_process.terminate()
        self.root.destroy()


def main():
    """主函数"""
    print("Reddit监控系统启动中...")
    
    # 检查是否在打包环境中
    if hasattr(sys, '_MEIPASS'):
        print(f"运行在打包环境中: {sys._MEIPASS}")
        print(f"可执行文件路径: {sys.executable}")
    
    try:
        # 启动GUI
        gui = RedditMonitorGUI()
        gui.run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行时出错: {e}")
        import traceback
        traceback.print_exc()
        
        # 如果是GUI错误，显示错误对话框
        try:
            import tkinter.messagebox as msgbox
            msgbox.showerror("程序错误", f"程序运行时出现错误:\n{e}\n\n详细信息请查看控制台输出")
        except:
            pass
    
    print("程序退出")


if __name__ == "__main__":
    main()
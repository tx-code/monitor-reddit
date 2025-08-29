import streamlit as st
from typing import Dict, Any, List, Tuple
import os

from ...utils.validators import URLValidator, ConfigValidator, get_suggested_reddit_urls

def display_config_form(config_manager) -> Dict[str, Any]:
    """Display configuration form and return updated config"""
    st.sidebar.header("⚙️ 监控配置")
    
    # Get current configuration
    current_config = config_manager.get_monitor_config()
    
    with st.sidebar.form("config_form"):
        st.write("**基本设置**")
        
        # URL configuration with suggestions
        url_option = st.radio(
            "URL选择方式",
            ["预设URL", "自定义URL"],
            index=0 if current_config.get('url', '') in [item['url'] for item in get_suggested_reddit_urls()] else 1
        )
        
        if url_option == "预设URL":
            suggested_urls = get_suggested_reddit_urls()
            url_options = {item['name']: item['url'] for item in suggested_urls}
            
            current_url = current_config.get('url', '')
            current_selection = None
            for name, url in url_options.items():
                if url == current_url:
                    current_selection = name
                    break
            
            selected_option = st.selectbox(
                "选择预设URL",
                options=list(url_options.keys()),
                index=list(url_options.keys()).index(current_selection) if current_selection else 0
            )
            url = url_options[selected_option]
            
            # Show description
            for item in suggested_urls:
                if item['url'] == url:
                    st.caption(f"📝 {item['description']}")
                    break
                    
        else:
            url = st.text_input(
                "Reddit URL",
                value=current_config.get('url', 'https://www.reddit.com/r/CNC/'),
                help="输入完整的Reddit子版块URL"
            )
        
        # Interval configuration
        interval = st.number_input(
            "检查间隔 (分钟)",
            min_value=1,
            max_value=1440,
            value=current_config.get('interval_minutes', 5),
            help="监控检查的时间间隔，建议5-60分钟"
        )
        
        # Data directory configuration
        data_dir = st.text_input(
            "数据目录",
            value=current_config.get('data_directory', 'data'),
            help="存储监控数据的目录路径"
        )
        
        st.write("**高级设置**")
        
        # Advanced settings in an expander
        with st.expander("显示高级选项"):
            continuous_mode = st.checkbox(
                "连续模式",
                value=current_config.get('continuous_mode', True),
                help="启用智能调度和时间恢复功能"
            )
            
            auto_cleanup = st.checkbox(
                "自动清理",
                value=True,
                help="自动清理旧的日志文件"
            )
        
        # Form submission
        submitted = st.form_submit_button("💾 保存配置", width="stretch")
        
        if submitted:
            # Validate configuration
            is_valid, validation_errors = validate_config_input(url, interval, data_dir)
            
            if is_valid:
                new_config = {
                    'url': url,
                    'interval_minutes': interval,
                    'data_directory': data_dir,
                    'enabled': current_config.get('enabled', False),
                    'continuous_mode': continuous_mode
                }
                
                if config_manager.update_monitor_config(new_config):
                    st.success("✅ 配置已保存！")
                    st.rerun()
                else:
                    st.error("❌ 配置保存失败")
            else:
                for error in validation_errors:
                    st.error(f"❌ {error}")
    
    return config_manager.get_monitor_config()

def validate_config_input(url: str, interval: int, data_dir: str) -> Tuple[bool, List[str]]:
    """Validate configuration input"""
    errors = []
    
    # Validate URL
    is_valid_url, url_msg = URLValidator.validate_reddit_url(url)
    if not is_valid_url:
        errors.append(f"URL错误: {url_msg}")
    
    # Validate interval
    is_valid_interval, interval_msg = ConfigValidator.validate_interval(interval)
    if not is_valid_interval:
        errors.append(f"间隔错误: {interval_msg}")
    
    # Validate data directory
    is_valid_dir, dir_msg = ConfigValidator.validate_data_directory(data_dir)
    if not is_valid_dir:
        errors.append(f"目录错误: {dir_msg}")
    
    return len(errors) == 0, errors

def display_monitoring_controls(config_manager, monitoring_enabled: bool) -> Dict[str, Any]:
    """Display monitoring control buttons"""
    st.sidebar.header("🎮 监控控制")
    
    col1, col2 = st.sidebar.columns(2)
    
    controls = {
        'start_clicked': False,
        'stop_clicked': False,
        'check_clicked': False
    }
    
    with col1:
        if st.button(
            "🟢 开始" if not monitoring_enabled else "🟢 运行中",
            disabled=monitoring_enabled,
            width="stretch",
            help="启动后台监控进程"
        ):
            controls['start_clicked'] = True
    
    with col2:
        if st.button(
            "🔴 停止" if monitoring_enabled else "🔴 已停止",
            disabled=not monitoring_enabled,
            width="stretch",
            help="停止后台监控进程"
        ):
            controls['stop_clicked'] = True
    
    # Manual check button (always enabled)
    if st.sidebar.button(
        "🔍 手动检查",
        width="stretch",
        help="立即执行一次检查"
    ):
        controls['check_clicked'] = True
    
    return controls

def display_system_status(config_manager, monitoring_enabled: bool) -> None:
    """Display system status information"""
    st.sidebar.markdown("---")
    st.sidebar.header("📊 系统状态")
    
    # Current monitoring status
    if monitoring_enabled:
        st.sidebar.success("🟢 监控运行中")
        
        # Show next check time if available
        try:
            time_until_next = config_manager.get_time_until_next_check()
            if time_until_next > 0:
                minutes = time_until_next // 60
                seconds = time_until_next % 60
                st.sidebar.info(f"⏰ 下次检查: {minutes}分{seconds}秒后")
        except Exception:
            pass
    else:
        st.sidebar.warning("🔴 监控已停止")
    
    # Show session statistics
    try:
        stats = config_manager.get_session_stats()
        
        with st.sidebar.expander("📈 统计信息", expanded=False):
            st.write(f"**本次会话:**")
            st.write(f"- 检查次数: {stats['session_checks']}")
            
            st.write(f"**总计:**")
            st.write(f"- 总检查: {stats['total_checks']}")
            st.write(f"- 失败次数: {stats['failed_checks']}")
            st.write(f"- 成功率: {stats['success_rate']:.1f}%")
            
            if stats['last_check']:
                st.write(f"- 上次检查: {stats['last_check']}")
    except Exception:
        pass

def display_data_management_controls(config_manager) -> Dict[str, Any]:
    """Display data management controls"""
    st.sidebar.markdown("---")
    st.sidebar.header("📁 数据管理")
    
    controls = {
        'export_csv': False,
        'export_json': False,
        'clear_data': False,
        'backup_data': False
    }
    
    data_dir = config_manager.get_data_directory()
    csv_file = f"{data_dir}/reddit_online_count.csv"
    
    # Check if data exists
    data_exists = os.path.exists(csv_file)
    
    if data_exists:
        # Export options
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("📄 CSV", help="导出CSV格式", width="stretch"):
                controls['export_csv'] = True
        
        with col2:
            if st.button("📊 JSON", help="导出JSON格式", width="stretch"):
                controls['export_json'] = True
        
        # Data management options
        with st.sidebar.expander("⚙️ 数据管理", expanded=False):
            # Backup functionality
            if st.button(
                "💾 备份数据",
                help="创建数据备份文件",
                width="stretch"
            ):
                controls['backup_data'] = True
            
            # Dangerous operations
            st.warning("⚠️ 危险操作")
            
            if st.button(
                "🗑️ 清空数据",
                help="删除所有监控数据（会自动备份）",
                width="stretch"
            ):
                controls['clear_data'] = True
    else:
        st.sidebar.info("暂无数据文件")
    
    return controls

def display_help_info() -> None:
    """Display help information"""
    st.sidebar.markdown("---")
    st.sidebar.header("📖 使用说明")
    
    with st.sidebar.expander("💡 快速开始", expanded=False):
        st.markdown("""
        **开始监控的步骤：**
        
        1. 📝 配置Reddit URL和检查间隔
        2. 💾 保存配置
        3. 🟢 点击'开始'启动监控
        4. 📊 查看实时数据和图表
        
        **建议设置：**
        - 检查间隔: 5-15分钟
        - 使用预设的热门子版块
        - 启用连续模式获得最佳体验
        """)
    
    with st.sidebar.expander("🔧 故障排除", expanded=False):
        st.markdown("""
        **常见问题：**
        
        - **无法获取数据**: 检查网络连接和URL
        - **监控自动停止**: 查看日志文件
        - **数据不更新**: 手动检查一次
        - **配置保存失败**: 检查目录权限
        
        **日志文件位置**: `logs/` 目录
        """)

def create_config_backup(config_manager) -> str:
    """Create configuration backup"""
    import json
    from datetime import datetime
    
    try:
        config = config_manager.get_config()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"config/backup_{timestamp}.json"
        
        os.makedirs(os.path.dirname(backup_file), exist_ok=True)
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False, default=str)
        
        return backup_file
    except Exception as e:
        st.error(f"备份配置失败: {e}")
        return None
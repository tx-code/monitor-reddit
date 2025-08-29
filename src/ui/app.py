import streamlit as st
import pandas as pd
import os
import sys
import subprocess
import time
from datetime import datetime
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.config_manager import ConfigManager
from src.core.reddit_monitor import RedditMonitor
from src.core.data_analyzer import DataAnalyzer
from src.ui.components.dashboard import (
    display_metrics_cards, display_subreddit_info, display_statistics_summary,
    display_activity_status, display_recent_activity, create_data_quality_indicator,
    check_data_anomalies
)
from src.ui.components.charts import (
    create_time_series_chart, create_hourly_pattern_chart, create_distribution_chart,
    create_change_analysis_chart, display_chart_controls, filter_data_by_time_range
)
from src.ui.components.config_panel import (
    display_config_form, display_monitoring_controls, display_system_status,
    display_data_management_controls, display_help_info
)

# Page configuration
st.set_page_config(
    page_title="Reddit在线人数监控系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}

.status-success {
    color: #28a745;
    font-weight: bold;
}

.status-warning {
    color: #ffc107;
    font-weight: bold;
}

.status-error {
    color: #dc3545;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

class RedditMonitorApp:
    """Main Streamlit application for Reddit monitoring"""
    
    def __init__(self):
        self.config_manager = self._get_config_manager()
        self.data_analyzer = DataAnalyzer(self.config_manager.get_data_directory())
        
    def _get_config_manager(self):
        """Get config manager instance (without caching to avoid hash issues)"""
        if not hasattr(self, '_config_manager_instance'):
            self._config_manager_instance = ConfigManager()
        return self._config_manager_instance
    
    def load_monitoring_data(self) -> Optional[pd.DataFrame]:
        """Load monitoring data without caching to avoid hash issues"""
        csv_file = f"{self.config_manager.get_data_directory()}/reddit_online_count.csv"
        
        if not os.path.exists(csv_file):
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(csv_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['online_count'] = pd.to_numeric(df['online_count'], errors='coerce')
            df['member_count'] = pd.to_numeric(df['member_count'], errors='coerce')
            return df.dropna(subset=['online_count'])
        except Exception as e:
            st.error(f"读取数据失败: {e}")
            return pd.DataFrame()
    
    def get_monitoring_status(self) -> bool:
        """Get current monitoring status without caching"""
        return self.config_manager.get_monitor_config().get('enabled', False)
    
    def start_background_monitoring(self) -> bool:
        """Start background monitoring process"""
        try:
            if 'monitor_process' not in st.session_state or st.session_state.monitor_process is None:
                # Create background monitor script path
                script_path = os.path.join('scripts', 'background_monitor.py')
                
                if not os.path.exists(script_path):
                    st.error("后台监控脚本不存在，请先创建脚本文件")
                    return False
                
                process = subprocess.Popen([
                    sys.executable, script_path
                ], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
                )
                
                st.session_state.monitor_process = process
                self.config_manager.update_monitor_config({'enabled': True})
                st.success("✅ 后台监控已启动")
                return True
            else:
                st.info("ℹ️ 监控已在运行中")
                return True
                
        except Exception as e:
            st.error(f"❌ 启动监控失败: {e}")
            return False
    
    def stop_background_monitoring(self) -> bool:
        """Stop background monitoring process"""
        try:
            if 'monitor_process' in st.session_state and st.session_state.monitor_process is not None:
                st.session_state.monitor_process.terminate()
                try:
                    st.session_state.monitor_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    st.session_state.monitor_process.kill()
                    st.session_state.monitor_process.wait()
                
                st.session_state.monitor_process = None
                
            self.config_manager.update_monitor_config({'enabled': False})
            st.warning("⚠️ 监控已停止")
            return True
            
        except Exception as e:
            st.error(f"❌ 停止监控失败: {e}")
            return False
    
    def perform_manual_check(self) -> None:
        """Perform manual monitoring check"""
        try:
            with st.spinner("🔍 正在检查Reddit在线人数..."):
                config = self.config_manager.get_monitor_config()
                monitor = RedditMonitor(
                    url=config.get('url', 'https://www.reddit.com/r/CNC/'),
                    interval=config.get('interval_minutes', 5) * 60,
                    data_dir=config.get('data_directory', 'data'),
                    config_manager=self.config_manager
                )
                
                success = monitor.monitor_once()
                
                if success:
                    st.success("✅ 检查完成！数据已更新")
                else:
                    st.warning("⚠️ 检查失败，请查看日志文件")
                
                # Rerun to show updated data
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ 手动检查失败: {e}")
    
    def handle_data_export(self, export_format: str, df: pd.DataFrame) -> None:
        """Handle data export requests"""
        if df.empty:
            st.warning("没有数据可导出")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            if export_format == 'csv':
                csv_data = df.to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="⬇️ 下载CSV文件",
                    data=csv_data,
                    file_name=f"reddit_monitor_{timestamp}.csv",
                    mime="text/csv"
                )
                
            elif export_format == 'json':
                json_data = df.to_json(orient='records', date_format='iso', indent=2)
                st.download_button(
                    label="⬇️ 下载JSON文件",
                    data=json_data,
                    file_name=f"reddit_monitor_{timestamp}.json",
                    mime="application/json"
                )
        except Exception as e:
            st.error(f"导出失败: {e}")
    
    def handle_data_clear(self) -> None:
        """Handle data clearing with confirmation"""
        st.warning("⚠️ 确认删除所有监控数据？此操作不可撤销！")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ 确认删除", type="primary"):
                try:
                    data_dir = self.config_manager.get_data_directory()
                    csv_file = f"{data_dir}/reddit_online_count.csv"
                    
                    if os.path.exists(csv_file):
                        # Create backup before deletion
                        backup_file = f"{data_dir}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        os.rename(csv_file, backup_file)
                        
                        st.success(f"✅ 数据已清理！备份保存至: {backup_file}")
                        st.info("🔄 页面将在3秒后刷新...")
                        
                        # Auto refresh after 3 seconds
                        import time
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.warning("📂 没有找到数据文件")
                        
                except Exception as e:
                    st.error(f"❌ 清理失败: {e}")
        
        with col2:
            if st.button("❌ 取消"):
                st.info("操作已取消")
                st.rerun()
    
    def handle_data_backup(self, df: pd.DataFrame) -> None:
        """Handle data backup"""
        if df.empty:
            st.warning("没有数据可备份")
            return
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            data_dir = self.config_manager.get_data_directory()
            
            # Create backups directory if not exists
            backup_dir = os.path.join(data_dir, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename
            backup_file = os.path.join(backup_dir, f"reddit_backup_{timestamp}.csv")
            
            # Save backup
            df.to_csv(backup_file, index=False, encoding='utf-8')
            
            st.success(f"✅ 备份创建成功！")
            st.info(f"📁 备份文件: {backup_file}")
            
            # Show backup download button
            csv_data = df.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="⬇️ 下载备份文件",
                data=csv_data,
                file_name=f"reddit_backup_{timestamp}.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"❌ 备份失败: {e}")
    
    def render_main_dashboard(self, df: pd.DataFrame) -> None:
        """Render the main dashboard"""
        st.title("📊 Reddit在线人数监控系统")
        
        if df.empty:
            st.warning("🔍 暂无监控数据")
            st.info("💡 点击侧边栏的 '开始' 按钮启动监控，或点击 '手动检查' 获取数据")
            return
        
        # Main metrics
        display_metrics_cards(df)
        
        # Subreddit info
        display_subreddit_info(df)
        
        # Charts section
        st.subheader("📈 数据可视化")
        
        # Chart controls
        time_range, show_trend, chart_type = display_chart_controls()
        
        # Filter data
        filtered_df = filter_data_by_time_range(df, time_range)
        
        if filtered_df.empty:
            st.warning(f"选定时间范围内暂无数据: {time_range}")
            return
        
        # Display selected chart
        try:
            if chart_type == "时间序列":
                fig = create_time_series_chart(filtered_df, time_range)
                st.plotly_chart(fig, width="stretch")
                
            elif chart_type == "分布图":
                fig = create_distribution_chart(filtered_df)
                st.plotly_chart(fig, width="stretch")
                
            elif chart_type == "变化分析":
                fig = create_change_analysis_chart(filtered_df)
                st.plotly_chart(fig, width="stretch")
                
            elif chart_type == "活动模式":
                fig = create_hourly_pattern_chart(filtered_df)
                st.plotly_chart(fig, width="stretch")
                
        except Exception as e:
            st.error(f"图表渲染失败: {e}")
        
        # Additional sections in tabs
        tab1, tab2, tab3 = st.tabs(["📋 详细数据", "📈 统计分析", "🔍 数据质量"])
        
        with tab1:
            self.render_data_table(filtered_df)
        
        with tab2:
            display_statistics_summary(filtered_df)
        
        with tab3:
            create_data_quality_indicator(filtered_df)
    
    def render_data_table(self, df: pd.DataFrame) -> None:
        """Render data table with controls"""
        st.subheader("📋 监控记录详情")
        
        # Table controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_rows = st.number_input("显示行数", min_value=10, max_value=1000, value=50)
        
        with col2:
            show_success_only = st.checkbox("仅显示成功记录", value=False)
        
        with col3:
            sort_order = st.selectbox("排序", ["最新在前", "最旧在前"], index=0)
        
        # Filter and sort data
        display_df = df.copy()
        
        if show_success_only and 'success' in display_df.columns:
            display_df = display_df[display_df['success'] == True]
        
        display_df = display_df.tail(show_rows) if sort_order == "最新在前" else display_df.head(show_rows)
        
        if sort_order == "最新在前":
            display_df = display_df.sort_values('timestamp', ascending=False)
        
        # Format for display
        if not display_df.empty:
            display_df_formatted = display_df.copy()
            display_df_formatted['时间'] = display_df_formatted['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            display_df_formatted['子版块'] = 'r/' + display_df_formatted['subreddit'].astype(str)
            display_df_formatted['在线人数'] = display_df_formatted['online_count'].fillna(0).astype(int)
            display_df_formatted['成员数'] = display_df_formatted['member_count'].fillna(0).astype(int)
            
            if 'success' in display_df_formatted.columns:
                display_df_formatted['状态'] = display_df_formatted['success'].map({
                    True: '✅ 成功', 
                    False: '❌ 失败'
                })
                display_columns = ['时间', '子版块', '在线人数', '成员数', '状态']
            else:
                display_columns = ['时间', '子版块', '在线人数', '成员数']
            
            st.dataframe(
                display_df_formatted[display_columns],
                width="stretch",
                hide_index=True
            )
        else:
            st.info("没有符合条件的记录")
    
    def run(self) -> None:
        """Run the main application"""
        # Sidebar configuration
        current_config = display_config_form(self.config_manager)
        
        # Monitoring controls
        monitoring_enabled = self.get_monitoring_status()
        controls = display_monitoring_controls(self.config_manager, monitoring_enabled)
        
        # Handle control actions
        if controls['start_clicked']:
            if self.start_background_monitoring():
                st.rerun()
        
        if controls['stop_clicked']:
            if self.stop_background_monitoring():
                st.rerun()
        
        if controls['check_clicked']:
            self.perform_manual_check()
        
        # System status
        display_system_status(self.config_manager, monitoring_enabled)
        
        # Check for data anomalies
        df_for_anomaly_check = self.load_monitoring_data()
        check_data_anomalies(df_for_anomaly_check)
        
        # Data management
        data_controls = display_data_management_controls(self.config_manager)
        
        # Load and display data
        df = self.load_monitoring_data()
        
        # Handle data export
        if data_controls['export_csv']:
            self.handle_data_export('csv', df)
        
        if data_controls['export_json']:
            self.handle_data_export('json', df)
        
        if data_controls['backup_data']:
            self.handle_data_backup(df)
        
        if data_controls['clear_data']:
            self.handle_data_clear()
        
        # Help information
        display_help_info()
        
        # Main dashboard
        self.render_main_dashboard(df)
        
        # Auto-refresh
        self.handle_auto_refresh()
    
    def handle_auto_refresh(self) -> None:
        """Handle auto-refresh functionality"""
        st.sidebar.markdown("---")
        auto_refresh = st.sidebar.checkbox("🔄 自动刷新数据", value=False)
        
        if auto_refresh:
            refresh_interval = st.sidebar.slider("刷新间隔(秒)", 10, 300, 60)
            time.sleep(refresh_interval)
            st.rerun()

def main():
    """Main entry point"""
    app = RedditMonitorApp()
    app.run()

if __name__ == "__main__":
    main()
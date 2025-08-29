import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any

def display_metrics_cards(df: pd.DataFrame) -> None:
    """Display key metrics in cards format"""
    if df.empty:
        st.warning("暂无数据显示")
        return
    
    latest_data = df.iloc[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_online = int(latest_data['online_count']) if pd.notna(latest_data['online_count']) else 0
        previous_online = int(df.iloc[-2]['online_count']) if len(df) > 1 and pd.notna(df.iloc[-2]['online_count']) else 0
        delta = current_online - previous_online if len(df) > 1 else 0
        
        st.metric(
            label="🔥 当前在线人数",
            value=f"{current_online:,}",
            delta=f"{delta:+,}" if delta != 0 else None
        )
        
        # Alert for significant changes
        if len(df) > 5:
            recent_avg = df['online_count'].tail(5).mean()
            if abs(delta) > recent_avg * 0.3:  # 30% change threshold
                if delta > 0:
                    st.success("📈 大幅上升！")
                else:
                    st.warning("📉 大幅下降！")
    
    with col2:
        member_count = latest_data.get('member_count')
        if pd.notna(member_count):
            st.metric(
                label="👥 总成员数",
                value=f"{int(member_count):,}"
            )
        else:
            st.metric(
                label="👥 总成员数",
                value="N/A"
            )
    
    with col3:
        st.metric(
            label="📊 总记录数",
            value=f"{len(df):,}"
        )
    
    with col4:
        if 'success' in df.columns:
            success_rate = (df['success'] == True).mean() * 100
            st.metric(
                label="✅ 成功率",
                value=f"{success_rate:.1f}%"
            )
        else:
            st.metric(
                label="✅ 成功率",
                value="100.0%"
            )

def display_subreddit_info(df: pd.DataFrame) -> None:
    """Display subreddit information"""
    if df.empty:
        return
    
    latest_data = df.iloc[-1]
    subreddit = latest_data.get('subreddit', 'unknown')
    last_updated = latest_data['timestamp']
    
    if isinstance(last_updated, str):
        try:
            last_updated = pd.to_datetime(last_updated)
        except:
            pass
    
    update_time = last_updated.strftime('%Y-%m-%d %H:%M:%S') if hasattr(last_updated, 'strftime') else str(last_updated)
    
    st.info(f"🎯 监控目标: **r/{subreddit}** | 🕐 最后更新: {update_time}")

def display_statistics_summary(df: pd.DataFrame) -> None:
    """Display statistics summary in an expandable section"""
    if df.empty:
        return
    
    with st.expander("📈 统计摘要", expanded=False):
        online_counts = df['online_count'].dropna()
        
        if not online_counts.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 平均在线", f"{online_counts.mean():.0f}")
                st.metric("📈 最高记录", f"{online_counts.max():.0f}")
            
            with col2:
                st.metric("📉 最低记录", f"{online_counts.min():.0f}")
                st.metric("📊 中位数", f"{online_counts.median():.0f}")
            
            with col3:
                st.metric("📊 标准差", f"{online_counts.std():.0f}")
                
                # Calculate volatility (coefficient of variation)
                cv = (online_counts.std() / online_counts.mean()) * 100
                st.metric("🌊 波动性", f"{cv:.1f}%")

def display_activity_status(monitoring_enabled: bool, config_manager) -> None:
    """Display current monitoring activity status"""
    status_container = st.container()
    
    with status_container:
        if monitoring_enabled:
            st.success("🟢 监控系统运行中")
            
            # Show next check time if available
            try:
                next_check = config_manager.get_next_scheduled_check()
                if next_check:
                    time_until = config_manager.get_time_until_next_check()
                    if time_until > 0:
                        minutes = time_until // 60
                        seconds = time_until % 60
                        st.info(f"⏰ 下次检查: {minutes}分{seconds}秒后")
            except Exception:
                pass
                
        else:
            st.warning("🔴 监控系统已停止")
            st.info("💡 点击侧边栏的 '开始' 按钮启动监控")

def display_recent_activity(df: pd.DataFrame, limit: int = 5) -> None:
    """Display recent activity in a compact format"""
    if df.empty:
        return
    
    st.subheader("🔔 最近活动")
    
    recent_data = df.tail(limit).copy()
    recent_data = recent_data.sort_values('timestamp', ascending=False)
    
    for _, row in recent_data.iterrows():
        timestamp = row['timestamp']
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)
        
        time_str = timestamp.strftime('%H:%M:%S')
        online_count = row['online_count']
        
        if pd.notna(online_count):
            online_str = f"{int(online_count):,} 在线"
            
            # Color code based on success/failure
            if row.get('success', True):
                st.success(f"✅ {time_str}: {online_str}")
            else:
                st.error(f"❌ {time_str}: 检查失败")
        else:
            st.error(f"❌ {time_str}: 数据获取失败")

def display_quick_stats_sidebar(df: pd.DataFrame) -> None:
    """Display quick stats in sidebar"""
    if df.empty:
        return
    
    st.sidebar.markdown("### 📊 快速统计")
    
    online_counts = df['online_count'].dropna()
    if not online_counts.empty:
        st.sidebar.metric("当前在线", f"{online_counts.iloc[-1]:,.0f}")
        st.sidebar.metric("今日平均", f"{online_counts.mean():.0f}")
        
        # Show trend
        if len(online_counts) > 1:
            change = online_counts.iloc[-1] - online_counts.iloc[-2]
            trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            st.sidebar.metric("趋势", f"{trend} {change:+.0f}")

def create_data_quality_indicator(df: pd.DataFrame) -> None:
    """Display data quality indicators"""
    if df.empty:
        return
    
    with st.expander("🔍 数据质量", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Missing data analysis
            total_records = len(df)
            missing_online = df['online_count'].isna().sum()
            missing_members = df['member_count'].isna().sum() if 'member_count' in df.columns else 0
            
            st.write("**数据完整性:**")
            st.write(f"- 在线人数缺失: {missing_online}/{total_records} ({missing_online/total_records*100:.1f}%)")
            st.write(f"- 成员数缺失: {missing_members}/{total_records} ({missing_members/total_records*100:.1f}%)")
        
        with col2:
            # Success rate over time
            if 'success' in df.columns:
                success_count = (df['success'] == True).sum()
                success_rate = success_count / total_records * 100
                
                st.write("**检查成功率:**")
                st.write(f"- 成功: {success_count}/{total_records}")
                st.write(f"- 成功率: {success_rate:.1f}%")
                
                # Recent success rate (last 10 records)
                recent_df = df.tail(10)
                if len(recent_df) > 0:
                    recent_success = (recent_df['success'] == True).mean() * 100
                    st.write(f"- 最近成功率: {recent_success:.1f}%")

def check_data_anomalies(df: pd.DataFrame) -> None:
    """Check for data anomalies and display alerts"""
    if df.empty or len(df) < 10:
        return
    
    online_counts = df['online_count'].dropna()
    if len(online_counts) < 10:
        return
    
    # Calculate statistics
    recent_data = online_counts.tail(20)
    mean_val = recent_data.mean()
    std_val = recent_data.std()
    
    # Check for anomalies (values outside 2 standard deviations)
    threshold = 2 * std_val
    latest_value = online_counts.iloc[-1]
    
    if abs(latest_value - mean_val) > threshold:
        st.sidebar.warning("⚠️ 检测到数据异常")
        st.sidebar.write(f"当前值: {latest_value:.0f}")
        st.sidebar.write(f"正常范围: {mean_val - threshold:.0f} - {mean_val + threshold:.0f}")
    
    # Check for consecutive failures
    if 'success' in df.columns:
        recent_failures = df.tail(5)
        if (recent_failures['success'] == False).sum() >= 3:
            st.sidebar.error("🚨 连续监控失败！")
            st.sidebar.write("建议检查网络连接或URL设置")
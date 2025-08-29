import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

def create_time_series_chart(df: pd.DataFrame, time_range: str = "全部数据") -> go.Figure:
    """Create a time series chart for online count data"""
    if df.empty:
        return go.Figure()
    
    # Filter data based on time range
    filtered_df = filter_data_by_time_range(df, time_range)
    
    if filtered_df.empty:
        return go.Figure()
    
    # Get subreddit name for title
    subreddit = filtered_df.iloc[-1].get('subreddit', 'unknown')
    
    fig = go.Figure()
    
    # Add main line trace
    fig.add_trace(go.Scatter(
        x=filtered_df['timestamp'],
        y=filtered_df['online_count'],
        mode='lines+markers',
        name='在线人数',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=4),
        fill='tonexty',
        fillcolor='rgba(31, 119, 180, 0.1)',
        hovertemplate='<b>时间:</b> %{x}<br><b>在线人数:</b> %{y:,}<extra></extra>'
    ))
    
    # Add trend line if enough data points
    if len(filtered_df) > 5:
        z = np.polyfit(range(len(filtered_df)), filtered_df['online_count'], 1)
        trend_line = np.poly1d(z)(range(len(filtered_df)))
        
        fig.add_trace(go.Scatter(
            x=filtered_df['timestamp'],
            y=trend_line,
            mode='lines',
            name='趋势线',
            line=dict(color='red', width=1, dash='dash'),
            hovertemplate='<b>趋势值:</b> %{y:.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=f"Reddit r/{subreddit} 在线人数变化趋势 ({time_range})",
        xaxis_title="时间",
        yaxis_title="在线人数",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(x=0, y=1, bgcolor='rgba(255,255,255,0.8)'),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def create_hourly_pattern_chart(df: pd.DataFrame) -> go.Figure:
    """Create hourly activity pattern chart"""
    if df.empty:
        return go.Figure()
    
    # Extract hour from timestamp
    df_copy = df.copy()
    df_copy['hour'] = pd.to_datetime(df_copy['timestamp']).dt.hour
    
    # Calculate hourly averages
    hourly_avg = df_copy.groupby('hour')['online_count'].agg(['mean', 'std']).reset_index()
    
    fig = go.Figure()
    
    # Add bar chart for average online count by hour
    fig.add_trace(go.Bar(
        x=hourly_avg['hour'],
        y=hourly_avg['mean'],
        name='平均在线人数',
        marker_color='lightblue',
        hovertemplate='<b>时间:</b> %{x}:00<br><b>平均在线:</b> %{y:.0f}<extra></extra>'
    ))
    
    # Add error bars for standard deviation
    if 'std' in hourly_avg.columns and hourly_avg['std'].notna().any():
        fig.add_trace(go.Scatter(
            x=hourly_avg['hour'],
            y=hourly_avg['mean'] + hourly_avg['std'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.add_trace(go.Scatter(
            x=hourly_avg['hour'],
            y=hourly_avg['mean'] - hourly_avg['std'],
            mode='lines',
            line=dict(width=0),
            fillcolor='rgba(173, 216, 230, 0.3)',
            fill='tonexty',
            showlegend=False,
            hoverinfo='skip'
        ))
    
    fig.update_layout(
        title="24小时活动模式",
        xaxis_title="小时",
        yaxis_title="平均在线人数",
        height=400,
        xaxis=dict(tickmode='array', tickvals=list(range(0, 24, 2))),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def create_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Create distribution chart for online counts"""
    if df.empty:
        return go.Figure()
    
    online_counts = df['online_count'].dropna()
    
    fig = go.Figure()
    
    # Add histogram
    fig.add_trace(go.Histogram(
        x=online_counts,
        nbinsx=30,
        name='分布',
        marker_color='lightgreen',
        opacity=0.7
    ))
    
    # Add vertical lines for mean and median
    mean_val = online_counts.mean()
    median_val = online_counts.median()
    
    fig.add_vline(
        x=mean_val,
        line_dash="dash",
        line_color="red",
        annotation_text=f"平均值: {mean_val:.0f}",
        annotation_position="top"
    )
    
    fig.add_vline(
        x=median_val,
        line_dash="dot",
        line_color="blue",
        annotation_text=f"中位数: {median_val:.0f}",
        annotation_position="bottom"
    )
    
    fig.update_layout(
        title="在线人数分布图",
        xaxis_title="在线人数",
        yaxis_title="频次",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def create_change_analysis_chart(df: pd.DataFrame) -> go.Figure:
    """Create chart showing changes between consecutive measurements"""
    if len(df) < 2:
        return go.Figure()
    
    df_copy = df.copy().sort_values('timestamp')
    df_copy['change'] = df_copy['online_count'].diff()
    df_copy = df_copy.dropna(subset=['change'])
    
    if df_copy.empty:
        return go.Figure()
    
    # Create color coding for changes
    colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' for x in df_copy['change']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_copy['timestamp'],
        y=df_copy['change'],
        name='变化量',
        marker_color=colors,
        hovertemplate='<b>时间:</b> %{x}<br><b>变化:</b> %{y:+.0f}<extra></extra>'
    ))
    
    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="black",
        opacity=0.5
    )
    
    fig.update_layout(
        title="在线人数变化分析",
        xaxis_title="时间",
        yaxis_title="变化量",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def create_heatmap_chart(df: pd.DataFrame) -> go.Figure:
    """Create heatmap showing activity patterns by day and hour"""
    if df.empty:
        return go.Figure()
    
    df_copy = df.copy()
    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
    df_copy['hour'] = df_copy['timestamp'].dt.hour
    df_copy['day_name'] = df_copy['timestamp'].dt.day_name()
    
    # Create pivot table for heatmap
    pivot_data = df_copy.pivot_table(
        values='online_count',
        index='day_name',
        columns='hour',
        aggfunc='mean'
    )
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot_data = pivot_data.reindex([day for day in day_order if day in pivot_data.index])
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Viridis',
        hovertemplate='<b>星期:</b> %{y}<br><b>时间:</b> %{x}:00<br><b>平均在线:</b> %{z:.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="每周活动热力图",
        xaxis_title="小时",
        yaxis_title="星期",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def filter_data_by_time_range(df: pd.DataFrame, time_range: str) -> pd.DataFrame:
    """Filter dataframe by time range selection"""
    if df.empty:
        return df
    
    now = datetime.now()
    
    if time_range == "最近1小时":
        cutoff = now - timedelta(hours=1)
    elif time_range == "最近6小时":
        cutoff = now - timedelta(hours=6)
    elif time_range == "最近24小时":
        cutoff = now - timedelta(hours=24)
    elif time_range == "最近7天":
        cutoff = now - timedelta(days=7)
    elif time_range == "最近30天":
        cutoff = now - timedelta(days=30)
    else:  # "全部数据"
        return df
    
    # Convert timestamp to datetime if it's a string
    df_copy = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_copy['timestamp']):
        df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
    
    return df_copy[df_copy['timestamp'] >= cutoff]

def display_chart_controls() -> Tuple[str, bool, str]:
    """Display chart control widgets and return selections"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        time_range = st.selectbox(
            "时间范围",
            ["最近1小时", "最近6小时", "最近24小时", "最近7天", "最近30天", "全部数据"],
            index=2
        )
    
    with col2:
        show_trend = st.checkbox("显示趋势线", value=True)
    
    with col3:
        chart_type = st.selectbox(
            "图表类型",
            ["时间序列", "分布图", "变化分析", "活动模式"],
            index=0
        )
    
    return time_range, show_trend, chart_type

# Import numpy for trend line calculation
try:
    import numpy as np
except ImportError:
    np = None
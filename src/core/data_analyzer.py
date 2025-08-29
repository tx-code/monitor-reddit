import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Any
from collections import defaultdict

class DataAnalyzer:
    """Data analysis utilities for Reddit monitoring data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        
    def load_csv_data(self) -> Optional[pd.DataFrame]:
        """Load Reddit monitoring data from CSV file"""
        csv_file = f"{self.data_dir}/reddit_online_count.csv"
        
        if not os.path.exists(csv_file):
            return None
        
        try:
            df = pd.read_csv(csv_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['online_count'] = pd.to_numeric(df['online_count'], errors='coerce')
            df['member_count'] = pd.to_numeric(df['member_count'], errors='coerce')
            return df.dropna(subset=['online_count'])
        except Exception as e:
            print(f"Error loading CSV data: {e}")
            return None
    
    def get_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get basic statistics from the data"""
        if df.empty:
            return {}
        
        online_counts = df['online_count']
        stats = {
            'total_records': len(df),
            'time_range': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max(),
                'duration': df['timestamp'].max() - df['timestamp'].min()
            },
            'online_count_stats': {
                'mean': online_counts.mean(),
                'median': online_counts.median(),
                'min': online_counts.min(),
                'max': online_counts.max(),
                'std': online_counts.std()
            },
            'success_rate': (df['success'] == True).mean() * 100 if 'success' in df.columns else 100.0,
            'subreddits': df['subreddit'].unique().tolist() if 'subreddit' in df.columns else []
        }
        
        return stats
    
    def analyze_trends(self, df: pd.DataFrame, window: str = '1H') -> Dict[str, Any]:
        """Analyze trends in the data"""
        if df.empty:
            return {}
        
        # Resample data to the specified window
        df_resampled = df.set_index('timestamp').resample(window).agg({
            'online_count': ['mean', 'min', 'max', 'std'],
            'member_count': 'mean'
        }).round(2)
        
        # Flatten column names
        df_resampled.columns = ['_'.join(col).strip() for col in df_resampled.columns]
        
        # Calculate hourly patterns
        df['hour'] = df['timestamp'].dt.hour
        hourly_avg = df.groupby('hour')['online_count'].mean()
        
        # Calculate daily patterns
        df['day_of_week'] = df['timestamp'].dt.day_name()
        daily_avg = df.groupby('day_of_week')['online_count'].mean()
        
        return {
            'resampled_data': df_resampled,
            'hourly_pattern': hourly_avg.to_dict(),
            'daily_pattern': daily_avg.to_dict(),
            'peak_hour': hourly_avg.idxmax(),
            'lowest_hour': hourly_avg.idxmin()
        }
    
    def detect_anomalies(self, df: pd.DataFrame, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalies in online count using standard deviation"""
        if df.empty:
            return []
        
        mean = df['online_count'].mean()
        std = df['online_count'].std()
        
        anomalies = []
        for _, row in df.iterrows():
            z_score = abs(row['online_count'] - mean) / std
            if z_score > threshold:
                anomalies.append({
                    'timestamp': row['timestamp'],
                    'online_count': row['online_count'],
                    'z_score': z_score,
                    'type': 'high' if row['online_count'] > mean else 'low'
                })
        
        return anomalies
    
    def get_growth_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate growth/change metrics"""
        if len(df) < 2:
            return {}
        
        # Sort by timestamp to ensure proper order
        df_sorted = df.sort_values('timestamp')
        
        # Calculate changes between consecutive measurements
        df_sorted['online_count_change'] = df_sorted['online_count'].diff()
        df_sorted['change_rate'] = (df_sorted['online_count_change'] / df_sorted['online_count'].shift(1)) * 100
        
        # Get significant changes (more than 10% or more than 50 users)
        significant_changes = df_sorted[
            (abs(df_sorted['online_count_change']) > 50) | 
            (abs(df_sorted['change_rate']) > 10)
        ]
        
        return {
            'total_change': df_sorted['online_count'].iloc[-1] - df_sorted['online_count'].iloc[0],
            'avg_change_per_measurement': df_sorted['online_count_change'].mean(),
            'biggest_increase': df_sorted['online_count_change'].max(),
            'biggest_decrease': df_sorted['online_count_change'].min(),
            'significant_changes_count': len(significant_changes),
            'volatility': df_sorted['online_count_change'].std()
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        df = self.load_csv_data()
        
        if df is None or df.empty:
            return {"error": "No data available for analysis"}
        
        basic_stats = self.get_basic_stats(df)
        trends = self.analyze_trends(df)
        anomalies = self.detect_anomalies(df)
        growth_metrics = self.get_growth_metrics(df)
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'data_summary': basic_stats,
            'trends': {k: v for k, v in trends.items() if k != 'resampled_data'},
            'anomalies': {
                'count': len(anomalies),
                'details': anomalies[:10]  # Limit to first 10
            },
            'growth_metrics': growth_metrics
        }
        
        return report
    
    def export_analysis(self, output_file: str = None) -> str:
        """Export analysis results to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"{self.data_dir}/analysis_{timestamp}.json"
        
        report = self.generate_report()
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"Analysis exported to: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error exporting analysis: {e}")
            return None
    
    def print_summary(self) -> None:
        """Print a readable summary of the analysis"""
        report = self.generate_report()
        
        if "error" in report:
            print(f"Error: {report['error']}")
            return
        
        print("=== Reddit Monitor Analysis Report ===")
        
        summary = report['data_summary']
        print(f"\n📊 Data Summary:")
        print(f"  Total records: {summary['total_records']}")
        print(f"  Time range: {summary['time_range']['start']} to {summary['time_range']['end']}")
        print(f"  Duration: {summary['time_range']['duration']}")
        print(f"  Success rate: {summary['success_rate']:.1f}%")
        
        online_stats = summary['online_count_stats']
        print(f"\n👥 Online Count Statistics:")
        print(f"  Average: {online_stats['mean']:.1f}")
        print(f"  Median: {online_stats['median']:.1f}")
        print(f"  Min: {online_stats['min']:.0f}")
        print(f"  Max: {online_stats['max']:.0f}")
        print(f"  Standard deviation: {online_stats['std']:.1f}")
        
        trends = report['trends']
        if 'peak_hour' in trends:
            print(f"\n📈 Activity Patterns:")
            print(f"  Peak activity hour: {trends['peak_hour']}:00")
            print(f"  Lowest activity hour: {trends['lowest_hour']}:00")
        
        growth = report['growth_metrics']
        if growth:
            print(f"\n📈 Growth Metrics:")
            print(f"  Total change: {growth['total_change']:+.0f}")
            print(f"  Average change per measurement: {growth['avg_change_per_measurement']:+.1f}")
            print(f"  Biggest increase: +{growth['biggest_increase']:.0f}")
            print(f"  Biggest decrease: {growth['biggest_decrease']:.0f}")
            print(f"  Significant changes: {growth['significant_changes_count']}")
        
        anomalies = report['anomalies']
        if anomalies['count'] > 0:
            print(f"\n⚠️  Anomalies Detected: {anomalies['count']}")
            for anomaly in anomalies['details'][:3]:  # Show first 3
                print(f"  - {anomaly['timestamp']}: {anomaly['online_count']} users (z-score: {anomaly['z_score']:.1f})")
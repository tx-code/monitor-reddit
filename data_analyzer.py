import json
import os
from datetime import datetime
from collections import defaultdict

class DataAnalyzer:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        
    def get_all_data_files(self):
        """Get all data files sorted by timestamp"""
        try:
            files = [f for f in os.listdir(self.data_dir) if f.startswith('data_') and f.endswith('.json')]
            return sorted([os.path.join(self.data_dir, f) for f in files])
        except Exception as e:
            print(f"Error reading data directory: {e}")
            return []
    
    def load_data_file(self, filepath):
        """Load data from a JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None
    
    def analyze_changes(self):
        """Analyze changes over time"""
        files = self.get_all_data_files()
        if len(files) < 2:
            print("Need at least 2 data files to analyze changes")
            return
            
        changes = []
        prev_content_hash = None
        
        for filepath in files:
            data = self.load_data_file(filepath)
            if not data:
                continue
                
            content = data.get('content', '')
            content_hash = hash(content)
            
            if prev_content_hash is not None and content_hash != prev_content_hash:
                changes.append({
                    'timestamp': data.get('timestamp'),
                    'file': filepath,
                    'content_length': len(content)
                })
            
            prev_content_hash = content_hash
        
        print(f"Total changes detected: {len(changes)}")
        for change in changes:
            print(f"  - {change['timestamp']}: Content length {change['content_length']}")
    
    def show_latest_data(self):
        """Display information about the latest data"""
        files = self.get_all_data_files()
        if not files:
            print("No data files found")
            return
            
        latest_file = files[-1]
        data = self.load_data_file(latest_file)
        if not data:
            return
            
        print(f"Latest data from: {data.get('timestamp')}")
        print(f"Status code: {data.get('status_code')}")
        print(f"Content length: {len(data.get('content', ''))}")
        print(f"Response headers count: {len(data.get('headers', {}))}")
    
    def generate_report(self):
        """Generate a comprehensive report"""
        files = self.get_all_data_files()
        if not files:
            print("No data files found")
            return
            
        print("=== Reddit Monitor Data Analysis Report ===")
        print(f"Total monitoring sessions: {len(files)}")
        
        if files:
            first_data = self.load_data_file(files[0])
            last_data = self.load_data_file(files[-1])
            
            if first_data and last_data:
                first_time = datetime.fromisoformat(first_data['timestamp'])
                last_time = datetime.fromisoformat(last_data['timestamp'])
                duration = last_time - first_time
                
                print(f"Monitoring period: {first_time.strftime('%Y-%m-%d %H:%M')} to {last_time.strftime('%Y-%m-%d %H:%M')}")
                print(f"Total duration: {duration}")
        
        print("\n--- Latest Data ---")
        self.show_latest_data()
        
        print("\n--- Change Analysis ---")
        self.analyze_changes()

if __name__ == "__main__":
    analyzer = DataAnalyzer()
    analyzer.generate_report()
from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import threading
import time
from reddit_monitor import RedditMonitor
from data_analyzer import DataAnalyzer
from config_manager import ConfigManager

app = Flask(__name__)

# Global instances
monitor = None
monitor_thread = None
is_monitoring = False
config_manager = ConfigManager()

class WebMonitor(RedditMonitor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = {
            'running': False,
            'last_check': None,
            'total_checks': 0,
            'changes_detected': 0,
            'errors': 0,
            'start_time': None
        }
    
    def monitor_once_with_status(self):
        """Enhanced monitoring with status tracking"""
        self.status['last_check'] = datetime.now().isoformat()
        self.status['total_checks'] += 1
        
        try:
            data = self.fetch_website_data()
            if not data:
                self.status['errors'] += 1
                return
            
            has_changes = self.check_for_changes(data)
            if has_changes:
                self.status['changes_detected'] += 1
                saved_file = self.save_data(data)
                if saved_file:
                    self.logger.info(f"Data saved to: {saved_file}")
        except Exception as e:
            self.status['errors'] += 1
            self.logger.error(f"Monitor error: {e}")
    
    def start_monitoring_thread(self):
        """Start monitoring in background thread"""
        global is_monitoring
        is_monitoring = True
        self.status['running'] = True
        self.status['start_time'] = datetime.now().isoformat()
        
        while is_monitoring:
            self.monitor_once_with_status()
            if is_monitoring:  # Check again before sleeping
                time.sleep(self.interval)
        
        self.status['running'] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current monitoring status"""
    global monitor
    if not monitor:
        return jsonify({
            'running': False,
            'last_check': None,
            'total_checks': 0,
            'changes_detected': 0,
            'errors': 0,
            'start_time': None,
            'uptime': None
        })
    
    status = monitor.status.copy()
    if status['start_time']:
        start_time = datetime.fromisoformat(status['start_time'])
        uptime = str(datetime.now() - start_time)
        status['uptime'] = uptime
    
    return jsonify(status)

@app.route('/api/data')
def get_data():
    """Get monitoring data analysis"""
    try:
        analyzer = DataAnalyzer()
        files = analyzer.get_all_data_files()
        
        if not files:
            return jsonify({'error': 'No data files found'})
        
        # Get latest file info
        latest_file = files[-1]
        latest_data = analyzer.load_data_file(latest_file)
        
        result = {
            'total_files': len(files),
            'latest_timestamp': latest_data.get('timestamp') if latest_data else None,
            'latest_content_length': len(latest_data.get('content', '')) if latest_data else 0,
            'files': []
        }
        
        # Get info for recent files (last 10)
        for filepath in files[-10:]:
            data = analyzer.load_data_file(filepath)
            if data:
                result['files'].append({
                    'filename': os.path.basename(filepath),
                    'timestamp': data.get('timestamp'),
                    'content_length': len(data.get('content', '')),
                    'status_code': data.get('status_code')
                })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start monitoring"""
    global monitor, monitor_thread, is_monitoring, config_manager
    
    if is_monitoring:
        return jsonify({'error': 'Monitoring already running'})
    
    try:
        # Load current configuration
        config = config_manager.get_monitor_config()
        url = config.get('url', 'https://www.reddit.com/r/CNC/')
        interval = config_manager.get_interval_seconds()
        data_dir = config.get('data_directory', 'data')
        
        monitor = WebMonitor(url=url, interval=interval, data_dir=data_dir)
        monitor_thread = threading.Thread(target=monitor.start_monitoring_thread, daemon=True)
        monitor_thread.start()
        
        return jsonify({'success': True, 'message': 'Monitoring started'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring"""
    global is_monitoring
    
    if not is_monitoring:
        return jsonify({'error': 'Monitoring not running'})
    
    is_monitoring = False
    return jsonify({'success': True, 'message': 'Monitoring stopped'})

@app.route('/api/logs')
def get_logs():
    """Get recent log entries"""
    try:
        if os.path.exists('reddit_monitor.log'):
            with open('reddit_monitor.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            # Return last 50 lines
            recent_lines = lines[-50:] if len(lines) > 50 else lines
            return jsonify({'logs': [line.strip() for line in recent_lines]})
        else:
            return jsonify({'logs': []})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/config')
def get_config():
    """Get current configuration"""
    try:
        config = config_manager.get_config()
        predefined_urls = config_manager.get_predefined_urls()
        return jsonify({
            'config': config,
            'predefined_urls': predefined_urls
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'monitor' in data:
            monitor_config = data['monitor']
            url = monitor_config.get('url', '').strip()
            interval_minutes = monitor_config.get('interval_minutes')
            data_directory = monitor_config.get('data_directory', '').strip()
            
            if not url or not url.startswith(('http://', 'https://')):
                return jsonify({'error': 'URL必须是有效的HTTP/HTTPS地址'})
            
            if not isinstance(interval_minutes, (int, float)) or interval_minutes < 1:
                return jsonify({'error': '监控间隔必须大于0分钟'})
            
            if not data_directory:
                return jsonify({'error': '数据目录不能为空'})
        
        # Update configuration
        success = config_manager.update_config(data)
        if success:
            return jsonify({'success': True, 'message': '配置已保存'})
        else:
            return jsonify({'error': '保存配置失败'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/config/validate', methods=['POST'])
def validate_config():
    """Validate configuration"""
    try:
        data = request.get_json()
        
        # Create temporary config manager to validate
        temp_config = config_manager.get_config()
        temp_config.update(data)
        
        # Create temporary config manager for validation
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(temp_config, f)
            temp_file = f.name
        
        temp_manager = ConfigManager(temp_file)
        errors = temp_manager.validate_config()
        
        # Clean up temp file
        os.unlink(temp_file)
        
        if errors:
            return jsonify({'valid': False, 'errors': errors})
        else:
            return jsonify({'valid': True})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
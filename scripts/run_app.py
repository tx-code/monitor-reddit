#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reddit Monitor - Streamlit Application Launcher
Launch script for the Reddit online count monitoring system
"""

import os
import sys
import subprocess
from pathlib import Path

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

def get_project_root():
    """Get the project root directory"""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def setup_environment():
    """Setup Python path and environment"""
    project_root = get_project_root()
    
    # Add project root to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Change to project root directory
    os.chdir(project_root)
    
    return project_root

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        ('streamlit', 'streamlit'),
        ('pandas', 'pandas'), 
        ('plotly', 'plotly'),
        ('requests', 'requests'),
        ('bs4', 'beautifulsoup4')  # bs4 is the import name for beautifulsoup4
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: uv add " + " ".join(missing_packages))
        return False
    
    return True

def launch_streamlit():
    """Launch the Streamlit application"""
    project_root = setup_environment()
    
    if not check_dependencies():
        sys.exit(1)
    
    app_path = project_root / "src" / "ui" / "app.py"
    
    if not app_path.exists():
        print(f"❌ Application file not found: {app_path}")
        sys.exit(1)
    
    print("🚀 Starting Reddit Monitor Streamlit Application...")
    print(f"📂 Project root: {project_root}")
    print(f"📱 App path: {app_path}")
    
    # Launch Streamlit
    try:
        cmd = [
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ]
        
        print(f"🔧 Command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    launch_streamlit()
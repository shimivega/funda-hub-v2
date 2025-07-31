#!/usr/bin/env python3
"""
Initialization script for Funda App services
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_directories():
    """Create necessary directories"""
    directories = [
        'resources',
        'uploads',
        'services',
        'templates',
        'static'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")

def create_init_files():
    """Create __init__.py files for Python packages"""
    init_files = [
        'services/__init__.py'
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"✓ Created: {init_file}")

def setup_database():
    """Initialize the database"""
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
            print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")

def start_scheduler():
    """Start the resource scheduler"""
    try:
        from services.scheduler import resource_scheduler
        resource_scheduler.start_scheduler()
        print("✓ Resource scheduler started")
        return True
    except Exception as e:
        print(f"✗ Failed to start scheduler: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Initializing Funda App...")
    print("=" * 50)
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Create init files
    print("\n📄 Creating package files...")
    create_init_files()
    
    # Setup database
    print("\n🗄️ Setting up database...")
    setup_database()
    
    # Start scheduler
    print("\n⏰ Starting scheduler...")
    scheduler_started = start_scheduler()
    
    print("\n" + "=" * 50)
    print("✅ Funda App initialization complete!")
    print("\n📋 Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the application: python app.py")
    print("3. Open browser to: http://localhost:5000")
    
    if scheduler_started:
        print("4. Resource scheduler is running (weekly updates)")
    else:
        print("4. ⚠️ Resource scheduler failed to start")
    
    print("\n🔧 Admin features:")
    print("- Upload resources: /admin/resources")
    print("- Trigger manual scrape: Click 'Update Resources' button")
    print("- View all resources: /resources")

if __name__ == "__main__":
    main()

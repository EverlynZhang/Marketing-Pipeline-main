#!/usr/bin/env python3
"""
Dashboard launcher script
"""

if __name__ == '__main__':
    from dashboard.app import app
    from config import Config
    import os
    
    config = Config()
    config.setup_directories()
    
    print("\n" + "="*70)
    print("🚀 NovaMind Marketing Pipeline Dashboard")
    print("="*70)
    print(f"\n📊 Access at: http://localhost:5000")
    print(f"📁 Data: {os.path.abspath(config.DATA_DIR)}")
    print(f"\n💡 Press CTRL+C to stop\n")
    
    app.run(debug=True, port=5000, use_reloader=False)
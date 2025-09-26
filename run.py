#!/usr/bin/env python3
"""
Advanced Attendance System - Main Runner
System managed and powered by Lord rahl
"""

from server import run_server
from config import Config

if __name__ == '__main__':
    print("🎓 Advanced Attendance System Starting...")
    print(f"💾 Database: {Config.DATABASE_NAME}")
    print(f"🌐 Server: http://{Config.SERVER_HOST}:{Config.SERVER_PORT}")
    print(f"⚡ {Config.SYSTEM_MANAGER}")
    print("\n" + "="*50)
    
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

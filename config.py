# System Configuration
class Config:
    SECRET_KEY = "lord_rahL_advanced_system_2024"
    DATABASE_NAME = "attendance_system.db"
    QR_CODE_TIMEOUT = 300  # 5 minutes
    SESSION_TIMEOUT = 3600  # 1 hour
    SERVER_HOST = "localhost"
    SERVER_PORT = 8000
    SYSTEM_MANAGER = "System managed and powered by Lord rahl"
    
    # Security settings
    MAX_LOGIN_ATTEMPTS = 3
    PASSWORD_MIN_LENGTH = 6

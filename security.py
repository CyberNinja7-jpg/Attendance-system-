import hashlib
import time
from datetime import datetime, timedelta
from config import Config

class AdvancedSecurity:
    def __init__(self):
        self.active_qr_sessions = {}
        self.suspicious_activities = []
    
    def generate_secure_qr_data(self, class_id):
        """Generate secure QR code data with timestamp"""
        timestamp = int(time.time())
        random_token = hashlib.sha256(f"{class_id}{timestamp}{Config.SECRET_KEY}".encode()).hexdigest()[:16]
        
        qr_data = {
            'class_id': class_id,
            'token': random_token,
            'created_at': timestamp,
            'expires_at': timestamp + Config.QR_CODE_TIMEOUT
        }
        
        # Store session
        session_key = f"{class_id}_{random_token}"
        self.active_qr_sessions[session_key] = qr_data
        
        return f"ATTEND:{class_id}:{random_token}:{timestamp}"
    
    def validate_qr_data(self, qr_data, student_ip=""):
        """Validate QR code data with security checks"""
        try:
            if not qr_data.startswith("ATTEND:"):
                return None, "Invalid QR format"
            
            parts = qr_data.split(':')
            if len(parts) != 4:
                return None, "Malformed QR data"
            
            class_id, token, timestamp = int(parts[1]), parts[2], int(parts[3])
            session_key = f"{class_id}_{token}"
            
            # Check if session exists
            if session_key not in self.active_qr_sessions:
                return None, "Invalid or expired QR session"
            
            session = self.active_qr_sessions[session_key]
            
            # Check expiration
            if time.time() > session['expires_at']:
                del self.active_qr_sessions[session_key]
                return None, "QR code has expired"
            
            # Check timestamp validity
            if abs(time.time() - timestamp) > Config.QR_CODE_TIMEOUT:
                self.record_suspicious_activity(f"Timestamp manipulation detected from IP: {student_ip}")
                return None, "Invalid timestamp"
            
            return session, "Valid"
            
        except Exception as e:
            self.record_suspicious_activity(f"QR validation error: {str(e)}")
            return None, "Validation error"
    
    def record_suspicious_activity(self, activity):
        """Record security events for monitoring"""
        self.suspicious_activities.append({
            'timestamp': datetime.now().isoformat(),
            'activity': activity,
            'ip': '127.0.0.1'  # In production, get from request
        })
        
        # Keep only last 100 activities
        self.suspicious_activities = self.suspicious_activities[-100:]
    
    def get_security_report(self):
        """Generate security report"""
        return {
            'total_suspicious_activities': len(self.suspicious_activities),
            'active_qr_sessions': len(self.active_qr_sessions),
            'recent_activities': self.suspicious_activities[-10:]
        }
    
    def cleanup_expired_sessions(self):
        """Clean up expired QR sessions"""
        current_time = time.time()
        expired_sessions = [
            key for key, session in self.active_qr_sessions.items()
            if current_time > session['expires_at']
        ]
        
        for key in expired_sessions:
            del self.active_qr_sessions[key]

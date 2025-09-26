import hashlib
import time
from config import Config

class AdvancedAuth:
    def __init__(self):
        self.sessions = {}
        self.login_attempts = {}
        self.session_timeout = Config.SESSION_TIMEOUT
    
    def create_session(self, user_id, username, role):
        """Create secure session with fingerprinting"""
        session_id = hashlib.sha256(
            f"{user_id}{username}{role}{time.time()}".encode()
        ).hexdigest()[:32]
        
        self.sessions[session_id] = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'created_at': time.time(),
            'last_activity': time.time()
        }
        
        # Cleanup old sessions
        self.cleanup_sessions()
        return session_id
    
    def verify_session(self, session_id):
        """Verify session with activity tracking"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Update last activity
            session['last_activity'] = time.time()
            
            # Check if session expired
            if time.time() - session['created_at'] > self.session_timeout:
                del self.sessions[session_id]
                return None
            
            return session
        return None
    
    def logout(self, session_id):
        """Logout user and clear session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def record_login_attempt(self, username, success):
        """Track login attempts for security"""
        if username not in self.login_attempts:
            self.login_attempts[username] = []
        
        self.login_attempts[username].append({
            'timestamp': time.time(),
            'success': success
        })
        
        # Keep only last 10 attempts
        self.login_attempts[username] = self.login_attempts[username][-10:]
    
    def is_account_locked(self, username):
        """Check if account is temporarily locked"""
        if username not in self.login_attempts:
            return False
        
        recent_failures = [
            attempt for attempt in self.login_attempts[username][-Config.MAX_LOGIN_ATTEMPTS:]
            if not attempt['success']
        ]
        
        return len(recent_failures) >= Config.MAX_LOGIN_ATTEMPTS
    
    def cleanup_sessions(self):
        """Clean up expired sessions"""
        current_time = time.time()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if current_time - session['created_at'] > self.session_timeout
        ]
        
        for sid in expired_sessions:
            del self.sessions[sid]

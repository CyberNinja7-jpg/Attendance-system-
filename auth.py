import hashlib

class Auth:
    def __init__(self):
        self.sessions = {}  # Simple session storage
    
    def create_session(self, user_id, username, role):
        """Create a simple session"""
        session_id = hashlib.sha256(f"{user_id}{username}{role}".encode()).hexdigest()[:16]
        self.sessions[session_id] = {
            'user_id': user_id,
            'username': username,
            'role': role
        }
        return session_id
    
    def verify_session(self, session_id):
        """Verify session exists"""
        return self.sessions.get(session_id)

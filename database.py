import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from config import Config

class AdvancedDatabase:
    def __init__(self, db_name=Config.DATABASE_NAME):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Get database connection with error handling"""
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row  # Enable dictionary-like access
            return conn
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            c = conn.cursor()
            
            # Users table
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )''')
            
            # Classes table
            c.execute('''CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT UNIQUE,
                teacher_id INTEGER,
                schedule TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users (id)
            )''')
            
            # Attendance sessions table
            c.execute('''CREATE TABLE IF NOT EXISTS attendance_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER,
                session_date TEXT,
                start_time TEXT,
                end_time TEXT,
                secret_token TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (class_id) REFERENCES classes (id)
            )''')
            
            # Attendance records table
            c.execute('''CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                student_id INTEGER,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                device_info TEXT,
                status TEXT DEFAULT 'present',
                FOREIGN KEY (session_id) REFERENCES attendance_sessions (id),
                FOREIGN KEY (student_id) REFERENCES users (id),
                UNIQUE(session_id, student_id)
            )''')
            
            # System logs table
            c.execute('''CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                message TEXT,
                user_id INTEGER,
                ip_address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Insert default data
            self._create_default_data(c)
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            return False
        finally:
            conn.close()
    
    def _create_default_data(self, cursor):
        """Create default users and classes"""
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            return
        
        # Create default teacher
        teacher_hash = hashlib.sha256("teacher123".encode()).hexdigest()
        cursor.execute('''INSERT INTO users (username, password_hash, role, full_name) 
                         VALUES (?, ?, ?, ?)''',
                     ('teacher1', teacher_hash, 'teacher', 'Professor John Doe'))
        
        # Create default students
        students = [
            ('student1', 'student123', 'student', 'Alice Johnson'),
            ('student2', 'student123', 'student', 'Bob Smith'),
            ('student3', 'student123', 'student', 'Carol Davis')
        ]
        
        for username, password, role, full_name in students:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('''INSERT INTO users (username, password_hash, role, full_name) 
                             VALUES (?, ?, ?, ?)''',
                         (username, password_hash, role, full_name))
        
        # Create default class
        cursor.execute('''INSERT INTO classes (name, code, teacher_id, schedule) 
                         VALUES (?, ?, ?, ?)''',
                     ('Advanced Computer Science', 'CS101', 1, 'Mon-Wed-Fri 10:00 AM'))
    
    def verify_user(self, username, password):
        """Verify user credentials with security"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''SELECT * FROM users 
                             WHERE username = ? AND password_hash = ? AND is_active = 1''',
                         (username, password_hash))
            
            user = cursor.fetchone()
            return dict(user) if user else None
            
        except sqlite3.Error as e:
            print(f"User verification error: {e}")
            return None
        finally:
            conn.close()
    
    def create_attendance_session(self, class_id, secret_token):
        """Create new attendance session"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            now = datetime.now()
            
            cursor.execute('''INSERT INTO attendance_sessions 
                            (class_id, session_date, start_time, secret_token) 
                            VALUES (?, ?, ?, ?)''',
                         (class_id, now.date().isoformat(), now.time().isoformat(), secret_token))
            
            session_id = cursor.lastrowid
            conn.commit()
            
            # Log the activity
            self.log_activity('INFO', f"Attendance session created: {session_id}", 1)
            
            return session_id
            
        except sqlite3.Error as e:
            print(f"Session creation error: {e}")
            return None
        finally:
            conn.close()
    
    def mark_attendance(self, session_id, student_id, ip_address="", device_info=""):
        """Mark student attendance with anti-cheating measures"""
        conn = self.get_connection()
        if not conn:
            return False, "Database error"
        
        try:
            cursor = conn.cursor()
            
            # Check if already attended
            cursor.execute('''SELECT * FROM attendance_records 
                             WHERE session_id = ? AND student_id = ?''',
                         (session_id, student_id))
            
            if cursor.fetchone():
                return False, "Already attended this session"
            
            # Check if session is active
            cursor.execute('''SELECT * FROM attendance_sessions 
                             WHERE id = ? AND is_active = 1''',
                         (session_id,))
            
            session = cursor.fetchone()
            if not session:
                return False, "Session not active or expired"
            
            # Record attendance
            cursor.execute('''INSERT INTO attendance_records 
                            (session_id, student_id, ip_address, device_info) 
                            VALUES (?, ?, ?, ?)''',
                         (session_id, student_id, ip_address, device_info))
            
            conn.commit()
            
            # Log the activity
            self.log_activity('INFO', f"Attendance marked: student {student_id} for session {session_id}", student_id)
            
            return True, "Attendance marked successfully"
            
        except sqlite3.Error as e:
            print(f"Attendance marking error: {e}")
            return False, "Database error"
        finally:
            conn.close()
    
    def get_attendance_report(self, class_id):
        """Generate comprehensive attendance report"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''SELECT u.username, u.full_name, 
                             COUNT(DISTINCT ar.session_id) as sessions_attended,
                             COUNT(DISTINCT ass.id) as total_sessions,
                             (COUNT(DISTINCT ar.session_id) * 100.0 / COUNT(DISTINCT ass.id)) as attendance_rate
                             FROM users u
                             CROSS JOIN attendance_sessions ass
                             LEFT JOIN attendance_records ar ON ar.session_id = ass.id AND ar.student_id = u.id
                             WHERE u.role = 'student' AND ass.class_id = ?
                             GROUP BY u.id, u.username, u.full_name''',
                         (class_id,))
            
            report = [dict(row) for row in cursor.fetchall()]
            return report
            
        except sqlite3.Error as e:
            print(f"Report generation error: {e}")
            return []
        finally:
            conn.close()
    
    def log_activity(self, level, message, user_id=None):
        """Log system activities"""
        conn = self.get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO system_logs (level, message, user_id, ip_address) 
                             VALUES (?, ?, ?, ?)''',
                         (level, message, user_id, '127.0.0.1'))
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            conn.close()

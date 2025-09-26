import sqlite3
import hashlib
import os
from datetime import datetime

class Database:
    def __init__(self, db_name="attendance.db"):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # Create tables
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY, username TEXT UNIQUE, 
                     password_hash TEXT, role TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS classes
                    (id INTEGER PRIMARY KEY, name TEXT, teacher_id INTEGER)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS attendance_sessions
                    (id INTEGER PRIMARY KEY, class_id INTEGER, date TEXT, 
                     secret_code TEXT, created_at TEXT, is_active BOOLEAN)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS attendance_records
                    (id INTEGER PRIMARY KEY, session_id INTEGER, 
                     student_id INTEGER, timestamp TEXT)''')
        
        # Add sample data if empty
        if not c.execute("SELECT * FROM users").fetchone():
            self.add_user('teacher1', 'password123', 'teacher')
            self.add_user('student1', 'password123', 'student')
            c.execute("INSERT INTO classes (name, teacher_id) VALUES ('Computer Science 101', 1)")
        
        conn.commit()
        conn.close()
    
    def add_user(self, username, password, role):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # Simple password hashing
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                     (username, password_hash, role))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # User already exists
        
        conn.close()
    
    def verify_user(self, username, password):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", 
                 (username, password_hash))
        user = c.fetchone()
        conn.close()
        
        return user
    
    def create_attendance_session(self, class_id, secret_code):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        now = datetime.now().isoformat()
        c.execute('''INSERT INTO attendance_sessions 
                    (class_id, date, secret_code, created_at, is_active) 
                    VALUES (?, ?, ?, ?, ?)''',
                 (class_id, now.split('T')[0], secret_code, now, True))
        
        session_id = c.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def mark_attendance(self, session_id, student_id):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # Check if already attended
        c.execute("SELECT * FROM attendance_records WHERE session_id=? AND student_id=?",
                 (session_id, student_id))
        if c.fetchone():
            conn.close()
            return False  # Already attended
        
        # Mark attendance
        timestamp = datetime.now().isoformat()
        c.execute("INSERT INTO attendance_records (session_id, student_id, timestamp) VALUES (?, ?, ?)",
                 (session_id, student_id, timestamp))
        
        conn.commit()
        conn.close()
        return True

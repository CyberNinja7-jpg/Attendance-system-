from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse
from database import Database
from qr_generator import generate_secret_code, generate_simple_qr, parse_qr_data
from auth import Auth
import json

class AttendanceHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = Database()
        self.auth = Auth()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.serve_login()
        elif path == '/teacher':
            self.serve_teacher_dashboard()
        elif path == '/student':
            self.serve_student_dashboard()
        elif path.startswith('/generate_qr/'):
            class_id = int(path.split('/')[-1])
            self.generate_qr(class_id)
        else:
            self.send_error(404, "Page not found")
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        if self.path == '/login':
            self.handle_login(post_data)
        elif self.path == '/mark_attendance':
            self.handle_mark_attendance(post_data)
        else:
            self.send_error(404)
    
    def serve_login(self):
        html = """
        <html>
        <head><title>Attendance System</title></head>
        <body>
            <h2>Login</h2>
            <form method="POST" action="/login">
                <input type="text" name="username" placeholder="Username" required><br>
                <input type="password" name="password" placeholder="Password" required><br>
                <button type="submit">Login</button>
            </form>
            <p><strong>Demo:</strong> teacher1/password123 or student1/password123</p>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def handle_login(self, post_data):
        params = urlparse.parse_qs(post_data)
        username = params.get('username', [''])[0]
        password = params.get('password', [''])[0]
        
        user = self.db.verify_user(username, password)
        
        if user:
            session_id = self.auth.create_session(user[0], user[1], user[3])
            
            # Set cookie and redirect
            self.send_response(302)
            if user[3] == 'teacher':
                self.send_header('Location', '/teacher')
            else:
                self.send_header('Location', '/student')
            self.send_header('Set-Cookie', f'session_id={session_id}')
            self.end_headers()
        else:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Login failed")
    
    def serve_teacher_dashboard(self):
        # Verify session
        if not self.verify_session():
            self.redirect_login()
            return
        
        html = """
        <html>
        <head><title>Teacher Dashboard</title></head>
        <body>
            <h2>Teacher Dashboard</h2>
            <div>
                <h3>Computer Science 101</h3>
                <a href="/generate_qr/1">Generate QR Code for Today</a>
                <p><em>QR codes are active for 5 minutes</em></p>
            </div>
            <br>
            <a href="/">Logout</a>
        </body>
        </html>
        """
        self.send_html(html)
    
    def generate_qr(self, class_id):
        secret_code = generate_secret_code()
        session_id = self.db.create_attendance_session(class_id, secret_code)
        
        qr_data = f"CLASS:{class_id}:CODE:{secret_code}"
        simple_qr = generate_simple_qr(qr_data)
        
        html = f"""
        <html>
        <body>
            <h2>QR Code for Attendance</h2>
            <div style='border: 2px solid black; padding: 20px; display: inline-block;'>
                <pre>{simple_qr}</pre>
            </div>
            <p><strong>Data:</strong> {qr_data}</p>
            <p>Students should scan this code within 5 minutes</p>
            <a href="/teacher">Back to Dashboard</a>
        </body>
        </html>
        """
        self.send_html(html)
    
    def handle_mark_attendance(self, post_data):
        data = json.loads(post_data)
        qr_data = data.get('qr_data', '')
        
        # Parse QR data (simple format: CLASS:1:CODE:abc123)
        if qr_data.startswith("CLASS:") and "CODE:" in qr_data:
            parts = qr_data.split(':')
            class_id = int(parts[1])
            secret_code = parts[3]
            
            # In a real system, you'd verify the session is active and not expired
            # For now, we'll just mark attendance
            success = self.db.mark_attendance(1, 2)  # Using fixed IDs for demo
            
            response = {'success': success, 'message': 'Attendance recorded!'}
        else:
            response = {'success': False, 'error': 'Invalid QR code'}
        
        self.send_json(response)
    
    # Helper methods
    def verify_session(self):
        cookie = self.headers.get('Cookie', '')
        if 'session_id=' in cookie:
            session_id = cookie.split('session_id=')[1].split(';')[0]
            return self.auth.verify_session(session_id)
        return False
    
    def redirect_login(self):
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def run_server():
    server = HTTPServer(('localhost', 8000), AttendanceHandler)
    print("Server running on http://localhost:8000")
    server.serve_forever()

if __name__ == '__main__':
    run_server()

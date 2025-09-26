from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse
import json
import time
from database import AdvancedDatabase
from auth import AdvancedAuth
from security import AdvancedSecurity
from config import Config

class AdvancedAttendanceHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = AdvancedDatabase()
        self.auth = AdvancedAuth()
        self.security = AdvancedSecurity()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse.urlparse(self.path)
            path = parsed_path.path
            
            routes = {
                '/': self.serve_login,
                '/dashboard': self.serve_dashboard,
                '/teacher': self.serve_teacher_dashboard,
                '/student': self.serve_student_dashboard,
                '/scanner': self.serve_qr_scanner,
                '/report': self.serve_attendance_report,
                '/security': self.serve_security_report,
                '/logout': self.handle_logout
            }
            
            if path in routes:
                routes[path]()
            elif path.startswith('/generate_qr/'):
                class_id = int(path.split('/')[-1])
                self.generate_qr_code(class_id)
            else:
                self.send_error(404, "Page not found")
                
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            if self.path == '/login':
                self.handle_login(post_data)
            elif self.path == '/mark_attendance':
                self.handle_mark_attendance(post_data)
            elif self.path == '/create_session':
                self.handle_create_session(post_data)
            else:
                self.send_error(404)
                
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def serve_login(self):
        """Serve login page"""
        html = self.render_template('login.html')
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_dashboard(self):
        """Serve appropriate dashboard based on user role"""
        session = self.get_current_session()
        if not session:
            self.redirect_login()
            return
        
        if session['role'] == 'teacher':
            self.serve_teacher_dashboard()
        else:
            self.serve_student_dashboard()
    
    def serve_teacher_dashboard(self):
        """Serve teacher dashboard"""
        session = self.get_current_session()
        if not session or session['role'] != 'teacher':
            self.redirect_login()
            return
        
        html = f"""
        <div class="card">
            <h2>👨‍🏫 Teacher Dashboard</h2>
            <p>Welcome, {session['username']}!</p>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-top: 2rem;">
                <div class="card">
                    <h3>📊 Quick Actions</h3>
                    <a href="/generate_qr/1" class="btn">Generate QR Code</a>
                    <a href="/report" class="btn">View Reports</a>
                    <a href="/security" class="btn">Security Monitor</a>
                </div>
                
                <div class="card">
                    <h3>ℹ️ System Info</h3>
                    <p>Active Sessions: {len(self.security.active_qr_sessions)}</p>
                    <p>Total Students: 3</p>
                    <p>Today's Date: {time.strftime('%Y-%m-%d')}</p>
                </div>
            </div>
        </div>
        """
        
        full_html = self.render_template('base.html', content=html, title="Teacher Dashboard")
        self.send_html(full_html)
    
    def serve_qr_scanner(self):
        """Serve QR scanner interface"""
        html = """
        <div class="card">
            <h2>📱 QR Code Scanner</h2>
            <p>Enter the QR code data displayed in class:</p>
            
            <input type="text" id="qrInput" placeholder="Paste QR code data here" 
                   style="width: 100%; padding: 12px; margin: 1rem 0; border: 1px solid #ddd; border-radius: 5px;">
            
            <button onclick="submitAttendance()" class="btn">Mark Attendance</button>
            
            <div id="result" style="margin-top: 1rem;"></div>
        </div>
        
        <script>
            async function submitAttendance() {{
                const qrData = document.getElementById('qrInput').value;
                const resultDiv = document.getElementById('result');
                
                if (!qrData) {{
                    resultDiv.innerHTML = '<div class="error">Please enter QR code data</div>';
                    return;
                }}
                
                try {{
                    const response = await fetch('/mark_attendance', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ qr_data: qrData }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        resultDiv.innerHTML = '<div class="success">✅ ' + data.message + '</div>';
                        document.getElementById('qrInput').value = '';
                    }} else {{
                        resultDiv.innerHTML = '<div class="error">❌ ' + data.error + '</div>';
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = '<div class="error">❌ Network error</div>';
                }}
            }}
            
            // Enter key support
            document.getElementById('qrInput').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') submitAttendance();
            }});
        </script>
        """
        
        full_html = self.render_template('base.html', content=html, title="QR Scanner")
        self.send_html(full_html)
    
    def generate_qr_code(self, class_id):
        """Generate and display QR code"""
        session = self.get_current_session()
        if not session or session['role'] != 'teacher':
            self.redirect_login()
            return
        
        qr_data = self.security.generate_secure_qr_data(class_id)
        
        html = f"""
        <div class="card">
            <h2>📲 Attendance QR Code</h2>
            <p>Display this code in class. It will expire in 5 minutes.</p>
            
            <div style="text-align: center; margin: 2rem 0;">
                <div style="border: 3px solid #333; padding: 2rem; display: inline-block; background: white;">
                    <div style="font-family: monospace; font-size: 18px; letter-spacing: 2px;">
                        {qr_data}
                    </div>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 5px;">
                <strong>QR Data:</strong> <code>{qr_data}</code><br>
                <strong>Expires:</strong> {time.strftime('%H:%M:%S', time.localtime(time.time() + 300))}
            </div>
            
            <a href="/teacher" class="btn">Back to Dashboard</a>
        </div>
        """
        
        full_html = self.render_template('base.html', content=html, title="QR Code")
        self.send_html(full_html)
    
    def handle_mark_attendance(self, post_data):
        """Handle attendance marking request"""
        try:
            data = json.loads(post_data)
            qr_data = data.get('qr_data', '')
            
            # Validate QR data
            session, message = self.security.validate_qr_data(qr_data, self.get_client_ip())
            
            if not session:
                response = {'success': False, 'error': message}
            else:
                # Get current student session
                student_session = self.get_current_session()
                if not student_session or student_session['role'] != 'student':
                    response = {'success': False, 'error': 'Student authentication required'}
                else:
                    # Mark attendance
                    success, message = self.db.mark_attendance(
                        session['class_id'],  # This should be session ID in real implementation
                        student_session['user_id'],
                        self.get_client_ip(),
                        self.headers.get('User-Agent', '')
                    )
                    response = {'success': success, 'message': message}
            
        except Exception as e:
            response = {'success': False, 'error': f'System error: {str(e)}'}
        
        self.send_json(response)
    
    def serve_attendance_report(self):
        """Serve attendance reports"""
        session = self.get_current_session()
        if not session or session['role'] != 'teacher':
            self.redirect_login()
            return
        
        report = self.db.get_attendance_report(1)  # Class ID 1 for demo
        
        html = """
        <div class="card">
            <h2>📊 Attendance Report</h2>
            <p>Computer Science 101 - Overall Attendance</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Student</th>
                        <th>Full Name</th>
                        <th>Sessions Attended</th>
                        <th>Total Sessions</th>
                        <th>Attendance Rate</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for student in report:
            html += f"""
                    <tr>
                        <td>{student['username']}</td>
                        <td>{student['full_name']}</td>
                        <td style="text-align: center;">{student['sessions_attended']}</td>
                        <td style="text-align: center;">{student['total_sessions']}</td>
                        <td style="text-align: center;"><strong>{student['attendance_rate']:.1f}%</strong></td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
            
            <a href="/teacher" class="btn">Back to Dashboard</a>
        </div>
        """
        
        full_html = self.render_template('base.html', content=html, title="Attendance Report")
        self.send_html(full_html)
    
    # Helper methods
    def get_current_session(self):
        """Get current user session from cookies"""
        cookie = self.headers.get('Cookie', '')
        if 'session_id=' in cookie:
            session_id = cookie.split('session_id=')[1].split(';')[0]
            return self.auth.verify_session(session_id)
        return None
    
    def get_client_ip(self):
        """Get client IP address"""
        return self.headers.get('X-Forwarded-For', self.headers.get('X-Real-IP', '127.0.0.1'))
    
    def redirect_login(self):
        """Redirect to login page"""
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
    
    def send_html(self, html):
        """Send HTML response"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def render_template(self, template_name, **context):
        """Simple template rendering"""
        base_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial; margin: 0; padding: 20px; background: #f5f5f5; }}
                .header {{ background: #2c3e50; color: white; padding: 1rem; border-radius: 5px; }}
                .card {{ background: white; padding: 2rem; margin: 1rem 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .btn {{ background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                .footer {{ text-align: center; margin-top: 2rem; color: #7f8c8d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎓 Advanced Attendance System</h1>
            </div>
            
            <div class="container">
                {content}
            </div>
            
            <div class="footer">
                <p>{system_manager}</p>
            </div>
        </body>
        </html>
        """.format(
            title=context.get('title', 'Advanced Attendance System'),
            content=context.get('content', ''),
            system_manager=Config.SYSTEM_MANAGER
        )
        return base_html

def run_server():
    """Start the advanced attendance server"""
    server = HTTPServer((Config.SERVER_HOST, Config.SERVER_PORT), AdvancedAttendanceHandler)
    print(f"🚀 Advanced Attendance System running on http://{Config.SERVER_HOST}:{Config.SERVER_PORT}")
    print(f"📝 {Config.SYSTEM_MANAGER}")
    print("\nDemo Accounts:")
    print("Teacher: teacher1 / teacher123")
    print("Student: student1 / student123")
    server.serve_forever()

if __name__ == '__main__':
    run_server()

// Advanced Attendance System - Main JavaScript
// System managed and powered by Lord rahl

class AttendanceSystem {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkSession();
        this.initializeComponents();
    }

    setupEventListeners() {
        // Form submissions
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });

        // QR scanner functionality
        this.setupQRScanner();

        // Real-time updates
        this.startRealTimeUpdates();

        // Print functionality
        this.setupPrintFunctionality();
    }

    handleFormSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Show loading state
        if (submitBtn) {
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Processing...';
            submitBtn.disabled = true;
        }

        this.submitForm(form)
            .finally(() => {
                if (submitBtn) {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }
            });
    }

    async submitForm(form) {
        const formData = new FormData(form);
        const action = form.getAttribute('action');
        const method = form.getAttribute('method') || 'POST';

        try {
            const response = await fetch(action, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification(result.message, 'success');
                if (result.redirect) {
                    setTimeout(() => {
                        window.location.href = result.redirect;
                    }, 1500);
                }
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
            console.error('Form submission error:', error);
        }
    }

    setupQRScanner() {
        const qrInput = document.getElementById('qrInput');
        if (qrInput) {
            // Auto-focus and select all text on focus
            qrInput.addEventListener('focus', function() {
                this.select();
            });

            // Handle paste events
            qrInput.addEventListener('paste', function(e) {
                setTimeout(() => {
                    this.dispatchEvent(new Event('input', { bubbles: true }));
                }, 10);
            });

            // Auto-submit on valid QR code detection
            qrInput.addEventListener('input', this.debounce(function(e) {
                const value = e.target.value.trim();
                if (value.length > 10 && value.includes('ATTEND:')) {
                    this.submitAttendance(value);
                }
            }, 500));
        }
    }

    async submitAttendance(qrData) {
        try {
            const response = await fetch('/mark_attendance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ qr_data: qrData })
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('✅ Attendance marked successfully!', 'success');
                
                // Clear input and show success animation
                const qrInput = document.getElementById('qrInput');
                if (qrInput) {
                    qrInput.value = '';
                    qrInput.focus();
                }

                // Add visual feedback
                this.animateSuccess();
            } else {
                this.showNotification('❌ ' + result.error, 'error');
            }
        } catch (error) {
            this.showNotification('❌ Network error. Please try again.', 'error');
        }
    }

    animateSuccess() {
        const scannerSection = document.querySelector('.scanner-input') || document.body;
        const successElem = document.createElement('div');
        successElem.innerHTML = '✅';
        successElem.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 4rem;
            z-index: 1000;
            animation: bounce 0.5s ease-in-out;
        `;
        
        scannerSection.appendChild(successElem);
        
        setTimeout(() => {
            successElem.remove();
        }, 1000);
    }

    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.system-notification');
        existingNotifications.forEach(notif => notif.remove());

        const notification = document.createElement('div');
        notification.className = `system-notification alert alert-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            min-width: 300px;
            animation: slideInRight 0.3s ease-out;
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    checkSession() {
        // Check if user session is still valid
        setInterval(async () => {
            try {
                const response = await fetch('/check_session');
                const result = await response.json();
                
                if (!result.valid) {
                    this.showNotification('Session expired. Please login again.', 'warning');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                }
            } catch (error) {
                console.error('Session check failed:', error);
            }
        }, 300000); // Check every 5 minutes
    }

    startRealTimeUpdates() {
        // Simulate real-time updates for demo
        if (document.querySelector('.stats-grid')) {
            setInterval(() => {
                this.updateLiveStats();
            }, 30000);
        }
    }

    updateLiveStats() {
        const stats = document.querySelectorAll('.stat-number');
        stats.forEach(stat => {
            const current = parseInt(stat.textContent);
            if (!isNaN(current)) {
                const change = Math.random() * 2 - 1; // Random small change
                const newValue = Math.max(0, current + change);
                stat.textContent = Math.round(newValue);
            }
        });
    }

    setupPrintFunctionality() {
        // Add print styles dynamically
        const printStyle = document.createElement('style');
        printStyle.textContent = `
            @media print {
                .btn, .header, .footer { display: none !important; }
                .card { box-shadow: none !important; border: 1px solid #000 !important; }
                body { background: white !important; }
            }
        `;
        document.head.appendChild(printStyle);
    }

    initializeComponents() {
        // Initialize tooltips
        this.initTooltips();
        
        // Initialize charts if Chart.js is available
        this.initCharts();
        
        // Add CSS animations
        this.addAnimations();
    }

    initTooltips() {
        // Simple tooltip implementation
        const elements = document.querySelectorAll('[title]');
        elements.forEach(el => {
            el.addEventListener('mouseenter', this.showTooltip);
            el.addEventListener('mouseleave', this.hideTooltip);
        });
    }

    showTooltip(e) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = this.getAttribute('title');
        tooltip.style.cssText =

import random
import string

def generate_secret_code(length=16):
    """Generate a random secret code for QR"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_simple_qr(data):
    """Create a simple text-based QR representation"""
    # For demo purposes, we'll just return the data
    # In a real system, you'd generate an actual QR image
    return f"QR_CODE:{data}"

def parse_qr_data(qr_data):
    """Parse QR code data"""
    if qr_data.startswith("QR_CODE:"):
        return qr_data[8:]  # Remove "QR_CODE:" prefix
    return None

"""
File upload utilities for handling image file uploads with validation
"""
import os
from datetime import datetime
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
UPLOAD_FOLDER = 'frontend/public/uploads'


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload_file(file):
    """
    Save uploaded file with timestamp-based name.

    Args:
        file: Werkzeug FileStorage object

    Returns:
        str: Relative path (e.g., '/uploads/logo-1234567890.png')

    Raises:
        ValueError: If file type is not allowed or file is invalid
    """
    if not file or file.filename == '':
        return None

    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Create uploads folder if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Generate filename with timestamp
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    base_filename = secure_filename(file.filename).rsplit('.', 1)[0]
    new_filename = f"{base_filename}-{timestamp}.{ext}"

    filepath = os.path.join(UPLOAD_FOLDER, new_filename)
    file.save(filepath)

    # Return relative path for database storage
    return f'/uploads/{new_filename}'

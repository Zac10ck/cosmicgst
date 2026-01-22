# PythonAnywhere WSGI Configuration
# Copy this content to: /var/www/cosmicsurgical_pythonanywhere_com_wsgi.py

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add application to path
path = '/home/cosmicsurgical/gst-billing-web/web'
if path not in sys.path:
    sys.path.insert(0, path)

# Load environment variables from .env file
env_path = Path(path) / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Set environment variables (fallback if .env doesn't load)
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('SECRET_KEY', 'change-this-to-a-secure-key')

# Import the Flask application
from wsgi import app as application

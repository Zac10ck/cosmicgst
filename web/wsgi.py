"""WSGI entry point for GST Billing Web Application.

For PythonAnywhere deployment:
1. Set the source code directory to: /home/cosmicsurgical/gst-billing/web
2. Set the WSGI configuration file to point to this file
3. Set environment variables in the WSGI config:
   - FLASK_ENV=production
   - SECRET_KEY=<your-secret-key>
   - DATABASE_URL=mysql+mysqlconnector://user:pass@host/dbname
"""
import os
import sys

# Add the project directory to the Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import the Flask app factory
from app import create_app

# Create the application instance
# The environment is determined by FLASK_ENV environment variable
# Default is 'development' for local, set to 'production' on PythonAnywhere
app = create_app()

# Alias for compatibility (PythonAnywhere uses 'application')
application = app

# For local development with `python wsgi.py`
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

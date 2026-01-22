#!/bin/bash
# Quick update script for PythonAnywhere
# Run this to pull latest changes and restart

set -e

PA_USERNAME="cosmicsurgical"
APP_DIR="/home/${PA_USERNAME}/gst-billing-web"
WEB_DIR="${APP_DIR}/web"
VENV_NAME="billing-env"

echo "Updating GST Billing..."

# Activate virtualenv
source "/home/${PA_USERNAME}/.virtualenvs/${VENV_NAME}/bin/activate"

# Pull latest code
cd "$APP_DIR"
git pull origin version-2

# Install any new dependencies
cd "$WEB_DIR"
pip install -r requirements.txt

# Run database migrations (if any)
export FLASK_APP=wsgi.py
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app.extensions import db; db.create_all()"

echo ""
echo "Update complete!"
echo "Don't forget to click 'Reload' in the Web tab!"

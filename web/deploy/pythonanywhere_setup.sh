#!/bin/bash
# PythonAnywhere Deployment Script for GST Billing Web App
# Run this script in a PythonAnywhere Bash console

set -e  # Exit on error

# Configuration - EDIT THESE VALUES
GITHUB_REPO="https://github.com/Zac10ck/cosmicgst.git"
GITHUB_BRANCH="version-2"
PA_USERNAME="cosmicsurgical"
APP_NAME="gst-billing-web"
PYTHON_VERSION="3.10"
VENV_NAME="billing-env"

# Derived paths
HOME_DIR="/home/${PA_USERNAME}"
APP_DIR="${HOME_DIR}/${APP_NAME}"
WEB_DIR="${APP_DIR}/web"
VENV_DIR="${HOME_DIR}/.virtualenvs/${VENV_NAME}"

echo "=========================================="
echo "GST Billing - PythonAnywhere Deployment"
echo "=========================================="

# Step 1: Clone or update repository
echo ""
echo "[1/6] Setting up repository..."
if [ -d "$APP_DIR" ]; then
    echo "Repository exists. Pulling latest changes..."
    cd "$APP_DIR"
    git fetch origin
    git checkout "$GITHUB_BRANCH"
    git pull origin "$GITHUB_BRANCH"
else
    echo "Cloning repository..."
    cd "$HOME_DIR"
    git clone -b "$GITHUB_BRANCH" "$GITHUB_REPO" "$APP_NAME"
fi

# Step 2: Create/update virtual environment
echo ""
echo "[2/6] Setting up virtual environment..."
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment exists. Activating..."
    source "${VENV_DIR}/bin/activate"
else
    echo "Creating virtual environment..."
    mkvirtualenv --python=/usr/bin/python${PYTHON_VERSION} "$VENV_NAME"
fi

# Step 3: Install dependencies
echo ""
echo "[3/6] Installing dependencies..."
cd "$WEB_DIR"
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Create .env file if not exists
echo ""
echo "[4/6] Setting up environment..."
if [ ! -f "${WEB_DIR}/.env" ]; then
    echo "Creating .env file..."
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    cat > "${WEB_DIR}/.env" << EOF
SECRET_KEY=${SECRET_KEY}
FLASK_ENV=production
DATABASE_URL=sqlite:///${WEB_DIR}/instance/billing.db
EOF
    echo ".env file created with generated SECRET_KEY"
else
    echo ".env file already exists"
fi

# Step 5: Initialize database
echo ""
echo "[5/6] Initializing database..."
export FLASK_APP=wsgi.py
source "${WEB_DIR}/.env" 2>/dev/null || true
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app.extensions import db; db.create_all(); print('Database initialized!')"

# Step 6: Create admin user if needed
echo ""
echo "[6/6] Checking admin user..."
python << 'PYTHON_SCRIPT'
from app import create_app
from app.models.user import User
from app.extensions import db

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("Creating admin user...")
        admin = User(username='admin', email='admin@cosmicsurgical.com', role='admin')
        admin.set_password('changeme123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created! Username: admin, Password: changeme123")
        print("IMPORTANT: Change this password after first login!")
    else:
        print("Admin user already exists")
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps (manual in PythonAnywhere Web tab):"
echo ""
echo "1. Go to Web tab -> Add a new web app"
echo "2. Select 'Manual configuration' -> Python ${PYTHON_VERSION}"
echo "3. Set these values:"
echo "   - Source code: ${WEB_DIR}"
echo "   - Working directory: ${WEB_DIR}"
echo "   - Virtualenv: ${VENV_DIR}"
echo ""
echo "4. Edit WSGI file with content from:"
echo "   ${WEB_DIR}/deploy/wsgi_config.py"
echo ""
echo "5. Add Static files mapping:"
echo "   URL: /static/"
echo "   Directory: ${WEB_DIR}/app/static"
echo ""
echo "6. Click 'Reload' button"
echo ""
echo "Your app will be live at: https://${PA_USERNAME}.pythonanywhere.com"
echo ""

#!/usr/bin/env bash
# Render Build Script

set -o errexit  # Exit on error

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Initializing database..."
python << 'EOF'
from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()
with app.app_context():
    db.create_all()

    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        import os
        admin_password = os.environ.get('ADMIN_PASSWORD', 'changeme123')
        admin = User(username='admin', email='admin@cosmicsurgical.com', role='admin')
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print("Admin user created!")
    else:
        print("Admin user exists")

print("Database initialized!")
EOF

echo "Build complete!"

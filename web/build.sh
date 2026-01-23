#!/usr/bin/env bash
# Render Build Script

set -o errexit  # Exit on error

echo "=========================================="
echo "GST Billing - Build Script"
echo "=========================================="

echo ""
echo "[1/4] Upgrading pip..."
pip install --upgrade pip

echo ""
echo "[2/4] Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "[3/4] Creating instance directory..."
mkdir -p instance

echo ""
echo "[4/4] Initializing database..."
python << 'PYEOF'
import os
import sys

print(f"Python version: {sys.version}")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'not set')}")
print(f"DATABASE_URL set: {'yes' if os.environ.get('DATABASE_URL') else 'no'}")

try:
    from app import create_app
    from app.extensions import db
    from app.models.user import User
    from sqlalchemy import text, inspect

    app = create_app()
    with app.app_context():
        print(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'not set')[:50]}...")

        # Create all new tables first
        db.create_all()
        print("Tables created!")

        # Helper function to check if column exists
        def column_exists(table_name, column_name):
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            return column_name in columns

        # Add new columns to existing tables (for migrations)
        migrations = [
            # Invoice table - B2B/B2C fields
            ('invoice', 'supply_type', "VARCHAR(10) DEFAULT 'B2C'"),
            ('invoice', 'customer_gstin', "VARCHAR(15) DEFAULT ''"),
            # Company table - admin notification email
            ('company', 'admin_notification_email', "VARCHAR(200) DEFAULT ''"),
        ]

        for table, column, col_type in migrations:
            try:
                if not column_exists(table, column):
                    print(f"Adding column {column} to {table}...")
                    db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}'))
                    db.session.commit()
                    print(f"  Added {column} to {table}")
                else:
                    print(f"  Column {column} already exists in {table}")
            except Exception as e:
                print(f"  Warning: Could not add {column} to {table}: {e}")
                db.session.rollback()

        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_password = os.environ.get('ADMIN_PASSWORD', 'changeme123')
            admin = User(username='admin', email='admin@cosmicsurgical.com', role='admin')
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("Admin user created! (admin/changeme123)")
        else:
            print("Admin user already exists")

    print("Database initialized successfully!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

echo ""
echo "=========================================="
echo "Build complete!"
echo "=========================================="

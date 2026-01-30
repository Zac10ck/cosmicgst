#!/usr/bin/env python3
"""
Weekly Invoice Summary Email Runner

This script sends a weekly summary email with all invoices from the past week.
It should be run via cron or systemd timer every Sunday.

Usage:
    python send_weekly_summary.py

Environment variables required:
    DATABASE_URL - PostgreSQL connection string
    MAIL_SERVER - SMTP server (default: smtp.gmail.com)
    MAIL_PORT - SMTP port (default: 587)
    MAIL_USERNAME - SMTP username
    MAIL_PASSWORD - SMTP password (app password for Gmail)
    MAIL_USE_TLS - Use TLS (default: true)
    MAIL_DEFAULT_SENDER - From email address
"""
import os
import sys

# Add the project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Set default environment if not set
if not os.environ.get('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'production'

if not os.environ.get('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'postgresql://gst_admin:gst_secure_pass_2024@localhost/gst_billing'

# SMTP config (will be overridden by systemd environment)
if not os.environ.get('MAIL_SERVER'):
    os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
if not os.environ.get('MAIL_PORT'):
    os.environ['MAIL_PORT'] = '587'
if not os.environ.get('MAIL_USE_TLS'):
    os.environ['MAIL_USE_TLS'] = 'true'


def main():
    """Run the weekly summary email job"""
    print('=' * 50)
    print('GST Billing - Weekly Summary Email')
    print('=' * 50)

    try:
        # Import Flask app
        from app import create_app
        from app.services.weekly_summary_service import send_weekly_summary_email

        # Create app context
        app = create_app()

        with app.app_context():
            print('Sending weekly summary email...')
            success = send_weekly_summary_email()

            if success:
                print('Weekly summary completed successfully!')
                return 0
            else:
                print('Weekly summary failed or no invoices to send')
                return 1

    except ImportError as e:
        print(f'Import error: {e}')
        print('Make sure you are running from the web directory with venv activated')
        return 1
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

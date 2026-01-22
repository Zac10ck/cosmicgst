"""Flask application factory"""
import os
from flask import Flask, redirect, url_for
from app.config import config
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_name=None):
    """Create and configure the Flask application"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    register_blueprints(app)

    # Register CLI commands
    register_commands(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Root route
    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))

    return app


def register_blueprints(app):
    """Register Flask blueprints"""
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.products import products_bp
    from app.blueprints.customers import customers_bp
    from app.blueprints.billing import billing_bp
    from app.blueprints.quotations import quotations_bp
    from app.blueprints.credit_notes import credit_notes_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.settings import settings_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(products_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(quotations_bp)
    app.register_blueprint(credit_notes_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)  # REST API


def register_commands(app):
    """Register Flask CLI commands"""
    import click

    @app.cli.command('create-admin')
    @click.option('--username', default='admin', help='Admin username')
    @click.option('--email', default='admin@example.com', help='Admin email')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, email, password):
        """Create an admin user"""
        from app.models.user import User

        # Check if user exists
        if User.query.filter_by(username=username).first():
            click.echo(f'User {username} already exists!')
            return

        user = User(username=username, email=email, role='admin')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Admin user {username} created successfully!')

    @app.cli.command('init-db')
    def init_db():
        """Initialize the database"""
        db.create_all()
        click.echo('Database initialized!')

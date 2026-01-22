"""Flask extensions initialization"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Database
db = SQLAlchemy()

# Database migrations
migrate = Migrate()

# Login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# CSRF protection
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    from app.models.user import User
    return User.query.get(int(user_id))

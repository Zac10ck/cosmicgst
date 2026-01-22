"""Flask application configuration"""
import os
from pathlib import Path


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Application settings
    APP_NAME = "GST Billing"
    APP_VERSION = "2.0.0"

    # GST settings
    GST_RATES = [0, 5, 12, 18, 28]
    DEFAULT_GST_RATE = 18.0
    FINANCIAL_YEAR_START_MONTH = 4  # April

    # Invoice settings
    INVOICE_PREFIX = "INV"
    QUOTATION_PREFIX = "QTN"
    CREDIT_NOTE_PREFIX = "CN"

    # Payment modes
    PAYMENT_MODES = ["CASH", "UPI", "CARD", "CREDIT", "BANK TRANSFER"]

    # Units
    UNITS = ["NOS", "KG", "GM", "LTR", "ML", "MTR", "CM", "SQM", "BOX", "PKT", "PCS"]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + str(Path(__file__).parent.parent / 'instance' / 'billing.db')


class ProductionConfig(Config):
    """Production configuration for Render/PythonAnywhere"""
    DEBUG = False

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Render provides DATABASE_URL (PostgreSQL)
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            # Render uses postgres:// but SQLAlchemy needs postgresql://
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return database_url

        # Fallback to MySQL for PythonAnywhere
        db_user = os.environ.get('DB_USER', 'cosmicsurgical')
        db_pass = os.environ.get('DB_PASS', '')
        db_host = os.environ.get('DB_HOST', 'cosmicsurgical.mysql.pythonanywhere-services.com')
        db_name = os.environ.get('DB_NAME', 'cosmicsurgical$billing')
        return f"mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}/{db_name}"


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

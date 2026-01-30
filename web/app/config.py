"""Flask application configuration"""
import os
from pathlib import Path


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Application settings
    APP_NAME = "Cosmic Surgical"
    APP_VERSION = "2.1.0"

    # GST settings
    GST_RATES = [0, 5, 12, 18, 28]
    DEFAULT_GST_RATE = 18.0
    FINANCIAL_YEAR_START_MONTH = 4  # April
    DEFAULT_STATE_CODE = "32"  # Kerala

    # Invoice settings
    INVOICE_PREFIX = "CS"
    QUOTATION_PREFIX = "CSQ"
    CREDIT_NOTE_PREFIX = "CSCN"

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

    # Database URL - Render provides DATABASE_URL (PostgreSQL)
    _database_url = os.environ.get('DATABASE_URL', '')

    # Fix Render's postgres:// to postgresql://
    if _database_url.startswith('postgres://'):
        _database_url = _database_url.replace('postgres://', 'postgresql://', 1)

    # Use DATABASE_URL if available, otherwise fallback to SQLite
    if _database_url:
        SQLALCHEMY_DATABASE_URI = _database_url
    else:
        # Fallback to SQLite for simple deployment
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(Path(__file__).parent.parent / 'instance' / 'billing.db')


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

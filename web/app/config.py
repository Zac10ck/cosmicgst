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
    """Production configuration for PythonAnywhere"""
    DEBUG = False

    # MySQL connection for PythonAnywhere
    DB_USER = os.environ.get('DB_USER', 'cosmicsurgical')
    DB_PASS = os.environ.get('DB_PASS', '')
    DB_HOST = os.environ.get('DB_HOST', 'cosmicsurgical.mysql.pythonanywhere-services.com')
    DB_NAME = os.environ.get('DB_NAME', 'cosmicsurgical$billing')

    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"


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

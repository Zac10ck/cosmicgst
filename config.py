"""Application configuration"""
import os
from pathlib import Path

# Application Info
APP_NAME = "GST Billing"
APP_VERSION = "2.0.0"

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
BACKUP_DIR = Path.home() / "Google Drive" / "Billing Backup"

# Database
DB_PATH = DATA_DIR / "billing.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)

# GST Settings
GST_RATES = [0, 5, 12, 18, 28]
DEFAULT_GST_RATE = 18.0

# State Codes (India)
STATE_CODES = {
    "32": "Kerala",
    "33": "Tamil Nadu",
    "29": "Karnataka",
    "27": "Maharashtra",
    "07": "Delhi",
}
DEFAULT_STATE_CODE = "32"  # Kerala

# Invoice Settings
INVOICE_PREFIX = "INV"
FINANCIAL_YEAR_START_MONTH = 4  # April

# Units
UNITS = ["NOS", "KG", "GM", "LTR", "ML", "MTR", "CM", "SQM", "BOX", "PKT", "PCS"]

# Payment Modes
PAYMENT_MODES = ["CASH", "UPI", "CARD", "CREDIT", "BANK TRANSFER"]

# UI Settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
THEME = "dark-blue"  # CustomTkinter theme

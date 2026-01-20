#!/usr/bin/env python3
"""Basic syntax and import test"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing basic imports and syntax...")
print("=" * 50)

# Test config
print("\n1. Testing config module...")
from config import APP_NAME, DB_PATH, GST_RATES
print(f"   App name: {APP_NAME}")
print(f"   DB path: {DB_PATH}")
print(f"   GST rates: {GST_RATES}")

# Test database module
print("\n2. Testing database module...")
from database.db import get_connection, init_db
print("   Database module loaded successfully")

# Test models
print("\n3. Testing models...")
from database.models import Product, Customer, Invoice, Company
print("   All models loaded successfully")

# Test validators
print("\n4. Testing validators...")
from utils.validators import validate_gstin, validate_hsn

valid, msg = validate_gstin("32AABCU9603R1ZM")
print(f"   GSTIN validation: {valid}")

valid, msg = validate_hsn("8471")
print(f"   HSN validation: {valid}")

# Test GST calculator (import directly to avoid reportlab dependency)
print("\n5. Testing GST calculator...")
import sys
sys.path.insert(0, str(Path(__file__).parent / "services"))
from services.gst_calculator import GSTCalculator
calc = GSTCalculator()
tax = calc.calculate_item_tax(qty=2, rate=1000, gst_rate=18)
print(f"   Tax calculation: Taxable={tax.taxable_value}, Total={tax.total_amount}")

# Test database initialization
print("\n6. Testing database initialization...")
init_db()
print("   Database initialized")

# Test product creation
print("\n7. Testing product model...")
product = Product(
    name="Test Product",
    barcode="TEST123",
    price=100,
    gst_rate=18
)
print(f"   Product created: {product.name}")

print("\n" + "=" * 50)
print("Basic tests passed!")
print("\nNote: Full application requires these packages:")
print("  pip install customtkinter pillow reportlab num2words python-dateutil")

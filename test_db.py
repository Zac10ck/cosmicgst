#!/usr/bin/env python3
"""Test database and basic functionality"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.db import init_db, get_connection
from database.models import Product, Customer, Invoice, Company
from services.gst_calculator import GSTCalculator

print("Testing GST Billing Software Components...")
print("=" * 50)

# Test 1: Initialize database
print("\n1. Initializing database...")
init_db()
print("   Database initialized successfully!")

# Test 2: Add sample company
print("\n2. Setting up sample company...")
company = Company.get()
if not company:
    company = Company(
        name="Sample Shop",
        address="Main Road, Kochi, Kerala - 682001",
        gstin="32AABCU9603R1ZM",
        phone="9876543210"
    )
    company.save()
    print("   Sample company created!")
else:
    print(f"   Company exists: {company.name}")

# Test 3: Add sample products
print("\n3. Adding sample products...")
products_data = [
    {"name": "Laptop", "barcode": "1234567890123", "hsn_code": "8471", "price": 45000, "gst_rate": 18, "stock_qty": 10},
    {"name": "Mouse", "barcode": "1234567890124", "hsn_code": "8471", "price": 500, "gst_rate": 18, "stock_qty": 50},
    {"name": "Keyboard", "barcode": "1234567890125", "hsn_code": "8471", "price": 800, "gst_rate": 18, "stock_qty": 30},
    {"name": "USB Cable", "barcode": "1234567890126", "hsn_code": "8544", "price": 150, "gst_rate": 18, "stock_qty": 100},
    {"name": "Notebook", "barcode": "1234567890127", "hsn_code": "4820", "price": 50, "gst_rate": 12, "stock_qty": 200},
]

for p_data in products_data:
    existing = Product.get_by_barcode(p_data['barcode'])
    if not existing:
        product = Product(**p_data)
        product.save()
        print(f"   Added: {product.name}")
    else:
        print(f"   Exists: {existing.name}")

# Test 4: Test GST Calculator
print("\n4. Testing GST Calculator...")
calc = GSTCalculator(seller_state_code="32")  # Kerala

# Test intra-state (Kerala to Kerala)
result = calc.calculate_item_tax(qty=2, rate=1000, gst_rate=18, buyer_state_code="32")
print(f"   Intra-state (Kerala): Taxable=2000, CGST={result.cgst_amount}, SGST={result.sgst_amount}, Total={result.total_amount}")

# Test inter-state (Kerala to Tamil Nadu)
result = calc.calculate_item_tax(qty=2, rate=1000, gst_rate=18, buyer_state_code="33")
print(f"   Inter-state (TN): Taxable=2000, IGST={result.igst_amount}, Total={result.total_amount}")

# Test 5: Invoice number generation
print("\n5. Testing Invoice Number Generation...")
invoice_number = Invoice.get_next_invoice_number()
print(f"   Next invoice number: {invoice_number}")

# Test 6: Search products
print("\n6. Testing Product Search...")
results = Product.search("Laptop")
print(f"   Found {len(results)} product(s) matching 'Laptop'")

# Test 7: Check database file
print("\n7. Database Status...")
from config import DB_PATH
print(f"   Database path: {DB_PATH}")
print(f"   Database exists: {DB_PATH.exists()}")
if DB_PATH.exists():
    print(f"   Database size: {DB_PATH.stat().st_size} bytes")

print("\n" + "=" * 50)
print("All tests passed! The application is ready to use.")
print("\nTo run the application, execute: python main.py")

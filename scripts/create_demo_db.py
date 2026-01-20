"""Create a demo database with sample data for client presentation"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
import random
from database.db import init_db, get_connection
from database.models import Company, Product, Customer, Invoice, Category
from services.invoice_service import InvoiceService

def create_demo_data():
    """Create sample data for demo"""

    # Initialize database
    init_db()

    conn = get_connection()

    # Clear existing data (except structure)
    tables = ['invoice_items', 'invoices', 'credit_notes', 'credit_note_items',
              'invoice_payments', 'stock_log', 'held_bills', 'products', 'customers', 'company', 'categories']
    for table in tables:
        try:
            conn.execute(f"DELETE FROM {table}")
        except Exception as e:
            print(f"  Note: Could not clear {table}: {e}")
    conn.commit()
    conn.close()

    print("Creating demo data...")

    # 1. Company Details
    company = Company(
        name="COSMIC RETAIL STORE",
        address="123 MG Road, Ernakulam\nKochi, Kerala - 682011",
        gstin="32AABCU9603R1ZM",
        state_code="32",
        phone="0484-2345678, 9876543210",
        email="sales@cosmicretail.com",
        bank_details="Bank: State Bank of India\nA/C: 12345678901234\nIFSC: SBIN0001234\nBranch: MG Road, Kochi"
    )
    company.save()
    print("- Company details created")

    # 2. Categories
    categories_data = [
        ("Electronics", "Electronic gadgets and accessories"),
        ("Groceries", "Food and daily essentials"),
        ("Stationery", "Office and school supplies"),
        ("Home Appliances", "Kitchen and home appliances"),
        ("Personal Care", "Beauty and personal care products"),
    ]

    categories = {}
    for name, desc in categories_data:
        cat = Category(name=name, description=desc)
        cat.save()
        categories[name] = cat
    print(f"- {len(categories)} categories created")

    # 3. Products
    products_data = [
        # Electronics (18% GST)
        ("Samsung Galaxy M14", "8471", 12999, 18, "Electronics", "NOS", 50),
        ("boAt Rockerz 450", "8518", 1499, 18, "Electronics", "NOS", 100),
        ("Fire-Boltt Ninja", "9102", 1799, 18, "Electronics", "NOS", 75),
        ("Realme Buds Air", "8518", 2999, 18, "Electronics", "NOS", 60),
        ("Mi Power Bank 10000", "8507", 999, 18, "Electronics", "NOS", 80),
        ("USB Type-C Cable", "8544", 299, 18, "Electronics", "NOS", 200),
        ("Mobile Cover", "3926", 199, 18, "Electronics", "NOS", 150),

        # Home Appliances (18% GST)
        ("Philips Mixer Grinder", "8509", 3499, 18, "Home Appliances", "NOS", 30),
        ("Prestige Induction Cooktop", "8516", 2799, 18, "Home Appliances", "NOS", 25),
        ("Bajaj Room Heater", "8516", 1899, 18, "Home Appliances", "NOS", 20),
        ("Kent RO Water Purifier", "8421", 15999, 18, "Home Appliances", "NOS", 10),

        # Groceries (5% GST)
        ("Aashirvaad Atta 10kg", "1101", 485, 5, "Groceries", "PKT", 100),
        ("Fortune Sunflower Oil 5L", "1512", 699, 5, "Groceries", "PKT", 80),
        ("Tata Salt 1kg", "2501", 28, 5, "Groceries", "PKT", 200),
        ("India Gate Basmati 5kg", "1006", 599, 5, "Groceries", "PKT", 60),
        ("Nescafe Classic 200g", "0901", 450, 5, "Groceries", "PKT", 50),

        # Groceries (0% GST - Exempt)
        ("Fresh Vegetables Pack", "0703", 150, 0, "Groceries", "KG", 50),
        ("Fruits Combo", "0804", 299, 0, "Groceries", "KG", 40),

        # Stationery (12% GST)
        ("Classmate Notebook Pack", "4820", 199, 12, "Stationery", "PKT", 150),
        ("Reynolds Pen Box (10)", "9608", 150, 12, "Stationery", "BOX", 100),
        ("Camlin Marker Set", "9608", 299, 12, "Stationery", "PKT", 75),
        ("A4 Paper Ream", "4802", 350, 12, "Stationery", "PKT", 80),

        # Personal Care (18% GST)
        ("Dove Shampoo 650ml", "3305", 499, 18, "Personal Care", "NOS", 60),
        ("Colgate Toothpaste 300g", "3306", 175, 18, "Personal Care", "NOS", 100),
        ("Nivea Body Lotion 400ml", "3304", 399, 18, "Personal Care", "NOS", 50),
        ("Dettol Handwash 900ml", "3401", 199, 18, "Personal Care", "NOS", 80),
    ]

    products = []
    for name, hsn, price, gst, cat_name, unit, stock in products_data:
        barcode = f"89{random.randint(10000000000, 99999999999)}"
        p = Product(
            name=name,
            barcode=barcode,
            hsn_code=hsn,
            unit=unit,
            price=price,
            gst_rate=gst,
            stock_qty=stock,
            low_stock_alert=10,
            category_id=categories[cat_name].id,
            purchase_price=price * 0.7  # 30% margin
        )
        p.save()
        products.append(p)
    print(f"- {len(products)} products created")

    # 4. Customers
    customers_data = [
        ("Rahul Sharma", "9876543210", "45 Anna Nagar, Chennai", "33AABCS1234A1ZY", "33"),
        ("Priya Menon", "9876543211", "12 MG Road, Kochi", "32AABCP5678B1ZX", "32"),
        ("Mohammed Ali", "9876543212", "78 Brigade Road, Bangalore", "29AABCM9012C1ZW", "29"),
        ("Anjali Nair", "9876543213", "23 Marine Drive, Kochi", "", "32"),
        ("Suresh Kumar", "9876543214", "56 Park Street, Kolkata", "19AABCS3456D1ZV", "19"),
        ("Lakshmi Iyer", "9876543215", "89 T Nagar, Chennai", "", "33"),
        ("Arun Pillai", "9876543216", "34 Vytilla, Kochi", "32AABCA7890E1ZU", "32"),
        ("Deepa Krishnan", "9876543217", "67 Indiranagar, Bangalore", "", "29"),
    ]

    customers = []
    for name, phone, address, gstin, state in customers_data:
        c = Customer(
            name=name,
            phone=phone,
            address=address,
            gstin=gstin,
            state_code=state,
            credit_limit=50000 if gstin else 10000
        )
        c.save()
        customers.append(c)
    print(f"- {len(customers)} customers created")

    # 5. Create Sample Invoices
    invoice_service = InvoiceService()

    # Generate invoices for the last 30 days
    today = date.today()
    invoice_count = 0

    for days_ago in range(30, -1, -1):
        invoice_date = today - timedelta(days=days_ago)

        # 2-5 invoices per day
        num_invoices = random.randint(2, 5)

        for _ in range(num_invoices):
            # Random customer (or None for cash)
            customer = random.choice(customers + [None, None, None])  # 3/11 chance of cash customer

            # Random 1-5 products
            num_items = random.randint(1, 5)
            cart_items = []
            selected_products = random.sample(products, min(num_items, len(products)))

            for product in selected_products:
                qty = random.randint(1, 3)
                cart_items.append({
                    'product_id': product.id,
                    'qty': qty
                })

            # Random discount (0-10% of orders have discount)
            discount = random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 50, 100, 200])

            # Random payment mode
            payment_mode = random.choice(["CASH", "CASH", "CASH", "UPI", "UPI", "CARD"])

            try:
                invoice = invoice_service.create_invoice(
                    cart_items=cart_items,
                    customer=customer,
                    discount=discount,
                    payment_mode=payment_mode,
                    invoice_date=invoice_date
                )
                invoice_count += 1
            except Exception as e:
                print(f"  Warning: Could not create invoice: {e}")

    print(f"- {invoice_count} invoices created")

    print("\nDemo database created successfully!")
    print(f"Location: {os.path.abspath('data/billing.db')}")

if __name__ == "__main__":
    create_demo_data()

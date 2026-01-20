"""Database connection and initialization"""
import sqlite3
from pathlib import Path
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database with schema"""
    conn = get_connection()
    cursor = conn.cursor()

    # Company/Shop Details
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT,
            gstin TEXT,
            state_code TEXT DEFAULT '32',
            phone TEXT,
            email TEXT,
            bank_details TEXT,
            logo_path TEXT
        )
    """)

    # Products/Items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            barcode TEXT UNIQUE,
            hsn_code TEXT,
            unit TEXT DEFAULT 'NOS',
            price REAL NOT NULL,
            gst_rate REAL DEFAULT 18.0,
            stock_qty REAL DEFAULT 0,
            low_stock_alert REAL DEFAULT 10,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            gstin TEXT,
            state_code TEXT DEFAULT '32',
            is_active INTEGER DEFAULT 1
        )
    """)

    # Invoices
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY,
            invoice_number TEXT UNIQUE NOT NULL,
            invoice_date DATE NOT NULL,
            customer_id INTEGER,
            customer_name TEXT,
            subtotal REAL,
            cgst_total REAL,
            sgst_total REAL,
            igst_total REAL,
            discount REAL DEFAULT 0,
            grand_total REAL,
            payment_mode TEXT DEFAULT 'CASH',
            is_cancelled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # Invoice Line Items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT,
            hsn_code TEXT,
            qty REAL,
            unit TEXT,
            rate REAL,
            gst_rate REAL,
            taxable_value REAL,
            cgst REAL,
            sgst REAL,
            igst REAL,
            total REAL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Stock Movement Log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_log (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            change_qty REAL,
            reason TEXT,
            reference_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number)")

    conn.commit()
    conn.close()

    print(f"Database initialized at: {DB_PATH}")


if __name__ == "__main__":
    init_db()

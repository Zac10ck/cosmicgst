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

    # Product Categories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Add category_id to products if not exists
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN category_id INTEGER REFERENCES categories(id)")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add purchase_price to products if not exists (for profit calculation)
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN purchase_price REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Add credit_balance to customers if not exists
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN credit_balance REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Add credit_limit to customers if not exists
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN credit_limit REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Held Bills (for hold/recall feature)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS held_bills (
            id INTEGER PRIMARY KEY,
            hold_name TEXT,
            customer_id INTEGER,
            customer_name TEXT,
            items_json TEXT,
            discount REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # App Settings (for password, preferences, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Add amount_paid and balance to invoices if not exists
    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN amount_paid REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN balance_due REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Add e-Way Bill related columns to invoices
    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN vehicle_number TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN transport_mode TEXT DEFAULT 'Road'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN transport_distance INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN transporter_id TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN eway_bill_number TEXT")
    except sqlite3.OperationalError:
        pass

    # Add PIN code to customers for e-Way Bill
    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN pin_code TEXT")
    except sqlite3.OperationalError:
        pass

    # Add payment_status to invoices
    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN payment_status TEXT DEFAULT 'PAID'")
    except sqlite3.OperationalError:
        pass

    # Invoice Payments table (for split payments)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_payments (
            id INTEGER PRIMARY KEY,
            invoice_id INTEGER NOT NULL,
            payment_mode TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_date DATE NOT NULL,
            reference_number TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        )
    """)

    # Credit Notes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_notes (
            id INTEGER PRIMARY KEY,
            credit_note_number TEXT UNIQUE NOT NULL,
            credit_note_date DATE NOT NULL,
            original_invoice_id INTEGER,
            original_invoice_number TEXT,
            customer_id INTEGER,
            customer_name TEXT,
            reason TEXT NOT NULL,
            reason_details TEXT,
            subtotal REAL,
            cgst_total REAL,
            sgst_total REAL,
            igst_total REAL,
            grand_total REAL,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (original_invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # Credit Note Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_note_items (
            id INTEGER PRIMARY KEY,
            credit_note_id INTEGER NOT NULL,
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
            FOREIGN KEY (credit_note_id) REFERENCES credit_notes(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Quotations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotations (
            id INTEGER PRIMARY KEY,
            quotation_number TEXT UNIQUE NOT NULL,
            quotation_date DATE NOT NULL,
            validity_date DATE NOT NULL,
            customer_id INTEGER,
            customer_name TEXT,
            subtotal REAL,
            cgst_total REAL,
            sgst_total REAL,
            igst_total REAL,
            discount REAL DEFAULT 0,
            grand_total REAL,
            status TEXT DEFAULT 'DRAFT',
            notes TEXT,
            terms_conditions TEXT,
            converted_invoice_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (converted_invoice_id) REFERENCES invoices(id)
        )
    """)

    # Quotation Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotation_items (
            id INTEGER PRIMARY KEY,
            quotation_id INTEGER NOT NULL,
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
            FOREIGN KEY (quotation_id) REFERENCES quotations(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Email Queue table (for offline email support)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_queue (
            id INTEGER PRIMARY KEY,
            invoice_id INTEGER NOT NULL,
            recipient_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            pdf_data BLOB,
            status TEXT DEFAULT 'PENDING',
            retry_count INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        )
    """)

    # Create indexes for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoice_payments_invoice ON invoice_payments(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoice_payments_date ON invoice_payments(payment_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_credit_notes_date ON credit_notes(credit_note_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_credit_notes_invoice ON credit_notes(original_invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_credit_notes_customer ON credit_notes(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotations_date ON quotations(quotation_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotations_status ON quotations(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotations_customer ON quotations(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue(status)")

    # Insert default categories if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ('General', 'Default category'),
            ('Electronics', 'Electronic items'),
            ('Groceries', 'Food and grocery items'),
            ('Stationery', 'Office and school supplies'),
            ('Clothing', 'Apparel and garments'),
        ]
        cursor.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", default_categories)

    conn.commit()
    conn.close()

    print(f"Database initialized at: {DB_PATH}")


if __name__ == "__main__":
    init_db()

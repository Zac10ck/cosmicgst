"""Data models and CRUD operations"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date, datetime
from .db import get_connection


@dataclass
class Company:
    id: Optional[int] = None
    name: str = ""
    address: str = ""
    gstin: str = ""
    state_code: str = "32"
    phone: str = ""
    email: str = ""
    bank_details: str = ""
    logo_path: str = ""

    @classmethod
    def get(cls) -> Optional['Company']:
        """Get company details (singleton)"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM company LIMIT 1").fetchone()
        conn.close()
        if row:
            return cls(**dict(row))
        return None

    def save(self):
        """Save or update company details"""
        conn = get_connection()
        if self.id:
            conn.execute("""
                UPDATE company SET name=?, address=?, gstin=?, state_code=?,
                phone=?, email=?, bank_details=?, logo_path=? WHERE id=?
            """, (self.name, self.address, self.gstin, self.state_code,
                  self.phone, self.email, self.bank_details, self.logo_path, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO company (name, address, gstin, state_code, phone, email, bank_details, logo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.name, self.address, self.gstin, self.state_code,
                  self.phone, self.email, self.bank_details, self.logo_path))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()


@dataclass
class Product:
    id: Optional[int] = None
    name: str = ""
    barcode: str = ""
    hsn_code: str = ""
    unit: str = "NOS"
    price: float = 0.0
    gst_rate: float = 18.0
    stock_qty: float = 0.0
    low_stock_alert: float = 10.0
    is_active: bool = True
    created_at: Optional[datetime] = None
    category_id: Optional[int] = None
    purchase_price: float = 0.0

    @classmethod
    def get_all(cls, active_only: bool = True) -> List['Product']:
        """Get all products"""
        conn = get_connection()
        query = "SELECT * FROM products"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"
        rows = conn.execute(query).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_by_id(cls, product_id: int) -> Optional['Product']:
        """Get product by ID"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        conn.close()
        if row:
            return cls(**dict(row))
        return None

    @classmethod
    def get_by_barcode(cls, barcode: str) -> Optional['Product']:
        """Get product by barcode"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM products WHERE barcode = ? AND is_active = 1", (barcode,)).fetchone()
        conn.close()
        if row:
            return cls(**dict(row))
        return None

    @classmethod
    def search(cls, query: str) -> List['Product']:
        """Search products by name or barcode"""
        conn = get_connection()
        search_term = f"%{query}%"
        rows = conn.execute("""
            SELECT * FROM products
            WHERE (name LIKE ? OR barcode LIKE ?) AND is_active = 1
            ORDER BY name LIMIT 20
        """, (search_term, search_term)).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_low_stock(cls) -> List['Product']:
        """Get products with low stock"""
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM products
            WHERE stock_qty <= low_stock_alert AND is_active = 1
            ORDER BY stock_qty
        """).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    def save(self):
        """Save or update product"""
        conn = get_connection()
        if self.id:
            conn.execute("""
                UPDATE products SET name=?, barcode=?, hsn_code=?, unit=?, price=?,
                gst_rate=?, stock_qty=?, low_stock_alert=?, is_active=?, category_id=?, purchase_price=? WHERE id=?
            """, (self.name, self.barcode, self.hsn_code, self.unit, self.price,
                  self.gst_rate, self.stock_qty, self.low_stock_alert, self.is_active,
                  self.category_id, self.purchase_price, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO products (name, barcode, hsn_code, unit, price, gst_rate, stock_qty, low_stock_alert, is_active, category_id, purchase_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.name, self.barcode, self.hsn_code, self.unit, self.price,
                  self.gst_rate, self.stock_qty, self.low_stock_alert, self.is_active,
                  self.category_id, self.purchase_price))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    def update_stock(self, qty_change: float, reason: str, reference_id: int = None):
        """Update stock quantity and log the change"""
        conn = get_connection()
        self.stock_qty += qty_change
        conn.execute("UPDATE products SET stock_qty = ? WHERE id = ?", (self.stock_qty, self.id))
        conn.execute("""
            INSERT INTO stock_log (product_id, change_qty, reason, reference_id)
            VALUES (?, ?, ?, ?)
        """, (self.id, qty_change, reason, reference_id))
        conn.commit()
        conn.close()


@dataclass
class Customer:
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    address: str = ""
    gstin: str = ""
    state_code: str = "32"
    is_active: bool = True
    credit_balance: float = 0.0
    credit_limit: float = 0.0

    @classmethod
    def get_all(cls, active_only: bool = True) -> List['Customer']:
        """Get all customers"""
        conn = get_connection()
        query = "SELECT * FROM customers"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"
        rows = conn.execute(query).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_by_id(cls, customer_id: int) -> Optional['Customer']:
        """Get customer by ID"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        conn.close()
        if row:
            return cls(**dict(row))
        return None

    @classmethod
    def search(cls, query: str) -> List['Customer']:
        """Search customers by name or phone"""
        conn = get_connection()
        search_term = f"%{query}%"
        rows = conn.execute("""
            SELECT * FROM customers
            WHERE (name LIKE ? OR phone LIKE ?) AND is_active = 1
            ORDER BY name LIMIT 20
        """, (search_term, search_term)).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    def save(self):
        """Save or update customer"""
        conn = get_connection()
        if self.id:
            conn.execute("""
                UPDATE customers SET name=?, phone=?, address=?, gstin=?, state_code=?, is_active=?,
                credit_balance=?, credit_limit=? WHERE id=?
            """, (self.name, self.phone, self.address, self.gstin, self.state_code, self.is_active,
                  self.credit_balance, self.credit_limit, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO customers (name, phone, address, gstin, state_code, is_active, credit_balance, credit_limit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.name, self.phone, self.address, self.gstin, self.state_code, self.is_active,
                  self.credit_balance, self.credit_limit))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    def update_credit(self, amount: float):
        """Update customer credit balance (positive = add credit, negative = reduce)"""
        conn = get_connection()
        self.credit_balance += amount
        conn.execute("UPDATE customers SET credit_balance = ? WHERE id = ?", (self.credit_balance, self.id))
        conn.commit()
        conn.close()


@dataclass
class InvoiceItem:
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    product_id: Optional[int] = None
    product_name: str = ""
    hsn_code: str = ""
    qty: float = 0.0
    unit: str = "NOS"
    rate: float = 0.0
    gst_rate: float = 0.0
    taxable_value: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    total: float = 0.0


@dataclass
class Invoice:
    id: Optional[int] = None
    invoice_number: str = ""
    invoice_date: date = field(default_factory=date.today)
    customer_id: Optional[int] = None
    customer_name: str = ""
    subtotal: float = 0.0
    cgst_total: float = 0.0
    sgst_total: float = 0.0
    igst_total: float = 0.0
    discount: float = 0.0
    grand_total: float = 0.0
    payment_mode: str = "CASH"
    is_cancelled: bool = False
    created_at: Optional[datetime] = None
    items: List[InvoiceItem] = field(default_factory=list)

    @classmethod
    def get_by_id(cls, invoice_id: int) -> Optional['Invoice']:
        """Get invoice by ID with items"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
        if not row:
            conn.close()
            return None

        invoice = cls(**{k: v for k, v in dict(row).items() if k != 'items'})

        # Get items
        items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,)).fetchall()
        invoice.items = [InvoiceItem(**dict(item)) for item in items]

        conn.close()
        return invoice

    @classmethod
    def get_by_number(cls, invoice_number: str) -> Optional['Invoice']:
        """Get invoice by number"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM invoices WHERE invoice_number = ?", (invoice_number,)).fetchone()
        conn.close()
        if row:
            return cls.get_by_id(row['id'])
        return None

    @classmethod
    def get_by_date_range(cls, start_date: date, end_date: date) -> List['Invoice']:
        """Get invoices in date range"""
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM invoices
            WHERE invoice_date BETWEEN ? AND ? AND is_cancelled = 0
            ORDER BY invoice_date DESC, id DESC
        """, (start_date.isoformat(), end_date.isoformat())).fetchall()
        conn.close()
        return [cls.get_by_id(row['id']) for row in rows]

    @classmethod
    def get_next_invoice_number(cls) -> str:
        """Generate next invoice number"""
        from datetime import date
        from config import INVOICE_PREFIX, FINANCIAL_YEAR_START_MONTH

        today = date.today()
        if today.month >= FINANCIAL_YEAR_START_MONTH:
            fy_start = today.year
            fy_end = today.year + 1
        else:
            fy_start = today.year - 1
            fy_end = today.year

        fy_str = f"{fy_start}-{str(fy_end)[-2:]}"
        prefix = f"{INVOICE_PREFIX}/{fy_str}/"

        conn = get_connection()
        row = conn.execute("""
            SELECT invoice_number FROM invoices
            WHERE invoice_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f"{prefix}%",)).fetchone()
        conn.close()

        if row:
            try:
                last_num = int(row['invoice_number'].split('/')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"

    def save(self):
        """Save invoice and items"""
        conn = get_connection()

        if self.id:
            conn.execute("""
                UPDATE invoices SET invoice_number=?, invoice_date=?, customer_id=?,
                customer_name=?, subtotal=?, cgst_total=?, sgst_total=?, igst_total=?,
                discount=?, grand_total=?, payment_mode=?, is_cancelled=? WHERE id=?
            """, (self.invoice_number, self.invoice_date.isoformat(), self.customer_id,
                  self.customer_name, self.subtotal, self.cgst_total, self.sgst_total,
                  self.igst_total, self.discount, self.grand_total, self.payment_mode,
                  self.is_cancelled, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO invoices (invoice_number, invoice_date, customer_id, customer_name,
                subtotal, cgst_total, sgst_total, igst_total, discount, grand_total, payment_mode, is_cancelled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.invoice_number, self.invoice_date.isoformat(), self.customer_id,
                  self.customer_name, self.subtotal, self.cgst_total, self.sgst_total,
                  self.igst_total, self.discount, self.grand_total, self.payment_mode, self.is_cancelled))
            self.id = cursor.lastrowid

        # Delete existing items and re-insert
        conn.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (self.id,))

        for item in self.items:
            item.invoice_id = self.id
            conn.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, product_name, hsn_code,
                qty, unit, rate, gst_rate, taxable_value, cgst, sgst, igst, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item.invoice_id, item.product_id, item.product_name, item.hsn_code,
                  item.qty, item.unit, item.rate, item.gst_rate, item.taxable_value,
                  item.cgst, item.sgst, item.igst, item.total))

        conn.commit()
        conn.close()


@dataclass
class StockLog:
    id: Optional[int] = None
    product_id: Optional[int] = None
    change_qty: float = 0.0
    reason: str = ""
    reference_id: Optional[int] = None
    created_at: Optional[datetime] = None

    @classmethod
    def get_by_product(cls, product_id: int) -> List['StockLog']:
        """Get stock log for a product"""
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM stock_log WHERE product_id = ? ORDER BY created_at DESC
        """, (product_id,)).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]


@dataclass
class Category:
    """Product category model"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    is_active: bool = True

    @classmethod
    def get_all(cls, active_only: bool = True) -> List['Category']:
        """Get all categories"""
        conn = get_connection()
        query = "SELECT * FROM categories"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"
        rows = conn.execute(query).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_by_id(cls, category_id: int) -> Optional['Category']:
        """Get category by ID"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
        conn.close()
        if row:
            return cls(**dict(row))
        return None

    def save(self):
        """Save or update category"""
        conn = get_connection()
        if self.id:
            conn.execute("""
                UPDATE categories SET name=?, description=?, is_active=? WHERE id=?
            """, (self.name, self.description, self.is_active, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO categories (name, description, is_active) VALUES (?, ?, ?)
            """, (self.name, self.description, self.is_active))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    def delete(self):
        """Soft delete category"""
        self.is_active = False
        self.save()


@dataclass
class HeldBill:
    """Held bill for hold/recall feature"""
    id: Optional[int] = None
    hold_name: str = ""
    customer_id: Optional[int] = None
    customer_name: str = ""
    items_json: str = "[]"
    discount: float = 0.0
    created_at: Optional[datetime] = None

    @classmethod
    def get_all(cls) -> List['HeldBill']:
        """Get all held bills"""
        conn = get_connection()
        rows = conn.execute("SELECT * FROM held_bills ORDER BY created_at DESC").fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_by_id(cls, bill_id: int) -> Optional['HeldBill']:
        """Get held bill by ID"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM held_bills WHERE id = ?", (bill_id,)).fetchone()
        conn.close()
        if row:
            return cls(**dict(row))
        return None

    def save(self):
        """Save held bill"""
        conn = get_connection()
        if self.id:
            conn.execute("""
                UPDATE held_bills SET hold_name=?, customer_id=?, customer_name=?,
                items_json=?, discount=? WHERE id=?
            """, (self.hold_name, self.customer_id, self.customer_name,
                  self.items_json, self.discount, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO held_bills (hold_name, customer_id, customer_name, items_json, discount)
                VALUES (?, ?, ?, ?, ?)
            """, (self.hold_name, self.customer_id, self.customer_name,
                  self.items_json, self.discount))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    def delete(self):
        """Delete held bill"""
        conn = get_connection()
        conn.execute("DELETE FROM held_bills WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()


@dataclass
class AppSettings:
    """Application settings (key-value store)"""
    key: str = ""
    value: str = ""

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        """Get a setting value"""
        conn = get_connection()
        row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        conn.close()
        if row:
            return row['value']
        return default

    @classmethod
    def set(cls, key: str, value: str):
        """Set a setting value"""
        conn = get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)
        """, (key, value))
        conn.commit()
        conn.close()

    @classmethod
    def get_all(cls) -> dict:
        """Get all settings as a dictionary"""
        conn = get_connection()
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        conn.close()
        return {row['key']: row['value'] for row in rows}

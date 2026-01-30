"""Data models and CRUD operations"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date, datetime, timedelta
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
    # Batch and Expiry tracking (for pharmaceuticals)
    batch_number: str = ""
    expiry_date: Optional[date] = None

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
        expiry_str = self.expiry_date.isoformat() if self.expiry_date else None
        if self.id:
            conn.execute("""
                UPDATE products SET name=?, barcode=?, hsn_code=?, unit=?, price=?,
                gst_rate=?, stock_qty=?, low_stock_alert=?, is_active=?, category_id=?, purchase_price=?,
                batch_number=?, expiry_date=? WHERE id=?
            """, (self.name, self.barcode, self.hsn_code, self.unit, self.price,
                  self.gst_rate, self.stock_qty, self.low_stock_alert, self.is_active,
                  self.category_id, self.purchase_price, self.batch_number, expiry_str, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO products (name, barcode, hsn_code, unit, price, gst_rate, stock_qty, low_stock_alert, is_active, category_id, purchase_price, batch_number, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.name, self.barcode, self.hsn_code, self.unit, self.price,
                  self.gst_rate, self.stock_qty, self.low_stock_alert, self.is_active,
                  self.category_id, self.purchase_price, self.batch_number, expiry_str))
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
    pin_code: str = ""
    # Drug License Number (for pharmaceutical customers)
    dl_number: str = ""

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
                credit_balance=?, credit_limit=?, pin_code=?, dl_number=? WHERE id=?
            """, (self.name, self.phone, self.address, self.gstin, self.state_code, self.is_active,
                  self.credit_balance, self.credit_limit, self.pin_code, self.dl_number, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO customers (name, phone, address, gstin, state_code, is_active, credit_balance, credit_limit, pin_code, dl_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.name, self.phone, self.address, self.gstin, self.state_code, self.is_active,
                  self.credit_balance, self.credit_limit, self.pin_code, self.dl_number))
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
    # Batch tracking for invoice items
    batch_number: str = ""


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
    # e-Way Bill fields
    vehicle_number: str = ""
    transport_mode: str = "Road"
    transport_distance: int = 0
    transporter_id: str = ""
    eway_bill_number: str = ""
    # Payment tracking fields (CRITICAL - must match database schema)
    amount_paid: float = 0.0
    balance_due: float = 0.0
    payment_status: str = "PAID"  # UNPAID, PARTIAL, PAID

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
    def get_by_date_range(cls, start_date: date, end_date: date, include_cancelled: bool = True) -> List['Invoice']:
        """Get invoices in date range"""
        conn = get_connection()
        if include_cancelled:
            rows = conn.execute("""
                SELECT * FROM invoices
                WHERE invoice_date BETWEEN ? AND ?
                ORDER BY invoice_date DESC, id DESC
            """, (start_date.isoformat(), end_date.isoformat())).fetchall()
        else:
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
                discount=?, grand_total=?, payment_mode=?, is_cancelled=?,
                amount_paid=?, balance_due=?, payment_status=?,
                vehicle_number=?, transport_mode=?, transport_distance=?,
                transporter_id=?, eway_bill_number=?
                WHERE id=?
            """, (self.invoice_number, self.invoice_date.isoformat(), self.customer_id,
                  self.customer_name, self.subtotal, self.cgst_total, self.sgst_total,
                  self.igst_total, self.discount, self.grand_total, self.payment_mode,
                  self.is_cancelled, self.amount_paid, self.balance_due, self.payment_status,
                  self.vehicle_number, self.transport_mode, self.transport_distance,
                  self.transporter_id, self.eway_bill_number, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO invoices (invoice_number, invoice_date, customer_id, customer_name,
                subtotal, cgst_total, sgst_total, igst_total, discount, grand_total, payment_mode,
                is_cancelled, amount_paid, balance_due, payment_status,
                vehicle_number, transport_mode, transport_distance, transporter_id, eway_bill_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.invoice_number, self.invoice_date.isoformat(), self.customer_id,
                  self.customer_name, self.subtotal, self.cgst_total, self.sgst_total,
                  self.igst_total, self.discount, self.grand_total, self.payment_mode,
                  self.is_cancelled, self.amount_paid, self.balance_due, self.payment_status,
                  self.vehicle_number, self.transport_mode, self.transport_distance,
                  self.transporter_id, self.eway_bill_number))
            self.id = cursor.lastrowid

        # Delete existing items and re-insert
        conn.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (self.id,))

        for item in self.items:
            item.invoice_id = self.id
            conn.execute("""
                INSERT INTO invoice_items (invoice_id, product_id, product_name, hsn_code,
                qty, unit, rate, gst_rate, taxable_value, cgst, sgst, igst, total, batch_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item.invoice_id, item.product_id, item.product_name, item.hsn_code,
                  item.qty, item.unit, item.rate, item.gst_rate, item.taxable_value,
                  item.cgst, item.sgst, item.igst, item.total, item.batch_number))

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


@dataclass
class InvoicePayment:
    """Payment record for split payments"""
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    payment_mode: str = "CASH"
    amount: float = 0.0
    payment_date: date = field(default_factory=date.today)
    reference_number: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None

    @classmethod
    def get_by_invoice(cls, invoice_id: int) -> List['InvoicePayment']:
        """Get all payments for an invoice"""
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM invoice_payments
            WHERE invoice_id = ?
            ORDER BY payment_date, id
        """, (invoice_id,)).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_by_date_range(cls, start_date: date, end_date: date) -> List['InvoicePayment']:
        """Get payments in date range"""
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM invoice_payments
            WHERE payment_date BETWEEN ? AND ?
            ORDER BY payment_date DESC, id DESC
        """, (start_date.isoformat(), end_date.isoformat())).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    def save(self):
        """Save payment record"""
        conn = get_connection()
        if self.id:
            conn.execute("""
                UPDATE invoice_payments SET invoice_id=?, payment_mode=?, amount=?,
                payment_date=?, reference_number=?, notes=? WHERE id=?
            """, (self.invoice_id, self.payment_mode, self.amount,
                  self.payment_date.isoformat(), self.reference_number, self.notes, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO invoice_payments (invoice_id, payment_mode, amount, payment_date, reference_number, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.invoice_id, self.payment_mode, self.amount,
                  self.payment_date.isoformat(), self.reference_number, self.notes))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    def delete(self):
        """Delete payment record"""
        conn = get_connection()
        conn.execute("DELETE FROM invoice_payments WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()


@dataclass
class CreditNoteItem:
    """Credit note line item"""
    id: Optional[int] = None
    credit_note_id: Optional[int] = None
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
class CreditNote:
    """Credit note for returns and refunds"""
    id: Optional[int] = None
    credit_note_number: str = ""
    credit_note_date: date = field(default_factory=date.today)
    original_invoice_id: Optional[int] = None
    original_invoice_number: str = ""
    customer_id: Optional[int] = None
    customer_name: str = ""
    reason: str = "RETURN"  # RETURN, DAMAGE, PRICE_ADJUSTMENT, OTHER
    reason_details: str = ""
    subtotal: float = 0.0
    cgst_total: float = 0.0
    sgst_total: float = 0.0
    igst_total: float = 0.0
    grand_total: float = 0.0
    status: str = "ACTIVE"  # ACTIVE, APPLIED, CANCELLED
    created_at: Optional[datetime] = None
    items: List[CreditNoteItem] = field(default_factory=list)

    @classmethod
    def get_by_id(cls, credit_note_id: int) -> Optional['CreditNote']:
        """Get credit note by ID with items"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM credit_notes WHERE id = ?", (credit_note_id,)).fetchone()
        if not row:
            conn.close()
            return None

        credit_note = cls(**{k: v for k, v in dict(row).items() if k != 'items'})

        # Get items
        items = conn.execute("SELECT * FROM credit_note_items WHERE credit_note_id = ?", (credit_note_id,)).fetchall()
        credit_note.items = [CreditNoteItem(**dict(item)) for item in items]

        conn.close()
        return credit_note

    @classmethod
    def get_by_number(cls, credit_note_number: str) -> Optional['CreditNote']:
        """Get credit note by number"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM credit_notes WHERE credit_note_number = ?", (credit_note_number,)).fetchone()
        conn.close()
        if row:
            return cls.get_by_id(row['id'])
        return None

    @classmethod
    def get_by_date_range(cls, start_date: date, end_date: date, include_cancelled: bool = False) -> List['CreditNote']:
        """Get credit notes in date range"""
        conn = get_connection()
        if include_cancelled:
            rows = conn.execute("""
                SELECT * FROM credit_notes
                WHERE credit_note_date BETWEEN ? AND ?
                ORDER BY credit_note_date DESC, id DESC
            """, (start_date.isoformat(), end_date.isoformat())).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM credit_notes
                WHERE credit_note_date BETWEEN ? AND ? AND status != 'CANCELLED'
                ORDER BY credit_note_date DESC, id DESC
            """, (start_date.isoformat(), end_date.isoformat())).fetchall()
        conn.close()
        return [cls.get_by_id(row['id']) for row in rows]

    @classmethod
    def get_by_invoice(cls, invoice_id: int) -> List['CreditNote']:
        """Get credit notes for an invoice"""
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM credit_notes
            WHERE original_invoice_id = ?
            ORDER BY credit_note_date DESC
        """, (invoice_id,)).fetchall()
        conn.close()
        return [cls.get_by_id(row['id']) for row in rows]

    @classmethod
    def get_next_credit_note_number(cls) -> str:
        """Generate next credit note number"""
        from config import FINANCIAL_YEAR_START_MONTH

        today = date.today()
        if today.month >= FINANCIAL_YEAR_START_MONTH:
            fy_start = today.year
            fy_end = today.year + 1
        else:
            fy_start = today.year - 1
            fy_end = today.year

        fy_str = f"{fy_start}-{str(fy_end)[-2:]}"
        prefix = f"CN/{fy_str}/"

        conn = get_connection()
        row = conn.execute("""
            SELECT credit_note_number FROM credit_notes
            WHERE credit_note_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f"{prefix}%",)).fetchone()
        conn.close()

        if row:
            try:
                last_num = int(row['credit_note_number'].split('/')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"

    def save(self):
        """Save credit note and items"""
        conn = get_connection()

        if self.id:
            conn.execute("""
                UPDATE credit_notes SET credit_note_number=?, credit_note_date=?,
                original_invoice_id=?, original_invoice_number=?, customer_id=?,
                customer_name=?, reason=?, reason_details=?, subtotal=?, cgst_total=?,
                sgst_total=?, igst_total=?, grand_total=?, status=?
                WHERE id=?
            """, (self.credit_note_number, self.credit_note_date.isoformat(),
                  self.original_invoice_id, self.original_invoice_number, self.customer_id,
                  self.customer_name, self.reason, self.reason_details, self.subtotal,
                  self.cgst_total, self.sgst_total, self.igst_total, self.grand_total,
                  self.status, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO credit_notes (credit_note_number, credit_note_date,
                original_invoice_id, original_invoice_number, customer_id, customer_name,
                reason, reason_details, subtotal, cgst_total, sgst_total, igst_total,
                grand_total, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.credit_note_number, self.credit_note_date.isoformat(),
                  self.original_invoice_id, self.original_invoice_number, self.customer_id,
                  self.customer_name, self.reason, self.reason_details, self.subtotal,
                  self.cgst_total, self.sgst_total, self.igst_total, self.grand_total,
                  self.status))
            self.id = cursor.lastrowid

        # Delete existing items and re-insert
        conn.execute("DELETE FROM credit_note_items WHERE credit_note_id = ?", (self.id,))

        for item in self.items:
            item.credit_note_id = self.id
            conn.execute("""
                INSERT INTO credit_note_items (credit_note_id, product_id, product_name, hsn_code,
                qty, unit, rate, gst_rate, taxable_value, cgst, sgst, igst, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item.credit_note_id, item.product_id, item.product_name, item.hsn_code,
                  item.qty, item.unit, item.rate, item.gst_rate, item.taxable_value,
                  item.cgst, item.sgst, item.igst, item.total))

        conn.commit()
        conn.close()

    def cancel(self):
        """Cancel credit note"""
        self.status = "CANCELLED"
        conn = get_connection()
        conn.execute("UPDATE credit_notes SET status = 'CANCELLED' WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()


@dataclass
class QuotationItem:
    """Quotation line item"""
    id: Optional[int] = None
    quotation_id: Optional[int] = None
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
class Quotation:
    """Quotation/Estimate model"""
    id: Optional[int] = None
    quotation_number: str = ""
    quotation_date: date = field(default_factory=date.today)
    validity_date: date = field(default_factory=lambda: date.today() + timedelta(days=30))
    customer_id: Optional[int] = None
    customer_name: str = ""
    subtotal: float = 0.0
    cgst_total: float = 0.0
    sgst_total: float = 0.0
    igst_total: float = 0.0
    discount: float = 0.0
    grand_total: float = 0.0
    status: str = "DRAFT"  # DRAFT, SENT, ACCEPTED, REJECTED, EXPIRED, CONVERTED
    notes: str = ""
    terms_conditions: str = ""
    converted_invoice_id: Optional[int] = None
    created_at: Optional[datetime] = None
    items: List[QuotationItem] = field(default_factory=list)

    # Class constants
    STATUSES = ["DRAFT", "SENT", "ACCEPTED", "REJECTED", "EXPIRED", "CONVERTED"]
    DEFAULT_VALIDITY_DAYS = 30

    @classmethod
    def get_by_id(cls, quotation_id: int) -> Optional['Quotation']:
        """Get quotation by ID with items"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM quotations WHERE id = ?", (quotation_id,)).fetchone()
        if not row:
            conn.close()
            return None

        quotation = cls(**{k: v for k, v in dict(row).items() if k != 'items'})

        # Convert date strings to date objects
        if isinstance(quotation.quotation_date, str):
            quotation.quotation_date = date.fromisoformat(quotation.quotation_date)
        if isinstance(quotation.validity_date, str):
            quotation.validity_date = date.fromisoformat(quotation.validity_date)

        # Get items
        items = conn.execute("SELECT * FROM quotation_items WHERE quotation_id = ?", (quotation_id,)).fetchall()
        quotation.items = [QuotationItem(**dict(item)) for item in items]

        conn.close()
        return quotation

    @classmethod
    def get_by_number(cls, quotation_number: str) -> Optional['Quotation']:
        """Get quotation by number"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM quotations WHERE quotation_number = ?", (quotation_number,)).fetchone()
        conn.close()
        if row:
            return cls.get_by_id(row['id'])
        return None

    @classmethod
    def get_by_date_range(cls, start_date: date, end_date: date, status: str = None) -> List['Quotation']:
        """Get quotations in date range, optionally filtered by status"""
        conn = get_connection()
        if status:
            rows = conn.execute("""
                SELECT * FROM quotations
                WHERE quotation_date BETWEEN ? AND ? AND status = ?
                ORDER BY quotation_date DESC, id DESC
            """, (start_date.isoformat(), end_date.isoformat(), status)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM quotations
                WHERE quotation_date BETWEEN ? AND ?
                ORDER BY quotation_date DESC, id DESC
            """, (start_date.isoformat(), end_date.isoformat())).fetchall()
        conn.close()
        return [cls.get_by_id(row['id']) for row in rows]

    @classmethod
    def get_by_customer(cls, customer_id: int) -> List['Quotation']:
        """Get quotations for a customer"""
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM quotations
            WHERE customer_id = ?
            ORDER BY quotation_date DESC
        """, (customer_id,)).fetchall()
        conn.close()
        return [cls.get_by_id(row['id']) for row in rows]

    @classmethod
    def get_expiring_soon(cls, days: int = 7) -> List['Quotation']:
        """Get quotations expiring within N days"""
        today = date.today()
        expiry_date = today + timedelta(days=days)
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM quotations
            WHERE validity_date BETWEEN ? AND ? AND status IN ('DRAFT', 'SENT')
            ORDER BY validity_date
        """, (today.isoformat(), expiry_date.isoformat())).fetchall()
        conn.close()
        return [cls.get_by_id(row['id']) for row in rows]

    @classmethod
    def get_next_quotation_number(cls) -> str:
        """Generate next quotation number (QTN/FY/0001)"""
        from config import FINANCIAL_YEAR_START_MONTH

        today = date.today()
        if today.month >= FINANCIAL_YEAR_START_MONTH:
            fy_start = today.year
            fy_end = today.year + 1
        else:
            fy_start = today.year - 1
            fy_end = today.year

        fy_str = f"{fy_start}-{str(fy_end)[-2:]}"
        prefix = f"QTN/{fy_str}/"

        conn = get_connection()
        row = conn.execute("""
            SELECT quotation_number FROM quotations
            WHERE quotation_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f"{prefix}%",)).fetchone()
        conn.close()

        if row:
            try:
                last_num = int(row['quotation_number'].split('/')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}{next_num:04d}"

    def save(self):
        """Save quotation and items"""
        conn = get_connection()

        if self.id:
            conn.execute("""
                UPDATE quotations SET quotation_number=?, quotation_date=?, validity_date=?,
                customer_id=?, customer_name=?, subtotal=?, cgst_total=?, sgst_total=?,
                igst_total=?, discount=?, grand_total=?, status=?, notes=?,
                terms_conditions=?, converted_invoice_id=?
                WHERE id=?
            """, (self.quotation_number, self.quotation_date.isoformat(),
                  self.validity_date.isoformat(), self.customer_id, self.customer_name,
                  self.subtotal, self.cgst_total, self.sgst_total, self.igst_total,
                  self.discount, self.grand_total, self.status, self.notes,
                  self.terms_conditions, self.converted_invoice_id, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO quotations (quotation_number, quotation_date, validity_date,
                customer_id, customer_name, subtotal, cgst_total, sgst_total, igst_total,
                discount, grand_total, status, notes, terms_conditions, converted_invoice_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.quotation_number, self.quotation_date.isoformat(),
                  self.validity_date.isoformat(), self.customer_id, self.customer_name,
                  self.subtotal, self.cgst_total, self.sgst_total, self.igst_total,
                  self.discount, self.grand_total, self.status, self.notes,
                  self.terms_conditions, self.converted_invoice_id))
            self.id = cursor.lastrowid

        # Delete existing items and re-insert
        conn.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (self.id,))

        for item in self.items:
            item.quotation_id = self.id
            conn.execute("""
                INSERT INTO quotation_items (quotation_id, product_id, product_name, hsn_code,
                qty, unit, rate, gst_rate, taxable_value, cgst, sgst, igst, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item.quotation_id, item.product_id, item.product_name, item.hsn_code,
                  item.qty, item.unit, item.rate, item.gst_rate, item.taxable_value,
                  item.cgst, item.sgst, item.igst, item.total))

        conn.commit()
        conn.close()

    def update_status(self, new_status: str):
        """Update quotation status"""
        if new_status in self.STATUSES:
            self.status = new_status
            conn = get_connection()
            conn.execute("UPDATE quotations SET status = ? WHERE id = ?", (new_status, self.id))
            conn.commit()
            conn.close()

    def is_expired(self) -> bool:
        """Check if quotation has expired"""
        return date.today() > self.validity_date and self.status in ('DRAFT', 'SENT')

    def delete(self):
        """Delete quotation and items"""
        conn = get_connection()
        conn.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (self.id,))
        conn.execute("DELETE FROM quotations WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()


@dataclass
class EmailQueueEntry:
    """Email queue entry for offline email support"""
    id: Optional[int] = None
    invoice_id: int = 0
    recipient_email: str = ""
    subject: str = ""
    body: str = ""
    pdf_data: Optional[bytes] = None
    status: str = "PENDING"  # PENDING, SENDING, SENT, FAILED
    retry_count: int = 0
    error_message: str = ""
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    @classmethod
    def get_by_id(cls, entry_id: int) -> Optional['EmailQueueEntry']:
        """Get queue entry by ID"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM email_queue WHERE id = ?", (entry_id,)).fetchone()
        conn.close()
        if row:
            return cls(**dict(row))
        return None

    @classmethod
    def get_pending(cls) -> List['EmailQueueEntry']:
        """Get pending emails (including retryable failed ones)"""
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM email_queue
            WHERE status = 'PENDING' OR (status = 'FAILED' AND retry_count < 3)
            ORDER BY created_at ASC
        """).fetchall()
        conn.close()
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_by_invoice(cls, invoice_id: int) -> Optional['EmailQueueEntry']:
        """Get queue entry for an invoice"""
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM email_queue WHERE invoice_id = ? ORDER BY created_at DESC LIMIT 1",
            (invoice_id,)
        ).fetchone()
        conn.close()
        if row:
            return cls(**dict(row))
        return None

    def save(self):
        """Save or update queue entry"""
        conn = get_connection()
        if self.id:
            conn.execute("""
                UPDATE email_queue SET invoice_id=?, recipient_email=?, subject=?,
                body=?, pdf_data=?, status=?, retry_count=?, error_message=?, sent_at=?
                WHERE id=?
            """, (self.invoice_id, self.recipient_email, self.subject, self.body,
                  self.pdf_data, self.status, self.retry_count, self.error_message,
                  self.sent_at, self.id))
        else:
            cursor = conn.execute("""
                INSERT INTO email_queue (invoice_id, recipient_email, subject, body,
                pdf_data, status, retry_count, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.invoice_id, self.recipient_email, self.subject, self.body,
                  self.pdf_data, self.status, self.retry_count, self.error_message))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    def delete(self):
        """Delete queue entry"""
        conn = get_connection()
        conn.execute("DELETE FROM email_queue WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()

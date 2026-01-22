"""Invoice and InvoiceItem models for SQLAlchemy"""
from datetime import date, datetime
from app.extensions import db


class Invoice(db.Model):
    """Invoice model"""
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_name = db.Column(db.String(200), default='')

    # Totals
    subtotal = db.Column(db.Float, default=0.0)
    cgst_total = db.Column(db.Float, default=0.0)
    sgst_total = db.Column(db.Float, default=0.0)
    igst_total = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    grand_total = db.Column(db.Float, default=0.0)

    # Payment
    payment_mode = db.Column(db.String(20), default='CASH')
    amount_paid = db.Column(db.Float, default=0.0)
    balance_due = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='PAID')  # PAID, PARTIAL, UNPAID

    # Status
    is_cancelled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # e-Way Bill fields
    vehicle_number = db.Column(db.String(20), default='')
    transport_mode = db.Column(db.String(20), default='Road')
    transport_distance = db.Column(db.Integer, default=0)
    transporter_id = db.Column(db.String(20), default='')
    eway_bill_number = db.Column(db.String(20), default='')

    # Relationships
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic',
                           cascade='all, delete-orphan')
    payments = db.relationship('InvoicePayment', backref='invoice', lazy='dynamic',
                              cascade='all, delete-orphan')

    @classmethod
    def get_by_id(cls, invoice_id):
        """Get invoice by ID"""
        return cls.query.get(invoice_id)

    @classmethod
    def get_by_number(cls, invoice_number):
        """Get invoice by number"""
        return cls.query.filter_by(invoice_number=invoice_number).first()

    @classmethod
    def get_by_date_range(cls, start_date, end_date, include_cancelled=False):
        """Get invoices in date range"""
        query = cls.query.filter(cls.invoice_date.between(start_date, end_date))
        if not include_cancelled:
            query = query.filter_by(is_cancelled=False)
        return query.order_by(cls.invoice_date.desc(), cls.id.desc()).all()

    @classmethod
    def get_recent(cls, limit=10):
        """Get recent invoices"""
        return cls.query.filter_by(is_cancelled=False)\
            .order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_next_invoice_number(cls, prefix='INV', fy_start_month=4):
        """Generate next invoice number"""
        today = date.today()
        if today.month >= fy_start_month:
            fy_start = today.year
            fy_end = today.year + 1
        else:
            fy_start = today.year - 1
            fy_end = today.year

        fy_str = f"{fy_start}-{str(fy_end)[-2:]}"
        prefix_str = f"{prefix}/{fy_str}/"

        last_invoice = cls.query.filter(
            cls.invoice_number.like(f"{prefix_str}%")
        ).order_by(cls.id.desc()).first()

        if last_invoice:
            try:
                last_num = int(last_invoice.invoice_number.split('/')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        return f"{prefix_str}{next_num:04d}"

    def save(self):
        """Save invoice"""
        db.session.add(self)
        db.session.commit()

    def cancel(self):
        """Cancel invoice"""
        self.is_cancelled = True
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'subtotal': self.subtotal,
            'cgst_total': self.cgst_total,
            'sgst_total': self.sgst_total,
            'igst_total': self.igst_total,
            'discount': self.discount,
            'grand_total': self.grand_total,
            'payment_mode': self.payment_mode,
            'payment_status': self.payment_status,
            'is_cancelled': self.is_cancelled,
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class InvoiceItem(db.Model):
    """Invoice line item"""
    __tablename__ = 'invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    product_name = db.Column(db.String(200), default='')
    hsn_code = db.Column(db.String(20), default='')
    qty = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(20), default='NOS')
    rate = db.Column(db.Float, default=0.0)
    gst_rate = db.Column(db.Float, default=0.0)
    taxable_value = db.Column(db.Float, default=0.0)
    cgst = db.Column(db.Float, default=0.0)
    sgst = db.Column(db.Float, default=0.0)
    igst = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'hsn_code': self.hsn_code,
            'qty': self.qty,
            'unit': self.unit,
            'rate': self.rate,
            'gst_rate': self.gst_rate,
            'taxable_value': self.taxable_value,
            'cgst': self.cgst,
            'sgst': self.sgst,
            'igst': self.igst,
            'total': self.total
        }

    def __repr__(self):
        return f'<InvoiceItem {self.product_name}>'


class InvoicePayment(db.Model):
    """Payment record for invoices"""
    __tablename__ = 'invoice_payments'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    payment_mode = db.Column(db.String(20), default='CASH')
    amount = db.Column(db.Float, default=0.0)
    payment_date = db.Column(db.Date, default=date.today)
    reference_number = db.Column(db.String(50), default='')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def get_by_invoice(cls, invoice_id):
        """Get all payments for an invoice"""
        return cls.query.filter_by(invoice_id=invoice_id)\
            .order_by(cls.payment_date, cls.id).all()

    def save(self):
        """Save payment"""
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f'<InvoicePayment {self.amount}>'

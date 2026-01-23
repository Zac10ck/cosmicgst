"""DebitNote and DebitNoteItem models for SQLAlchemy"""
from datetime import date, datetime
from app.extensions import db


class DebitNote(db.Model):
    """Debit note for additional charges or corrections that increase tax liability"""
    __tablename__ = 'debit_notes'

    id = db.Column(db.Integer, primary_key=True)
    debit_note_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    debit_note_date = db.Column(db.Date, nullable=False, default=date.today)

    # Link to original invoice
    original_invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    original_invoice_number = db.Column(db.String(50), default='')

    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_name = db.Column(db.String(200), default='')

    # Reason: PRICE_INCREASE, ADDITIONAL_CHARGES, TAX_CORRECTION, OTHER
    reason = db.Column(db.String(30), default='PRICE_INCREASE')
    reason_details = db.Column(db.Text, default='')

    # Totals
    subtotal = db.Column(db.Float, default=0.0)
    cgst_total = db.Column(db.Float, default=0.0)
    sgst_total = db.Column(db.Float, default=0.0)
    igst_total = db.Column(db.Float, default=0.0)
    grand_total = db.Column(db.Float, default=0.0)

    # Status: ACTIVE, APPLIED, CANCELLED
    status = db.Column(db.String(20), default='ACTIVE')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    items = db.relationship('DebitNoteItem', backref='debit_note', lazy='dynamic',
                           cascade='all, delete-orphan')
    original_invoice = db.relationship('Invoice', foreign_keys=[original_invoice_id])

    # Constants
    REASONS = [
        ('PRICE_INCREASE', 'Price Increase'),
        ('ADDITIONAL_CHARGES', 'Additional Charges'),
        ('TAX_CORRECTION', 'Tax Rate Correction'),
        ('SHORTAGE', 'Short Delivery Correction'),
        ('OTHER', 'Other')
    ]
    STATUSES = ['ACTIVE', 'APPLIED', 'CANCELLED']

    @classmethod
    def get_by_id(cls, debit_note_id):
        """Get debit note by ID"""
        return cls.query.get(debit_note_id)

    @classmethod
    def get_by_number(cls, debit_note_number):
        """Get debit note by number"""
        return cls.query.filter_by(debit_note_number=debit_note_number).first()

    @classmethod
    def get_by_date_range(cls, start_date, end_date, include_cancelled=False):
        """Get debit notes in date range"""
        query = cls.query.filter(cls.debit_note_date.between(start_date, end_date))
        if not include_cancelled:
            query = query.filter(cls.status != 'CANCELLED')
        return query.order_by(cls.debit_note_date.desc(), cls.id.desc()).all()

    @classmethod
    def get_by_invoice(cls, invoice_id):
        """Get debit notes for an invoice"""
        return cls.query.filter_by(original_invoice_id=invoice_id)\
            .order_by(cls.debit_note_date.desc()).all()

    @classmethod
    def get_active(cls):
        """Get active debit notes"""
        return cls.query.filter_by(status='ACTIVE')\
            .order_by(cls.debit_note_date.desc()).all()

    @classmethod
    def get_next_debit_note_number(cls, prefix='DN', fy_start_month=4):
        """Generate next debit note number"""
        today = date.today()
        if today.month >= fy_start_month:
            fy_start = today.year
            fy_end = today.year + 1
        else:
            fy_start = today.year - 1
            fy_end = today.year

        fy_str = f"{fy_start}-{str(fy_end)[-2:]}"
        prefix_str = f"{prefix}/{fy_str}/"

        last_dn = cls.query.filter(
            cls.debit_note_number.like(f"{prefix_str}%")
        ).order_by(cls.id.desc()).first()

        if last_dn:
            try:
                last_num = int(last_dn.debit_note_number.split('/')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        return f"{prefix_str}{next_num:04d}"

    def save(self):
        """Save debit note"""
        db.session.add(self)
        db.session.commit()

    def cancel(self):
        """Cancel debit note"""
        self.status = 'CANCELLED'
        db.session.commit()

    def apply(self):
        """Mark debit note as applied"""
        self.status = 'APPLIED'
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'debit_note_number': self.debit_note_number,
            'debit_note_date': self.debit_note_date.isoformat() if self.debit_note_date else None,
            'original_invoice_id': self.original_invoice_id,
            'original_invoice_number': self.original_invoice_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'reason': self.reason,
            'reason_details': self.reason_details,
            'subtotal': self.subtotal,
            'cgst_total': self.cgst_total,
            'sgst_total': self.sgst_total,
            'igst_total': self.igst_total,
            'grand_total': self.grand_total,
            'status': self.status,
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f'<DebitNote {self.debit_note_number}>'


class DebitNoteItem(db.Model):
    """Debit note line item"""
    __tablename__ = 'debit_note_items'

    id = db.Column(db.Integer, primary_key=True)
    debit_note_id = db.Column(db.Integer, db.ForeignKey('debit_notes.id'), nullable=False)
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
        return f'<DebitNoteItem {self.product_name}>'

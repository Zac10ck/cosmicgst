"""Quotation and QuotationItem models for SQLAlchemy"""
from datetime import date, datetime, timedelta
from app.extensions import db


class Quotation(db.Model):
    """Quotation/Estimate model"""
    __tablename__ = 'quotations'

    id = db.Column(db.Integer, primary_key=True)
    quotation_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    quotation_date = db.Column(db.Date, nullable=False, default=date.today)
    validity_date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_name = db.Column(db.String(200), default='')

    # Totals
    subtotal = db.Column(db.Float, default=0.0)
    cgst_total = db.Column(db.Float, default=0.0)
    sgst_total = db.Column(db.Float, default=0.0)
    igst_total = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    grand_total = db.Column(db.Float, default=0.0)

    # Status: DRAFT, SENT, ACCEPTED, REJECTED, EXPIRED, CONVERTED
    status = db.Column(db.String(20), default='DRAFT')
    notes = db.Column(db.Text, default='')
    terms_conditions = db.Column(db.Text, default='')

    # Conversion tracking
    converted_invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    items = db.relationship('QuotationItem', backref='quotation', lazy='dynamic',
                           cascade='all, delete-orphan')
    converted_invoice = db.relationship('Invoice', foreign_keys=[converted_invoice_id])

    # Constants
    STATUSES = ['DRAFT', 'SENT', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'CONVERTED']
    DEFAULT_VALIDITY_DAYS = 30

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.validity_date:
            self.validity_date = date.today() + timedelta(days=self.DEFAULT_VALIDITY_DAYS)

    @classmethod
    def get_by_id(cls, quotation_id):
        """Get quotation by ID"""
        return cls.query.get(quotation_id)

    @classmethod
    def get_by_number(cls, quotation_number):
        """Get quotation by number"""
        return cls.query.filter_by(quotation_number=quotation_number).first()

    @classmethod
    def get_by_date_range(cls, start_date, end_date, status=None):
        """Get quotations in date range"""
        query = cls.query.filter(cls.quotation_date.between(start_date, end_date))
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.quotation_date.desc(), cls.id.desc()).all()

    @classmethod
    def get_pending(cls):
        """Get pending quotations (DRAFT or SENT)"""
        return cls.query.filter(cls.status.in_(['DRAFT', 'SENT']))\
            .order_by(cls.validity_date).all()

    @classmethod
    def get_expiring_soon(cls, days=7):
        """Get quotations expiring within N days"""
        today = date.today()
        expiry_date = today + timedelta(days=days)
        return cls.query.filter(
            cls.validity_date.between(today, expiry_date),
            cls.status.in_(['DRAFT', 'SENT'])
        ).order_by(cls.validity_date).all()

    @classmethod
    def get_next_quotation_number(cls, prefix='QTN', fy_start_month=4):
        """Generate next quotation number"""
        today = date.today()
        if today.month >= fy_start_month:
            fy_start = today.year
            fy_end = today.year + 1
        else:
            fy_start = today.year - 1
            fy_end = today.year

        fy_str = f"{fy_start}-{str(fy_end)[-2:]}"
        prefix_str = f"{prefix}/{fy_str}/"

        last_quotation = cls.query.filter(
            cls.quotation_number.like(f"{prefix_str}%")
        ).order_by(cls.id.desc()).first()

        if last_quotation:
            try:
                last_num = int(last_quotation.quotation_number.split('/')[-1])
                next_num = last_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        return f"{prefix_str}{next_num:04d}"

    def save(self):
        """Save quotation"""
        db.session.add(self)
        db.session.commit()

    def update_status(self, new_status):
        """Update quotation status"""
        if new_status in self.STATUSES:
            self.status = new_status
            db.session.commit()

    def is_expired(self):
        """Check if quotation has expired"""
        return date.today() > self.validity_date and self.status in ('DRAFT', 'SENT')

    def can_convert(self):
        """Check if quotation can be converted to invoice"""
        return self.status in ('DRAFT', 'SENT', 'ACCEPTED') and not self.converted_invoice_id

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'quotation_number': self.quotation_number,
            'quotation_date': self.quotation_date.isoformat() if self.quotation_date else None,
            'validity_date': self.validity_date.isoformat() if self.validity_date else None,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'subtotal': self.subtotal,
            'cgst_total': self.cgst_total,
            'sgst_total': self.sgst_total,
            'igst_total': self.igst_total,
            'discount': self.discount,
            'grand_total': self.grand_total,
            'status': self.status,
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f'<Quotation {self.quotation_number}>'


class QuotationItem(db.Model):
    """Quotation line item"""
    __tablename__ = 'quotation_items'

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=False)
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
        return f'<QuotationItem {self.product_name}>'

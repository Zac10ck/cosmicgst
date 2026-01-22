"""Customer model for SQLAlchemy"""
from app.extensions import db


class Customer(db.Model):
    """Customer model"""
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), default='')
    address = db.Column(db.Text, default='')
    gstin = db.Column(db.String(15), default='')
    state_code = db.Column(db.String(2), default='32')
    pin_code = db.Column(db.String(10), default='')
    is_active = db.Column(db.Boolean, default=True)
    credit_balance = db.Column(db.Float, default=0.0)
    credit_limit = db.Column(db.Float, default=0.0)

    # Relationships
    invoices = db.relationship('Invoice', backref='customer', lazy='dynamic')
    quotations = db.relationship('Quotation', backref='customer', lazy='dynamic')

    @classmethod
    def get_all(cls, active_only=True):
        """Get all customers"""
        query = cls.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(cls.name).all()

    @classmethod
    def get_by_id(cls, customer_id):
        """Get customer by ID"""
        return cls.query.get(customer_id)

    @classmethod
    def search(cls, query_str, limit=20):
        """Search customers by name or phone"""
        search_term = f'%{query_str}%'
        return cls.query.filter(
            cls.is_active == True,
            db.or_(
                cls.name.ilike(search_term),
                cls.phone.ilike(search_term)
            )
        ).order_by(cls.name).limit(limit).all()

    def save(self):
        """Save or update customer"""
        db.session.add(self)
        db.session.commit()

    def update_credit(self, amount):
        """Update customer credit balance"""
        self.credit_balance += amount
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary for JSON API"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'gstin': self.gstin,
            'state_code': self.state_code,
            'pin_code': self.pin_code,
            'credit_balance': self.credit_balance,
            'credit_limit': self.credit_limit
        }

    def __repr__(self):
        return f'<Customer {self.name}>'

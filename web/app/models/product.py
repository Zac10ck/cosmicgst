"""Product model for SQLAlchemy"""
from datetime import datetime
from app.extensions import db


class Product(db.Model):
    """Product model"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    barcode = db.Column(db.String(50), index=True, default='')
    hsn_code = db.Column(db.String(20), default='')
    unit = db.Column(db.String(20), default='NOS')
    price = db.Column(db.Float, default=0.0)
    purchase_price = db.Column(db.Float, default=0.0)
    gst_rate = db.Column(db.Float, default=18.0)
    stock_qty = db.Column(db.Float, default=0.0)
    low_stock_alert = db.Column(db.Float, default=10.0)
    is_active = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    stock_logs = db.relationship('StockLog', backref='product', lazy='dynamic')

    @classmethod
    def get_all(cls, active_only=True):
        """Get all products"""
        query = cls.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(cls.name).all()

    @classmethod
    def get_by_id(cls, product_id):
        """Get product by ID"""
        return cls.query.get(product_id)

    @classmethod
    def get_by_barcode(cls, barcode):
        """Get product by barcode"""
        return cls.query.filter_by(barcode=barcode, is_active=True).first()

    @classmethod
    def search(cls, query_str, limit=20):
        """Search products by name or barcode"""
        search_term = f'%{query_str}%'
        return cls.query.filter(
            cls.is_active == True,
            db.or_(
                cls.name.ilike(search_term),
                cls.barcode.ilike(search_term)
            )
        ).order_by(cls.name).limit(limit).all()

    @classmethod
    def get_low_stock(cls):
        """Get products with low stock"""
        return cls.query.filter(
            cls.is_active == True,
            cls.stock_qty <= cls.low_stock_alert
        ).order_by(cls.stock_qty).all()

    def save(self):
        """Save or update product"""
        db.session.add(self)
        db.session.commit()

    def update_stock(self, qty_change, reason, reference_id=None):
        """Update stock quantity and log the change"""
        self.stock_qty += qty_change
        log = StockLog(
            product_id=self.id,
            change_qty=qty_change,
            reason=reason,
            reference_id=reference_id
        )
        db.session.add(log)
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary for JSON API"""
        return {
            'id': self.id,
            'name': self.name,
            'barcode': self.barcode,
            'hsn_code': self.hsn_code,
            'unit': self.unit,
            'price': self.price,
            'purchase_price': self.purchase_price,
            'gst_rate': self.gst_rate,
            'stock_qty': self.stock_qty,
            'category_id': self.category_id
        }

    def __repr__(self):
        return f'<Product {self.name}>'


class StockLog(db.Model):
    """Stock movement log"""
    __tablename__ = 'stock_log'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    change_qty = db.Column(db.Float, default=0.0)
    reason = db.Column(db.String(100), default='')
    reference_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def get_by_product(cls, product_id):
        """Get stock log for a product"""
        return cls.query.filter_by(product_id=product_id).order_by(cls.created_at.desc()).all()

    def __repr__(self):
        return f'<StockLog {self.product_id} {self.change_qty:+}>'

"""Category model for SQLAlchemy"""
from app.extensions import db


class Category(db.Model):
    """Product category model"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    is_active = db.Column(db.Boolean, default=True)

    # Relationship to products
    products = db.relationship('Product', backref='category', lazy='dynamic')

    @classmethod
    def get_all(cls, active_only=True):
        """Get all categories"""
        query = cls.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(cls.name).all()

    @classmethod
    def get_by_id(cls, category_id):
        """Get category by ID"""
        return cls.query.get(category_id)

    def save(self):
        """Save or update category"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Soft delete category"""
        self.is_active = False
        db.session.commit()

    def __repr__(self):
        return f'<Category {self.name}>'

"""Company model for SQLAlchemy"""
from app.extensions import db


class Company(db.Model):
    """Company details (singleton - only one record)"""
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, default='')
    address = db.Column(db.Text, default='')
    gstin = db.Column(db.String(15), default='')
    state_code = db.Column(db.String(2), default='32')
    phone = db.Column(db.String(20), default='')
    email = db.Column(db.String(120), default='')
    pan = db.Column(db.String(10), default='')
    logo_path = db.Column(db.String(500), default='')

    # Bank Details
    bank_name = db.Column(db.String(200), default='')
    bank_account = db.Column(db.String(50), default='')
    bank_ifsc = db.Column(db.String(11), default='')

    # Invoice Settings
    invoice_prefix = db.Column(db.String(10), default='INV')
    invoice_terms = db.Column(db.Text, default='')

    # Email Settings
    smtp_server = db.Column(db.String(200), default='')
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(200), default='')
    smtp_password = db.Column(db.String(200), default='')
    smtp_use_tls = db.Column(db.Boolean, default=True)
    email_from = db.Column(db.String(200), default='')
    admin_notification_email = db.Column(db.String(200), default='')  # Receive invoice notifications

    @classmethod
    def get(cls):
        """Get company details (singleton)"""
        return cls.query.first()

    @classmethod
    def get_or_create(cls):
        """Get company or create default"""
        company = cls.query.first()
        if not company:
            company = cls(name='My Company')
            db.session.add(company)
            db.session.commit()
        return company

    def save(self):
        """Save company details"""
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f'<Company {self.name}>'

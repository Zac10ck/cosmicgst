"""Email queue model for asynchronous email sending with retry support"""
from datetime import datetime, timedelta
from app.extensions import db


class EmailQueue(db.Model):
    """Queue for email sending with retry support"""
    __tablename__ = 'email_queue'

    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    body_text = db.Column(db.Text, nullable=False)

    # Attachment info
    attachment_type = db.Column(db.String(50), default='')  # 'invoice_pdf', etc.
    attachment_reference_id = db.Column(db.Integer, nullable=True)  # invoice_id, etc.

    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    last_error = db.Column(db.Text, default='')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)
    next_retry_at = db.Column(db.DateTime, nullable=True)

    @classmethod
    def queue_invoice_email(cls, invoice_id: int, recipient: str, subject: str,
                            body_html: str, body_text: str):
        """Queue an invoice email for sending"""
        entry = cls(
            recipient=recipient,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            attachment_type='invoice_pdf',
            attachment_reference_id=invoice_id,
            status='pending'
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    @classmethod
    def get_pending(cls, limit=10):
        """Get pending emails to send"""
        return cls.query.filter(
            cls.status == 'pending',
            db.or_(
                cls.next_retry_at.is_(None),
                cls.next_retry_at <= datetime.utcnow()
            )
        ).order_by(cls.created_at).limit(limit).all()

    @classmethod
    def get_failed(cls, limit=50):
        """Get failed emails for review"""
        return cls.query.filter(
            cls.status == 'failed'
        ).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_sent(cls, limit=50):
        """Get successfully sent emails"""
        return cls.query.filter(
            cls.status == 'sent'
        ).order_by(cls.sent_at.desc()).limit(limit).all()

    @classmethod
    def get_stats(cls):
        """Get email queue statistics"""
        return {
            'pending': cls.query.filter(cls.status == 'pending').count(),
            'sent': cls.query.filter(cls.status == 'sent').count(),
            'failed': cls.query.filter(cls.status == 'failed').count()
        }

    def mark_sent(self):
        """Mark email as successfully sent"""
        self.status = 'sent'
        self.sent_at = datetime.utcnow()
        db.session.commit()

    def mark_failed(self, error: str):
        """Mark email as failed, schedule retry if applicable"""
        self.retry_count += 1
        self.last_error = error

        if self.retry_count >= self.max_retries:
            self.status = 'failed'
        else:
            # Exponential backoff: 5min, 15min, 45min
            delay = timedelta(minutes=5 * (3 ** (self.retry_count - 1)))
            self.next_retry_at = datetime.utcnow() + delay

        db.session.commit()

    def retry(self):
        """Reset status to pending for retry"""
        self.status = 'pending'
        self.next_retry_at = None
        db.session.commit()

    def delete(self):
        """Delete email from queue"""
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'recipient': self.recipient,
            'subject': self.subject,
            'attachment_type': self.attachment_type,
            'attachment_reference_id': self.attachment_reference_id,
            'status': self.status,
            'retry_count': self.retry_count,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None
        }

    def __repr__(self):
        return f'<EmailQueue {self.id} to {self.recipient} [{self.status}]>'

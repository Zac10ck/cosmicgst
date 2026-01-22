"""Activity Log model for audit trail"""
from datetime import datetime
from app.extensions import db


class ActivityLog(db.Model):
    """Activity log for tracking user actions (audit trail)"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, DELETE, VIEW, LOGIN, LOGOUT
    entity_type = db.Column(db.String(50), nullable=False)  # Invoice, Product, Customer, etc.
    entity_id = db.Column(db.Integer, nullable=True)
    entity_name = db.Column(db.String(200), default='')
    description = db.Column(db.Text, default='')
    old_values = db.Column(db.JSON, nullable=True)  # For UPDATE actions
    new_values = db.Column(db.JSON, nullable=True)  # For CREATE/UPDATE actions
    ip_address = db.Column(db.String(50), default='')
    user_agent = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = db.relationship('User', backref='activity_logs')

    # Action types
    ACTIONS = ['CREATE', 'UPDATE', 'DELETE', 'VIEW', 'LOGIN', 'LOGOUT', 'EXPORT', 'PRINT', 'EMAIL', 'CANCEL']

    @classmethod
    def log(cls, action, entity_type, entity_id=None, entity_name='', description='',
            old_values=None, new_values=None, user_id=None, ip_address='', user_agent=''):
        """Create a new activity log entry"""
        from flask_login import current_user

        log_entry = cls(
            user_id=user_id or (current_user.id if current_user and current_user.is_authenticated else None),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else ''
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry

    @classmethod
    def log_create(cls, entity_type, entity_id, entity_name, new_values=None):
        """Log a CREATE action"""
        return cls.log(
            action='CREATE',
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            description=f'Created {entity_type}: {entity_name}',
            new_values=new_values
        )

    @classmethod
    def log_update(cls, entity_type, entity_id, entity_name, old_values=None, new_values=None):
        """Log an UPDATE action"""
        return cls.log(
            action='UPDATE',
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            description=f'Updated {entity_type}: {entity_name}',
            old_values=old_values,
            new_values=new_values
        )

    @classmethod
    def log_delete(cls, entity_type, entity_id, entity_name):
        """Log a DELETE action"""
        return cls.log(
            action='DELETE',
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            description=f'Deleted {entity_type}: {entity_name}'
        )

    @classmethod
    def log_login(cls, user_id, username, ip_address='', user_agent=''):
        """Log a LOGIN action"""
        return cls.log(
            action='LOGIN',
            entity_type='User',
            entity_id=user_id,
            entity_name=username,
            description=f'User logged in: {username}',
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @classmethod
    def log_logout(cls, user_id, username):
        """Log a LOGOUT action"""
        return cls.log(
            action='LOGOUT',
            entity_type='User',
            entity_id=user_id,
            entity_name=username,
            description=f'User logged out: {username}',
            user_id=user_id
        )

    @classmethod
    def get_recent(cls, limit=50):
        """Get recent activity logs"""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_by_user(cls, user_id, limit=100):
        """Get activity logs for a specific user"""
        return cls.query.filter_by(user_id=user_id)\
            .order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_by_entity(cls, entity_type, entity_id):
        """Get activity logs for a specific entity"""
        return cls.query.filter_by(entity_type=entity_type, entity_id=entity_id)\
            .order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_date_range(cls, start_date, end_date, action=None, entity_type=None):
        """Get activity logs within a date range"""
        query = cls.query.filter(cls.created_at.between(start_date, end_date))
        if action:
            query = query.filter_by(action=action)
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        return query.order_by(cls.created_at.desc()).all()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else 'System',
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'entity_name': self.entity_name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<ActivityLog {self.action} {self.entity_type}>'

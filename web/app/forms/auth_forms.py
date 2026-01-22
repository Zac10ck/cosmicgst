"""Authentication forms"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UserForm(FlaskForm):
    """User creation/edit form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    password = PasswordField('Password', validators=[
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('staff', 'Staff'),
        ('admin', 'Admin')
    ])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, field):
        if field.data != self.original_username:
            user = User.query.filter_by(username=field.data).first()
            if user:
                raise ValidationError('Username already exists')

    def validate_email(self, field):
        if field.data != self.original_email:
            user = User.query.filter_by(email=field.data).first()
            if user:
                raise ValidationError('Email already registered')


class ChangePasswordForm(FlaskForm):
    """Password change form"""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')

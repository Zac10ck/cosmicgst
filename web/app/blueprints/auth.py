"""Authentication blueprint"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.forms.auth_forms import LoginForm, UserForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Contact admin.', 'danger')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)
            user.update_last_login()

            # Log the login activity with IP address
            ActivityLog.log_login(
                user_id=user.id,
                username=user.username,
                ip_address=request.remote_addr,
                user_agent=str(request.user_agent)
            )

            flash(f'Welcome back, {user.username}!', 'success')

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))

        flash('Invalid username or password', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    # Log the logout activity before logging out
    ActivityLog.log(
        action='LOGOUT',
        entity_type='User',
        entity_id=current_user.id,
        entity_name=current_user.username,
        description=f'User logged out: {current_user.username}',
        user_id=current_user.id,
        ip_address=request.remote_addr,
        user_agent=str(request.user_agent)
    )
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/users')
@login_required
def manage_users():
    """Manage users (admin only)"""
    if not current_user.is_admin():
        flash('Admin access required', 'danger')
        return redirect(url_for('dashboard.index'))

    users = User.query.order_by(User.username).all()
    return render_template('auth/manage_users.html', users=users)


@auth_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """Add new user (admin only)"""
    if not current_user.is_admin():
        flash('Admin access required', 'danger')
        return redirect(url_for('dashboard.index'))

    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('auth.manage_users'))

    return render_template('auth/user_form.html', form=form, title='Add User')


@auth_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    """Edit user (admin only)"""
    if not current_user.is_admin():
        flash('Admin access required', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(id)
    form = UserForm(original_username=user.username, original_email=user.email, obj=user)

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data

        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('auth.manage_users'))

    return render_template('auth/user_form.html', form=form, title='Edit User', user=user)


@auth_bp.route('/users/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_user(id):
    """Toggle user active status (admin only)"""
    if not current_user.is_admin():
        flash('Admin access required', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'warning')
        return redirect(url_for('auth.manage_users'))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} {status}', 'success')
    return redirect(url_for('auth.manage_users'))

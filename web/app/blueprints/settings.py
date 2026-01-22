"""Settings blueprint - Company settings, email config, categories"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.company import Company
from app.models.category import Category
from functools import wraps

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@settings_bp.route('/')
@login_required
@admin_required
def index():
    """Settings dashboard"""
    company = Company.get()
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return render_template(
        'settings/index.html',
        company=company,
        categories=categories
    )


@settings_bp.route('/company', methods=['GET', 'POST'])
@login_required
@admin_required
def company():
    """Company settings"""
    company = Company.get()

    if request.method == 'POST':
        if not company:
            company = Company()

        company.name = request.form.get('name', '').strip()
        company.address = request.form.get('address', '').strip()
        company.gstin = request.form.get('gstin', '').strip().upper()
        company.state_code = request.form.get('state_code', '32').strip()
        company.phone = request.form.get('phone', '').strip()
        company.email = request.form.get('email', '').strip()
        company.bank_name = request.form.get('bank_name', '').strip()
        company.bank_account = request.form.get('bank_account', '').strip()
        company.bank_ifsc = request.form.get('bank_ifsc', '').strip().upper()
        company.pan = request.form.get('pan', '').strip().upper()
        company.invoice_prefix = request.form.get('invoice_prefix', 'INV').strip().upper()
        company.invoice_terms = request.form.get('invoice_terms', '').strip()

        company.save()
        flash('Company settings saved successfully', 'success')
        return redirect(url_for('settings.company'))

    # State codes for dropdown
    state_codes = [
        ('01', '01 - Jammu & Kashmir'),
        ('02', '02 - Himachal Pradesh'),
        ('03', '03 - Punjab'),
        ('04', '04 - Chandigarh'),
        ('05', '05 - Uttarakhand'),
        ('06', '06 - Haryana'),
        ('07', '07 - Delhi'),
        ('08', '08 - Rajasthan'),
        ('09', '09 - Uttar Pradesh'),
        ('10', '10 - Bihar'),
        ('11', '11 - Sikkim'),
        ('12', '12 - Arunachal Pradesh'),
        ('13', '13 - Nagaland'),
        ('14', '14 - Manipur'),
        ('15', '15 - Mizoram'),
        ('16', '16 - Tripura'),
        ('17', '17 - Meghalaya'),
        ('18', '18 - Assam'),
        ('19', '19 - West Bengal'),
        ('20', '20 - Jharkhand'),
        ('21', '21 - Odisha'),
        ('22', '22 - Chhattisgarh'),
        ('23', '23 - Madhya Pradesh'),
        ('24', '24 - Gujarat'),
        ('26', '26 - Dadra & Nagar Haveli'),
        ('27', '27 - Maharashtra'),
        ('28', '28 - Andhra Pradesh'),
        ('29', '29 - Karnataka'),
        ('30', '30 - Goa'),
        ('31', '31 - Lakshadweep'),
        ('32', '32 - Kerala'),
        ('33', '33 - Tamil Nadu'),
        ('34', '34 - Puducherry'),
        ('35', '35 - Andaman & Nicobar'),
        ('36', '36 - Telangana'),
        ('37', '37 - Andhra Pradesh (New)'),
        ('38', '38 - Ladakh'),
    ]

    return render_template(
        'settings/company.html',
        company=company,
        state_codes=state_codes
    )


@settings_bp.route('/email', methods=['GET', 'POST'])
@login_required
@admin_required
def email():
    """Email settings"""
    company = Company.get()

    if request.method == 'POST':
        if not company:
            company = Company()

        company.smtp_server = request.form.get('smtp_server', '').strip()
        company.smtp_port = int(request.form.get('smtp_port', 587) or 587)
        company.smtp_username = request.form.get('smtp_username', '').strip()
        smtp_password = request.form.get('smtp_password', '').strip()
        if smtp_password:  # Only update if provided
            company.smtp_password = smtp_password
        company.smtp_use_tls = request.form.get('smtp_use_tls') == '1'
        company.email_from = request.form.get('email_from', '').strip()

        company.save()
        flash('Email settings saved successfully', 'success')
        return redirect(url_for('settings.email'))

    return render_template('settings/email.html', company=company)


@settings_bp.route('/email/test', methods=['POST'])
@login_required
@admin_required
def test_email():
    """Test email configuration"""
    company = Company.get()
    if not company or not company.smtp_server:
        flash('Please configure email settings first', 'error')
        return redirect(url_for('settings.email'))

    test_to = request.form.get('test_email', '').strip()
    if not test_to:
        flash('Please enter a test email address', 'error')
        return redirect(url_for('settings.email'))

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg['From'] = company.email_from or company.smtp_username
        msg['To'] = test_to
        msg['Subject'] = 'GST Billing - Test Email'

        body = f"""
        This is a test email from GST Billing.

        If you received this email, your email configuration is working correctly.

        Company: {company.name}
        SMTP Server: {company.smtp_server}
        """
        msg.attach(MIMEText(body, 'plain'))

        if company.smtp_use_tls:
            server = smtplib.SMTP(company.smtp_server, company.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(company.smtp_server, company.smtp_port)

        server.login(company.smtp_username, company.smtp_password)
        server.send_message(msg)
        server.quit()

        flash(f'Test email sent successfully to {test_to}', 'success')
    except Exception as e:
        flash(f'Failed to send test email: {str(e)}', 'error')

    return redirect(url_for('settings.email'))


# Category Management
@settings_bp.route('/categories')
@login_required
@admin_required
def categories():
    """Category management"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('settings/categories.html', categories=categories)


@settings_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    """Add new category"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category name is required', 'error')
        return redirect(url_for('settings.categories'))

    if Category.query.filter_by(name=name).first():
        flash('Category already exists', 'error')
        return redirect(url_for('settings.categories'))

    category = Category(name=name, description=description)
    db.session.add(category)
    db.session.commit()

    flash(f'Category "{name}" created successfully', 'success')
    return redirect(url_for('settings.categories'))


@settings_bp.route('/categories/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_category(id):
    """Edit category"""
    category = Category.query.get_or_404(id)

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category name is required', 'error')
        return redirect(url_for('settings.categories'))

    existing = Category.query.filter_by(name=name).first()
    if existing and existing.id != id:
        flash('Category name already in use', 'error')
        return redirect(url_for('settings.categories'))

    category.name = name
    category.description = description
    db.session.commit()

    flash(f'Category "{name}" updated successfully', 'success')
    return redirect(url_for('settings.categories'))


@settings_bp.route('/categories/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_category(id):
    """Toggle category active status"""
    category = Category.query.get_or_404(id)
    category.is_active = not category.is_active
    db.session.commit()

    status = 'activated' if category.is_active else 'deactivated'
    flash(f'Category "{category.name}" {status}', 'success')
    return redirect(url_for('settings.categories'))

"""Customers blueprint - CRUD operations"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models.customer import Customer
from app.forms.customer_forms import CustomerForm

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')


@customers_bp.route('/')
@login_required
def index():
    """List all customers"""
    show_inactive = request.args.get('show_inactive', '0') == '1'
    search = request.args.get('search', '').strip()

    query = Customer.query

    if not show_inactive:
        query = query.filter_by(is_active=True)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Customer.name.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.gstin.ilike(search_term)
            )
        )

    customers = query.order_by(Customer.name).all()

    return render_template(
        'customers/index.html',
        customers=customers,
        show_inactive=show_inactive,
        search=search
    )


@customers_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add new customer"""
    form = CustomerForm()

    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data,
            phone=form.phone.data or '',
            address=form.address.data or '',
            gstin=form.gstin.data.upper() if form.gstin.data else '',
            state_code=form.state_code.data,
            pin_code=form.pin_code.data or '',
            credit_limit=form.credit_limit.data or 0,
            dl_number=form.dl_number.data or '',
            is_active=form.is_active.data
        )
        customer.save()
        flash(f'Customer "{customer.name}" added successfully!', 'success')
        return redirect(url_for('customers.index'))

    return render_template('customers/form.html', form=form, title='Add Customer')


@customers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit customer"""
    customer = Customer.get_by_id(id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers.index'))

    form = CustomerForm(obj=customer)

    if form.validate_on_submit():
        customer.name = form.name.data
        customer.phone = form.phone.data or ''
        customer.address = form.address.data or ''
        customer.gstin = form.gstin.data.upper() if form.gstin.data else ''
        customer.state_code = form.state_code.data
        customer.pin_code = form.pin_code.data or ''
        customer.credit_limit = form.credit_limit.data or 0
        customer.dl_number = form.dl_number.data or ''
        customer.is_active = form.is_active.data
        customer.save()
        flash(f'Customer "{customer.name}" updated successfully!', 'success')
        return redirect(url_for('customers.index'))

    return render_template('customers/form.html', form=form, customer=customer, title='Edit Customer')


@customers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Soft delete customer (deactivate)"""
    customer = Customer.get_by_id(id)
    if customer:
        customer.is_active = False
        customer.save()
        flash(f'Customer "{customer.name}" has been deactivated', 'success')
    return redirect(url_for('customers.index'))


@customers_bp.route('/<int:id>/view')
@login_required
def view(id):
    """View customer details with invoice history"""
    customer = Customer.get_by_id(id)
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers.index'))

    # Get recent invoices for this customer (will be implemented later)
    invoices = []  # customer.invoices.order_by(Invoice.invoice_date.desc()).limit(10).all()

    return render_template('customers/view.html', customer=customer, invoices=invoices)


# API endpoints for AJAX
@customers_bp.route('/api/search')
@login_required
def api_search():
    """Search customers API for autocomplete"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    customers = Customer.search(query, limit=10)
    return jsonify([c.to_dict() for c in customers])


@customers_bp.route('/api/<int:id>')
@login_required
def api_get(id):
    """Get customer by ID"""
    customer = Customer.get_by_id(id)
    if customer:
        return jsonify(customer.to_dict())
    return jsonify({'error': 'Customer not found'}), 404

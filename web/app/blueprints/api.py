"""REST API Blueprint for mobile app and integrations"""
from datetime import date, datetime
from functools import wraps
from flask import Blueprint, jsonify, request, g
from flask_login import current_user, login_required
from app.extensions import db
from app.models.invoice import Invoice, InvoiceItem
from app.models.product import Product
from app.models.customer import Customer
from app.models.quotation import Quotation
from app.models.company import Company

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


def api_login_required(f):
    """Decorator for API endpoints requiring authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required', 'status': 401}), 401
        return f(*args, **kwargs)
    return decorated_function


def success_response(data, message='Success', status=200):
    """Standard success response format"""
    return jsonify({
        'status': status,
        'message': message,
        'data': data
    }), status


def error_response(message, status=400):
    """Standard error response format"""
    return jsonify({
        'status': status,
        'error': message
    }), status


# ==================== Products API ====================

@api_bp.route('/products', methods=['GET'])
@api_login_required
def get_products():
    """Get all products with optional filtering"""
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Product.query.filter_by(is_active=True)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.barcode.ilike(search_term),
                Product.hsn_code.ilike(search_term)
            )
        )

    if category_id:
        query = query.filter_by(category_id=category_id)

    pagination = query.order_by(Product.name).paginate(page=page, per_page=per_page)

    return success_response({
        'products': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/products/<int:id>', methods=['GET'])
@api_login_required
def get_product(id):
    """Get single product by ID"""
    product = Product.query.get_or_404(id)
    return success_response(product.to_dict())


@api_bp.route('/products/barcode/<barcode>', methods=['GET'])
@api_login_required
def get_product_by_barcode(barcode):
    """Get product by barcode"""
    product = Product.query.filter_by(barcode=barcode, is_active=True).first()
    if not product:
        return error_response('Product not found', 404)
    return success_response(product.to_dict())


@api_bp.route('/products', methods=['POST'])
@api_login_required
def create_product():
    """Create a new product"""
    data = request.get_json()

    if not data.get('name'):
        return error_response('Product name is required')

    product = Product(
        name=data['name'],
        barcode=data.get('barcode', ''),
        hsn_code=data.get('hsn_code', ''),
        price=data.get('price', 0),
        cost_price=data.get('cost_price', 0),
        gst_rate=data.get('gst_rate', 18),
        stock_qty=data.get('stock_qty', 0),
        unit=data.get('unit', 'NOS'),
        low_stock_alert=data.get('low_stock_alert', 10),
        category_id=data.get('category_id')
    )

    db.session.add(product)
    db.session.commit()

    return success_response(product.to_dict(), 'Product created', 201)


@api_bp.route('/products/<int:id>', methods=['PUT'])
@api_login_required
def update_product(id):
    """Update a product"""
    product = Product.query.get_or_404(id)
    data = request.get_json()

    if 'name' in data:
        product.name = data['name']
    if 'barcode' in data:
        product.barcode = data['barcode']
    if 'hsn_code' in data:
        product.hsn_code = data['hsn_code']
    if 'price' in data:
        product.price = data['price']
    if 'cost_price' in data:
        product.cost_price = data['cost_price']
    if 'gst_rate' in data:
        product.gst_rate = data['gst_rate']
    if 'stock_qty' in data:
        product.stock_qty = data['stock_qty']
    if 'unit' in data:
        product.unit = data['unit']
    if 'low_stock_alert' in data:
        product.low_stock_alert = data['low_stock_alert']
    if 'category_id' in data:
        product.category_id = data['category_id']

    db.session.commit()
    return success_response(product.to_dict(), 'Product updated')


# ==================== Customers API ====================

@api_bp.route('/customers', methods=['GET'])
@api_login_required
def get_customers():
    """Get all customers with optional filtering"""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Customer.query.filter_by(is_active=True)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Customer.name.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.gstin.ilike(search_term)
            )
        )

    pagination = query.order_by(Customer.name).paginate(page=page, per_page=per_page)

    return success_response({
        'customers': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/customers/<int:id>', methods=['GET'])
@api_login_required
def get_customer(id):
    """Get single customer by ID"""
    customer = Customer.query.get_or_404(id)
    return success_response(customer.to_dict())


@api_bp.route('/customers', methods=['POST'])
@api_login_required
def create_customer():
    """Create a new customer"""
    data = request.get_json()

    if not data.get('name'):
        return error_response('Customer name is required')

    customer = Customer(
        name=data['name'],
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        address=data.get('address', ''),
        gstin=data.get('gstin', ''),
        state_code=data.get('state_code', ''),
        state_name=data.get('state_name', '')
    )

    db.session.add(customer)
    db.session.commit()

    return success_response(customer.to_dict(), 'Customer created', 201)


# ==================== Invoices API ====================

@api_bp.route('/invoices', methods=['GET'])
@api_login_required
def get_invoices():
    """Get invoices with filtering"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    customer_id = request.args.get('customer_id', type=int)
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Invoice.query.filter_by(is_cancelled=False)

    if start_date:
        query = query.filter(Invoice.invoice_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Invoice.invoice_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if status:
        query = query.filter_by(payment_status=status)

    pagination = query.order_by(Invoice.created_at.desc()).paginate(page=page, per_page=per_page)

    return success_response({
        'invoices': [inv.to_dict() for inv in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/invoices/<int:id>', methods=['GET'])
@api_login_required
def get_invoice(id):
    """Get single invoice with items"""
    invoice = Invoice.query.get_or_404(id)
    data = invoice.to_dict()
    data['items'] = [item.to_dict() for item in invoice.items]
    return success_response(data)


@api_bp.route('/invoices', methods=['POST'])
@api_login_required
def create_invoice():
    """Create a new invoice"""
    data = request.get_json()

    if not data.get('items'):
        return error_response('Invoice items are required')

    # Generate invoice number
    invoice_number = Invoice.get_next_invoice_number()

    invoice = Invoice(
        invoice_number=invoice_number,
        invoice_date=datetime.strptime(data.get('invoice_date', date.today().isoformat()), '%Y-%m-%d').date(),
        customer_id=data.get('customer_id'),
        customer_name=data.get('customer_name', ''),
        payment_mode=data.get('payment_mode', 'CASH'),
        discount=data.get('discount', 0),
        created_by=current_user.id
    )

    # Add items
    subtotal = 0
    cgst_total = 0
    sgst_total = 0
    igst_total = 0

    for item_data in data['items']:
        taxable_value = item_data['qty'] * item_data['rate']
        gst_rate = item_data.get('gst_rate', 18)

        # Calculate tax (assume intra-state for now)
        cgst = taxable_value * (gst_rate / 2) / 100
        sgst = taxable_value * (gst_rate / 2) / 100
        igst = 0

        if data.get('is_igst'):
            cgst = 0
            sgst = 0
            igst = taxable_value * gst_rate / 100

        item = InvoiceItem(
            product_id=item_data.get('product_id'),
            product_name=item_data['product_name'],
            hsn_code=item_data.get('hsn_code', ''),
            qty=item_data['qty'],
            unit=item_data.get('unit', 'NOS'),
            rate=item_data['rate'],
            gst_rate=gst_rate,
            taxable_value=taxable_value,
            cgst=cgst,
            sgst=sgst,
            igst=igst,
            total=taxable_value + cgst + sgst + igst
        )
        invoice.items.append(item)

        subtotal += taxable_value
        cgst_total += cgst
        sgst_total += sgst
        igst_total += igst

        # Update stock
        if item_data.get('product_id'):
            product = Product.query.get(item_data['product_id'])
            if product:
                product.stock_qty -= item_data['qty']

    invoice.subtotal = subtotal
    invoice.cgst_total = cgst_total
    invoice.sgst_total = sgst_total
    invoice.igst_total = igst_total
    invoice.grand_total = subtotal + cgst_total + sgst_total + igst_total - invoice.discount

    # Payment
    amount_paid = data.get('amount_paid', invoice.grand_total)
    invoice.amount_paid = amount_paid
    invoice.balance_due = invoice.grand_total - amount_paid

    if invoice.balance_due <= 0:
        invoice.payment_status = 'PAID'
    elif amount_paid > 0:
        invoice.payment_status = 'PARTIAL'
    else:
        invoice.payment_status = 'UNPAID'

    db.session.add(invoice)
    db.session.commit()

    return success_response(invoice.to_dict(), 'Invoice created', 201)


# ==================== Dashboard API ====================

@api_bp.route('/dashboard/stats', methods=['GET'])
@api_login_required
def get_dashboard_stats():
    """Get dashboard statistics"""
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Today's stats
    today_invoices = Invoice.query.filter(
        Invoice.invoice_date == today,
        Invoice.is_cancelled == False
    ).all()

    # Monthly stats
    monthly_invoices = Invoice.query.filter(
        Invoice.invoice_date >= month_start,
        Invoice.is_cancelled == False
    ).all()

    # Counts
    total_customers = Customer.query.filter_by(is_active=True).count()
    total_products = Product.query.filter_by(is_active=True).count()
    low_stock = Product.query.filter(
        Product.is_active == True,
        Product.stock_qty <= Product.low_stock_alert
    ).count()

    return success_response({
        'today_sales': sum(inv.grand_total for inv in today_invoices),
        'today_invoices': len(today_invoices),
        'monthly_sales': sum(inv.grand_total for inv in monthly_invoices),
        'monthly_invoices': len(monthly_invoices),
        'total_customers': total_customers,
        'total_products': total_products,
        'low_stock_items': low_stock
    })


# ==================== Company API ====================

@api_bp.route('/company', methods=['GET'])
@api_login_required
def get_company():
    """Get company details"""
    company = Company.get()
    if company:
        return success_response(company.to_dict())
    return success_response({})


# ==================== Utility Endpoints ====================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

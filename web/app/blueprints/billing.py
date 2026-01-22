"""Billing blueprint - New bill creation and invoice management"""
from datetime import date
from io import BytesIO
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models.product import Product
from app.models.customer import Customer
from app.models.company import Company
from app.models.invoice import Invoice, InvoiceItem
from app.services.gst_calculator import GSTCalculator
from app.services.pdf_generator import pdf_generator

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

# Payment modes
PAYMENT_MODES = [
    ('CASH', 'Cash'),
    ('CARD', 'Card'),
    ('UPI', 'UPI'),
    ('BANK', 'Bank Transfer'),
    ('CREDIT', 'Credit'),
]


@billing_bp.route('/new')
@login_required
def new_bill():
    """New bill page"""
    company = Company.get()
    customers = Customer.get_all()
    next_invoice_number = Invoice.get_next_invoice_number()

    return render_template(
        'billing/new_bill.html',
        company=company,
        customers=customers,
        next_invoice_number=next_invoice_number,
        payment_modes=PAYMENT_MODES,
        today=date.today().isoformat()
    )


@billing_bp.route('/create', methods=['POST'])
@login_required
def create_invoice():
    """Create new invoice from cart data"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        items = data.get('items', [])
        if not items:
            return jsonify({'error': 'No items in cart'}), 400

        # Get company for seller state code
        company = Company.get()
        seller_state_code = company.state_code if company else '32'

        # Get customer state code
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name', 'Walk-in Customer')
        buyer_state_code = data.get('buyer_state_code', seller_state_code)

        if customer_id:
            customer = Customer.get_by_id(customer_id)
            if customer:
                customer_name = customer.name
                buyer_state_code = customer.state_code

        # Calculate totals using GST calculator
        calculator = GSTCalculator(seller_state_code)
        discount = float(data.get('discount', 0))
        cart_total = calculator.calculate_cart(items, buyer_state_code, discount)

        # Create invoice
        invoice = Invoice(
            invoice_number=Invoice.get_next_invoice_number(),
            invoice_date=date.today(),
            customer_id=customer_id,
            customer_name=customer_name,
            subtotal=cart_total['subtotal'],
            cgst_total=cart_total['cgst_total'],
            sgst_total=cart_total['sgst_total'],
            igst_total=cart_total['igst_total'],
            discount=discount,
            grand_total=cart_total['grand_total'],
            payment_mode=data.get('payment_mode', 'CASH'),
            amount_paid=cart_total['grand_total'],
            balance_due=0,
            payment_status='PAID',
            created_by=current_user.id
        )

        db.session.add(invoice)
        db.session.flush()  # Get invoice ID

        # Create invoice items and update stock
        for item_data in cart_total['items']:
            item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                hsn_code=item_data['hsn_code'],
                qty=item_data['qty'],
                unit=item_data['unit'],
                rate=item_data['rate'],
                gst_rate=item_data['gst_rate'],
                taxable_value=item_data['taxable_value'],
                cgst=item_data['cgst'],
                sgst=item_data['sgst'],
                igst=item_data['igst'],
                total=item_data['total']
            )
            db.session.add(item)

            # Update stock
            if item_data['product_id']:
                product = Product.get_by_id(item_data['product_id'])
                if product:
                    product.update_stock(
                        -item_data['qty'],
                        f'Invoice #{invoice.invoice_number}',
                        invoice.id
                    )

        db.session.commit()

        return jsonify({
            'success': True,
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'message': f'Invoice {invoice.invoice_number} created successfully!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/invoices')
@login_required
def invoice_list():
    """List all invoices"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search', '').strip()

    query = Invoice.query

    if start_date and end_date:
        query = query.filter(Invoice.invoice_date.between(start_date, end_date))

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Invoice.invoice_number.ilike(search_term),
                Invoice.customer_name.ilike(search_term)
            )
        )

    invoices = query.order_by(Invoice.invoice_date.desc(), Invoice.id.desc()).limit(100).all()

    return render_template(
        'billing/invoice_list.html',
        invoices=invoices,
        start_date=start_date or '',
        end_date=end_date or '',
        search=search
    )


@billing_bp.route('/invoices/<int:id>')
@login_required
def view_invoice(id):
    """View invoice details"""
    invoice = Invoice.get_by_id(id)
    if not invoice:
        flash('Invoice not found', 'error')
        return redirect(url_for('billing.invoice_list'))

    company = Company.get()
    items = list(invoice.items)

    # Get tax summary by rate
    item_dicts = [item.to_dict() for item in items]
    tax_summary = GSTCalculator.get_tax_summary_by_rate(item_dicts)

    return render_template(
        'billing/view_invoice.html',
        invoice=invoice,
        items=items,
        company=company,
        tax_summary=tax_summary
    )


@billing_bp.route('/invoices/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_invoice(id):
    """Cancel an invoice"""
    invoice = Invoice.get_by_id(id)
    if not invoice:
        flash('Invoice not found', 'error')
        return redirect(url_for('billing.invoice_list'))

    if invoice.is_cancelled:
        flash('Invoice is already cancelled', 'warning')
        return redirect(url_for('billing.view_invoice', id=id))

    # Restore stock
    for item in invoice.items:
        if item.product_id:
            product = Product.get_by_id(item.product_id)
            if product:
                product.update_stock(
                    item.qty,
                    f'Invoice #{invoice.invoice_number} cancelled',
                    invoice.id
                )

    invoice.cancel()
    flash(f'Invoice {invoice.invoice_number} has been cancelled', 'success')
    return redirect(url_for('billing.view_invoice', id=id))


# API endpoints for billing page
@billing_bp.route('/api/calculate', methods=['POST'])
@login_required
def api_calculate():
    """Calculate cart totals"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        buyer_state_code = data.get('buyer_state_code')
        discount = float(data.get('discount', 0))

        company = Company.get()
        seller_state_code = company.state_code if company else '32'

        calculator = GSTCalculator(seller_state_code)
        result = calculator.calculate_cart(items, buyer_state_code, discount)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/api/products/search')
@login_required
def api_search_products():
    """Search products for billing autocomplete"""
    query = request.args.get('q', '').strip()
    if len(query) < 1:
        return jsonify([])

    products = Product.search(query, limit=10)
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'barcode': p.barcode,
        'hsn_code': p.hsn_code,
        'unit': p.unit,
        'price': p.price,
        'gst_rate': p.gst_rate,
        'stock_qty': p.stock_qty
    } for p in products])


@billing_bp.route('/api/products/barcode/<barcode>')
@login_required
def api_get_by_barcode(barcode):
    """Get product by barcode"""
    product = Product.get_by_barcode(barcode)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'barcode': product.barcode,
            'hsn_code': product.hsn_code,
            'unit': product.unit,
            'price': product.price,
            'gst_rate': product.gst_rate,
            'stock_qty': product.stock_qty
        })
    return jsonify({'error': 'Product not found'}), 404


@billing_bp.route('/api/customers/search')
@login_required
def api_search_customers():
    """Search customers for billing"""
    query = request.args.get('q', '').strip()
    if len(query) < 1:
        return jsonify([])

    customers = Customer.search(query, limit=10)
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'phone': c.phone,
        'gstin': c.gstin,
        'state_code': c.state_code,
        'address': c.address
    } for c in customers])


@billing_bp.route('/invoices/<int:id>/pdf')
@login_required
def download_invoice_pdf(id):
    """Download invoice as PDF"""
    invoice = Invoice.get_by_id(id)
    if not invoice:
        flash('Invoice not found', 'error')
        return redirect(url_for('billing.invoice_list'))

    company = Company.get()
    items = list(invoice.items)

    try:
        pdf_bytes = pdf_generator.generate_invoice_pdf(invoice, company, items)
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{invoice.invoice_number.replace("/", "-")}.pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('billing.view_invoice', id=id))

"""Quotations blueprint - Create, manage, and convert quotations (Admin only)"""
from datetime import date, timedelta
from io import BytesIO
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.decorators import admin_required
from app.models.product import Product
from app.models.customer import Customer
from app.models.company import Company
from app.models.quotation import Quotation, QuotationItem
from app.models.invoice import Invoice, InvoiceItem
from app.services.gst_calculator import GSTCalculator
from app.services.pdf_generator import pdf_generator

quotations_bp = Blueprint('quotations', __name__, url_prefix='/quotations')


@quotations_bp.route('/')
@login_required
@admin_required
def index():
    """List all quotations"""
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()

    query = Quotation.query

    if status:
        query = query.filter_by(status=status)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Quotation.quotation_number.ilike(search_term),
                Quotation.customer_name.ilike(search_term)
            )
        )

    quotations = query.order_by(Quotation.quotation_date.desc(), Quotation.id.desc()).limit(100).all()

    # Check for expired quotations
    for q in quotations:
        if q.is_expired() and q.status not in ('EXPIRED', 'CONVERTED', 'REJECTED'):
            q.update_status('EXPIRED')

    return render_template(
        'quotations/index.html',
        quotations=quotations,
        status=status,
        search=search,
        statuses=Quotation.STATUSES
    )


@quotations_bp.route('/new')
@login_required
@admin_required
def new_quotation():
    """New quotation page"""
    company = Company.get()
    customers = Customer.get_all()
    next_number = Quotation.get_next_quotation_number()
    default_validity = date.today() + timedelta(days=30)

    return render_template(
        'quotations/new_quotation.html',
        company=company,
        customers=customers,
        next_number=next_number,
        today=date.today().isoformat(),
        default_validity=default_validity.isoformat()
    )


@quotations_bp.route('/create', methods=['POST'])
@login_required
@admin_required
def create_quotation():
    """Create new quotation"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        items = data.get('items', [])
        if not items:
            return jsonify({'error': 'No items in quotation'}), 400

        # Get company for seller state code
        company = Company.get()
        seller_state_code = company.state_code if company else '32'

        # Get customer info
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name', '')
        buyer_state_code = data.get('buyer_state_code', seller_state_code)

        if customer_id:
            customer = Customer.get_by_id(customer_id)
            if customer:
                customer_name = customer.name
                buyer_state_code = customer.state_code

        # Calculate totals
        calculator = GSTCalculator(seller_state_code)
        discount = float(data.get('discount', 0))
        cart_total = calculator.calculate_cart(items, buyer_state_code, discount)

        # Parse validity date
        validity_str = data.get('validity_date')
        validity_date = date.fromisoformat(validity_str) if validity_str else date.today() + timedelta(days=30)

        # Create quotation
        quotation = Quotation(
            quotation_number=Quotation.get_next_quotation_number(),
            quotation_date=date.today(),
            validity_date=validity_date,
            customer_id=customer_id,
            customer_name=customer_name,
            subtotal=cart_total['subtotal'],
            cgst_total=cart_total['cgst_total'],
            sgst_total=cart_total['sgst_total'],
            igst_total=cart_total['igst_total'],
            discount=discount,
            grand_total=cart_total['grand_total'],
            status='DRAFT',
            notes=data.get('notes', ''),
            terms_conditions=data.get('terms_conditions', ''),
            created_by=current_user.id
        )

        db.session.add(quotation)
        db.session.flush()

        # Create quotation items
        for item_data in cart_total['items']:
            item = QuotationItem(
                quotation_id=quotation.id,
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

        db.session.commit()

        return jsonify({
            'success': True,
            'quotation_id': quotation.id,
            'quotation_number': quotation.quotation_number,
            'message': f'Quotation {quotation.quotation_number} created successfully!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@quotations_bp.route('/<int:id>')
@login_required
@admin_required
def view_quotation(id):
    """View quotation details"""
    quotation = Quotation.get_by_id(id)
    if not quotation:
        flash('Quotation not found', 'error')
        return redirect(url_for('quotations.index'))

    company = Company.get()
    items = list(quotation.items)

    # Get tax summary
    item_dicts = [item.to_dict() for item in items]
    tax_summary = GSTCalculator.get_tax_summary_by_rate(item_dicts)

    return render_template(
        'quotations/view_quotation.html',
        quotation=quotation,
        items=items,
        company=company,
        tax_summary=tax_summary
    )


@quotations_bp.route('/<int:id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_status(id):
    """Update quotation status"""
    quotation = Quotation.get_by_id(id)
    if not quotation:
        flash('Quotation not found', 'error')
        return redirect(url_for('quotations.index'))

    new_status = request.form.get('status')
    if new_status in Quotation.STATUSES:
        quotation.update_status(new_status)
        flash(f'Quotation status updated to {new_status}', 'success')

    return redirect(url_for('quotations.view_quotation', id=id))


@quotations_bp.route('/<int:id>/convert', methods=['POST'])
@login_required
@admin_required
def convert_to_invoice(id):
    """Convert quotation to invoice"""
    quotation = Quotation.get_by_id(id)
    if not quotation:
        flash('Quotation not found', 'error')
        return redirect(url_for('quotations.index'))

    if not quotation.can_convert():
        flash('This quotation cannot be converted to invoice', 'error')
        return redirect(url_for('quotations.view_quotation', id=id))

    try:
        # Create invoice from quotation
        invoice = Invoice(
            invoice_number=Invoice.get_next_invoice_number(),
            invoice_date=date.today(),
            customer_id=quotation.customer_id,
            customer_name=quotation.customer_name,
            subtotal=quotation.subtotal,
            cgst_total=quotation.cgst_total,
            sgst_total=quotation.sgst_total,
            igst_total=quotation.igst_total,
            discount=quotation.discount,
            grand_total=quotation.grand_total,
            payment_mode='CASH',
            amount_paid=quotation.grand_total,
            balance_due=0,
            payment_status='PAID',
            created_by=current_user.id
        )

        db.session.add(invoice)
        db.session.flush()

        # Copy items and update stock
        for q_item in quotation.items:
            item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=q_item.product_id,
                product_name=q_item.product_name,
                hsn_code=q_item.hsn_code,
                qty=q_item.qty,
                unit=q_item.unit,
                rate=q_item.rate,
                gst_rate=q_item.gst_rate,
                taxable_value=q_item.taxable_value,
                cgst=q_item.cgst,
                sgst=q_item.sgst,
                igst=q_item.igst,
                total=q_item.total
            )
            db.session.add(item)

            # Update stock
            if q_item.product_id:
                product = Product.get_by_id(q_item.product_id)
                if product:
                    product.update_stock(
                        -q_item.qty,
                        f'Invoice #{invoice.invoice_number} (from Quote)',
                        invoice.id
                    )

        # Update quotation
        quotation.status = 'CONVERTED'
        quotation.converted_invoice_id = invoice.id

        db.session.commit()

        flash(f'Quotation converted to Invoice {invoice.invoice_number}', 'success')
        return redirect(url_for('billing.view_invoice', id=invoice.id))

    except Exception as e:
        db.session.rollback()
        flash(f'Error converting quotation: {str(e)}', 'error')
        return redirect(url_for('quotations.view_quotation', id=id))


@quotations_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_quotation(id):
    """Delete quotation (only if DRAFT)"""
    quotation = Quotation.get_by_id(id)
    if not quotation:
        flash('Quotation not found', 'error')
        return redirect(url_for('quotations.index'))

    if quotation.status != 'DRAFT':
        flash('Only draft quotations can be deleted', 'error')
        return redirect(url_for('quotations.view_quotation', id=id))

    db.session.delete(quotation)
    db.session.commit()

    flash('Quotation deleted', 'success')
    return redirect(url_for('quotations.index'))


# API endpoints
@quotations_bp.route('/api/calculate', methods=['POST'])
@login_required
@admin_required
def api_calculate():
    """Calculate quotation totals"""
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


@quotations_bp.route('/<int:id>/pdf')
@login_required
@admin_required
def download_pdf(id):
    """Download quotation as PDF"""
    quotation = Quotation.get_by_id(id)
    if not quotation:
        flash('Quotation not found', 'error')
        return redirect(url_for('quotations.index'))

    company = Company.get()
    items = list(quotation.items)

    try:
        pdf_bytes = pdf_generator.generate_quotation_pdf(quotation, company, items)
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{quotation.quotation_number.replace("/", "-")}.pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('quotations.view_quotation', id=id))

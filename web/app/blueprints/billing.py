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

# Transport modes for e-Way bill
TRANSPORT_MODES = [
    ('Road', 'Road'),
    ('Rail', 'Rail'),
    ('Air', 'Air'),
    ('Ship', 'Ship'),
]

# E-Way bill threshold (Rs. 50,000)
EWAY_BILL_THRESHOLD = 50000


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
        transport_modes=TRANSPORT_MODES,
        eway_threshold=EWAY_BILL_THRESHOLD,
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

        # Get customer details
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name', 'Walk-in Customer')
        buyer_state_code = data.get('buyer_state_code', seller_state_code)
        customer_gstin = ''
        supply_type = 'B2C'  # Default to B2C

        if customer_id:
            customer = Customer.get_by_id(customer_id)
            if customer:
                customer_name = customer.name
                buyer_state_code = customer.state_code
                # B2B/B2C classification based on GSTIN
                if customer.gstin:
                    customer_gstin = customer.gstin
                    supply_type = 'B2B'

        # Calculate totals using GST calculator
        calculator = GSTCalculator(seller_state_code)
        discount = float(data.get('discount', 0))
        cart_total = calculator.calculate_cart(items, buyer_state_code, discount)

        # Determine payment status based on payment mode
        payment_mode = data.get('payment_mode', 'CASH')
        if payment_mode == 'CREDIT':
            # Credit sales: mark as UNPAID with full balance due
            payment_status = 'UNPAID'
            amount_paid = 0
            balance_due = cart_total['grand_total']
        else:
            # Cash/Card/UPI/Bank: mark as PAID
            payment_status = 'PAID'
            amount_paid = cart_total['grand_total']
            balance_due = 0

        # Get GST options
        is_reverse_charge = data.get('is_reverse_charge', False)

        # Determine invoice type based on GST rates
        # If all items have 0% GST, it's a Bill of Supply
        all_zero_gst = all(item.get('gst_rate', 0) == 0 for item in items)
        invoice_type = 'BILL_OF_SUPPLY' if all_zero_gst else 'TAX_INVOICE'

        # Get e-Way bill transport details
        transport_mode = data.get('transport_mode', 'Road')
        vehicle_number = data.get('vehicle_number', '').strip().upper()
        transport_distance = int(data.get('transport_distance', 0) or 0)
        transporter_id = data.get('transporter_id', '').strip().upper()

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
            payment_mode=payment_mode,
            amount_paid=amount_paid,
            balance_due=balance_due,
            payment_status=payment_status,
            # B2B/B2C classification
            supply_type=supply_type,
            customer_gstin=customer_gstin,
            # GST compliance fields
            invoice_type=invoice_type,
            is_reverse_charge=is_reverse_charge,
            buyer_state_code=buyer_state_code,
            # E-Way bill transport details
            transport_mode=transport_mode,
            vehicle_number=vehicle_number,
            transport_distance=transport_distance,
            transporter_id=transporter_id,
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

        # Queue email notification if configured
        _queue_invoice_email(invoice, company)

        # Check if e-Way bill is required
        eway_required = cart_total['grand_total'] >= EWAY_BILL_THRESHOLD

        return jsonify({
            'success': True,
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'message': f'Invoice {invoice.invoice_number} created successfully!',
            'eway_required': eway_required,
            'payment_status': payment_status
        })

    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def _queue_invoice_email(invoice, company):
    """Queue email notification for invoice (non-blocking)"""
    try:
        if not company or not getattr(company, 'admin_notification_email', None):
            return  # Email not configured

        if not company.smtp_server:
            return  # SMTP not configured

        from app.models.email_queue import EmailQueue
        from app.services.email_service import EmailService

        email_service = EmailService(company)
        email_content = email_service.generate_invoice_email_content(invoice, company)

        # Queue the email
        EmailQueue.queue_invoice_email(
            invoice_id=invoice.id,
            recipient=company.admin_notification_email,
            subject=email_content['subject'],
            body_html=email_content['body_html'],
            body_text=email_content['body_text']
        )

        # Try to send immediately (non-blocking)
        _process_email_queue()

    except Exception as e:
        # Log error but don't fail invoice creation
        print(f"Email queue error: {e}")


def _process_email_queue():
    """Process pending emails in queue"""
    try:
        from app.models.email_queue import EmailQueue
        from app.services.email_service import EmailService

        company = Company.get()
        if not company:
            return

        email_service = EmailService(company)
        if not email_service.is_configured():
            return

        pending = EmailQueue.get_pending(limit=5)
        for entry in pending:
            try:
                pdf_bytes = None
                pdf_name = "document.pdf"

                # Generate PDF if it's an invoice email
                if entry.attachment_type == 'invoice_pdf' and entry.attachment_reference_id:
                    invoice = Invoice.get_by_id(entry.attachment_reference_id)
                    if invoice:
                        items = list(invoice.items)
                        pdf_bytes = pdf_generator.generate_invoice_pdf(invoice, company, items)
                        pdf_name = f"{invoice.invoice_number.replace('/', '-')}.pdf"

                success, error = email_service.send_email(
                    recipient=entry.recipient,
                    subject=entry.subject,
                    body_html=entry.body_html,
                    body_text=entry.body_text,
                    pdf_bytes=pdf_bytes,
                    pdf_name=pdf_name
                )

                if success:
                    entry.mark_sent()
                else:
                    entry.mark_failed(error)

            except Exception as e:
                entry.mark_failed(str(e))

    except Exception as e:
        print(f"Email processing error: {e}")


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


# E-Way Bill endpoints
@billing_bp.route('/invoices/<int:id>/eway-bill/json')
@login_required
def export_eway_bill_json(id):
    """Export e-Way Bill data as JSON for GST portal upload"""
    invoice = Invoice.get_by_id(id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    company = Company.get()
    customer = Customer.get_by_id(invoice.customer_id) if invoice.customer_id else None
    items = list(invoice.items)

    # Determine if inter-state
    seller_state = company.state_code if company else '32'
    buyer_state = customer.state_code if customer else seller_state
    is_inter_state = buyer_state != seller_state

    # Build JSON structure matching GST portal format
    eway_data = {
        "supplyType": "O",  # Outward
        "subSupplyType": "1",  # Supply
        "docType": "INV",
        "docNo": invoice.invoice_number,
        "docDate": invoice.invoice_date.strftime("%d/%m/%Y") if invoice.invoice_date else "",
        "fromGstin": company.gstin if company else "",
        "fromTrdName": company.name if company else "",
        "fromAddr1": company.address if company else "",
        "fromPlace": company.city if company else "",
        "fromPincode": getattr(company, 'pin_code', '') or "",
        "fromStateCode": int(seller_state) if seller_state else 32,
        "toGstin": customer.gstin if customer and customer.gstin else "URP",
        "toTrdName": invoice.customer_name or "Cash Customer",
        "toAddr1": customer.address if customer else "",
        "toPlace": customer.city if customer else "",
        "toPincode": customer.pin_code if customer else "",
        "toStateCode": int(buyer_state) if buyer_state else int(seller_state),
        "transMode": {"Road": "1", "Rail": "2", "Air": "3", "Ship": "4"}.get(
            invoice.transport_mode or "Road", "1"
        ),
        "transDistance": str(invoice.transport_distance or 0),
        "transporterId": invoice.transporter_id or "",
        "transporterName": "",
        "vehicleNo": invoice.vehicle_number or "",
        "vehicleType": "R",  # Regular
        "totInvValue": float(invoice.grand_total or 0),
        "cgstValue": float(invoice.cgst_total or 0),
        "sgstValue": float(invoice.sgst_total or 0),
        "igstValue": float(invoice.igst_total or 0),
        "cessValue": 0,
        "cessNonAdvolValue": 0,
        "otherValue": 0,
        "totalValue": float(invoice.subtotal or 0),
        "itemList": []
    }

    # Add items
    for item in items:
        eway_data["itemList"].append({
            "productName": item.product_name,
            "productDesc": item.product_name,
            "hsnCode": int(item.hsn_code) if item.hsn_code and item.hsn_code.isdigit() else 0,
            "quantity": float(item.qty or 0),
            "qtyUnit": item.unit or "NOS",
            "cgstRate": float(item.gst_rate / 2) if item.cgst and item.cgst > 0 else 0,
            "sgstRate": float(item.gst_rate / 2) if item.sgst and item.sgst > 0 else 0,
            "igstRate": float(item.gst_rate) if item.igst and item.igst > 0 else 0,
            "cessRate": 0,
            "cessNonadvol": 0,
            "taxableAmount": float(item.taxable_value or 0)
        })

    # Return as downloadable JSON file
    response = jsonify(eway_data)
    response.headers['Content-Disposition'] = f'attachment; filename=eway_bill_{invoice.invoice_number.replace("/", "-")}.json'
    return response


@billing_bp.route('/invoices/<int:id>/eway-bill/save', methods=['POST'])
@login_required
def save_eway_bill_number(id):
    """Save e-Way Bill number after manual portal entry"""
    invoice = Invoice.get_by_id(id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    data = request.get_json()
    eway_number = data.get('eway_bill_number', '').strip()

    if not eway_number:
        return jsonify({'error': 'E-Way Bill number is required'}), 400

    # Validate format (12 digits)
    if not eway_number.isdigit() or len(eway_number) != 12:
        return jsonify({'error': 'E-Way Bill number must be 12 digits'}), 400

    invoice.eway_bill_number = eway_number
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'E-Way Bill number {eway_number} saved successfully'
    })


@billing_bp.route('/invoices/<int:id>/eway-bill/check')
@login_required
def check_eway_bill_required(id):
    """Check if e-Way bill is required for an invoice"""
    invoice = Invoice.get_by_id(id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    required = (invoice.grand_total or 0) >= EWAY_BILL_THRESHOLD

    # Calculate validity if distance is provided
    validity_days = 1
    if invoice.transport_distance and invoice.transport_distance > 0:
        # 1 day per 100 km (or part thereof)
        validity_days = max(1, (invoice.transport_distance + 99) // 100)

    return jsonify({
        'required': required,
        'threshold': EWAY_BILL_THRESHOLD,
        'invoice_value': float(invoice.grand_total or 0),
        'eway_bill_number': invoice.eway_bill_number or None,
        'transport_distance': invoice.transport_distance or 0,
        'validity_days': validity_days
    })

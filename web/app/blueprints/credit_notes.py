"""Credit Notes blueprint - Create and manage credit notes (Admin only)"""
from datetime import date
from io import BytesIO
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.decorators import admin_required
from app.models.product import Product
from app.models.customer import Customer
from app.models.company import Company
from app.models.invoice import Invoice
from app.models.credit_note import CreditNote, CreditNoteItem
from app.services.gst_calculator import GSTCalculator
from app.services.pdf_generator import pdf_generator

credit_notes_bp = Blueprint('credit_notes', __name__, url_prefix='/credit-notes')


def _perform_cancellation(credit_note):
    """
    Perform cancellation logic for a credit note.
    Returns (success, error_message) tuple.
    """
    # Validate stock before cancellation for returns
    if credit_note.reason == 'RETURN':
        for item in credit_note.items:
            if item.product_id:
                product = Product.get_by_id(item.product_id)
                if product and product.stock_qty < item.qty:
                    return False, f"Cannot cancel: {product.name} has insufficient stock ({product.stock_qty} available, need {item.qty})"

    # Reverse stock if it was a return
    if credit_note.reason == 'RETURN':
        for item in credit_note.items:
            if item.product_id:
                product = Product.get_by_id(item.product_id)
                if product:
                    product.update_stock(
                        -item.qty,
                        f'Credit Note #{credit_note.credit_note_number} cancelled',
                        credit_note.id
                    )

    # Reverse invoice balance update
    if credit_note.original_invoice_id:
        invoice = Invoice.get_by_id(credit_note.original_invoice_id)
        if invoice:
            # Add back the credit note amount to balance
            invoice.balance_due = min(invoice.grand_total, invoice.balance_due + credit_note.grand_total)
            invoice.amount_paid = invoice.grand_total - invoice.balance_due

            # Update payment status
            if invoice.balance_due >= invoice.grand_total:
                invoice.payment_status = 'UNPAID'
            elif invoice.balance_due > 0:
                invoice.payment_status = 'PARTIAL'
            else:
                invoice.payment_status = 'PAID'

    credit_note.cancel()
    return True, None


@credit_notes_bp.route('/')
@login_required
@admin_required
def index():
    """List all credit notes"""
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()

    query = CreditNote.query

    if status:
        query = query.filter_by(status=status)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                CreditNote.credit_note_number.ilike(search_term),
                CreditNote.customer_name.ilike(search_term),
                CreditNote.original_invoice_number.ilike(search_term)
            )
        )

    credit_notes = query.order_by(CreditNote.credit_note_date.desc(), CreditNote.id.desc()).limit(100).all()

    return render_template(
        'credit_notes/index.html',
        credit_notes=credit_notes,
        status=status,
        search=search,
        statuses=CreditNote.STATUSES
    )


@credit_notes_bp.route('/new')
@login_required
@admin_required
def new_credit_note():
    """New credit note page - requires invoice selection"""
    invoice_id = request.args.get('invoice_id', type=int)
    invoice = None
    invoice_items = []
    returnable_items = []

    if invoice_id:
        invoice = Invoice.get_by_id(invoice_id)
        if invoice:
            if invoice.is_cancelled:
                flash('Cannot create credit note for cancelled invoice', 'error')
                return redirect(url_for('billing.view_invoice', id=invoice_id))

            # Get all existing credit notes for this invoice
            existing_credit_notes = CreditNote.query.filter(
                CreditNote.original_invoice_id == invoice_id,
                CreditNote.status != 'CANCELLED'
            ).all()

            # Calculate already credited quantities per product
            credited_qty = {}
            for cn in existing_credit_notes:
                for item in cn.items:
                    if item.product_id:
                        if item.product_id not in credited_qty:
                            credited_qty[item.product_id] = 0
                        credited_qty[item.product_id] += item.qty

            # Build returnable items list with remaining quantities
            for item in invoice.items:
                already_credited = credited_qty.get(item.product_id, 0)
                remaining_qty = item.qty - already_credited

                if remaining_qty > 0:
                    returnable_items.append({
                        'product_id': item.product_id,
                        'product_name': item.product_name,
                        'hsn_code': item.hsn_code,
                        'original_qty': item.qty,
                        'already_credited': already_credited,
                        'remaining_qty': remaining_qty,
                        'unit': item.unit,
                        'rate': item.rate,
                        'gst_rate': item.gst_rate,
                        'taxable_value': item.taxable_value,
                        'total': item.total
                    })

            invoice_items = list(invoice.items)

    company = Company.get()
    next_number = CreditNote.get_next_credit_note_number()

    return render_template(
        'credit_notes/new_credit_note.html',
        company=company,
        invoice=invoice,
        invoice_items=invoice_items,
        returnable_items=returnable_items,
        next_number=next_number,
        today=date.today().isoformat(),
        reasons=CreditNote.REASONS
    )


@credit_notes_bp.route('/create', methods=['POST'])
@login_required
@admin_required
def create_credit_note():
    """Create new credit note - with proper validation against original invoice"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        items = data.get('items', [])
        if not items:
            return jsonify({'error': 'No items in credit note'}), 400

        # VALIDATION 1: Invoice is mandatory
        invoice_id = data.get('invoice_id')
        if not invoice_id:
            return jsonify({'error': 'Credit note must be against an invoice'}), 400

        invoice = Invoice.get_by_id(invoice_id)
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        if invoice.is_cancelled:
            return jsonify({'error': 'Cannot create credit note for cancelled invoice'}), 400

        # Get company for seller state code
        company = Company.get()
        seller_state_code = company.state_code if company else '32'

        invoice_number = invoice.invoice_number
        customer_id = invoice.customer_id
        customer_name = invoice.customer_name
        buyer_state_code = seller_state_code
        if invoice.customer:
            buyer_state_code = invoice.customer.state_code or seller_state_code

        # VALIDATION 2: Build map of original invoice quantities
        original_qty_map = {}
        for inv_item in invoice.items:
            original_qty_map[inv_item.product_id] = {
                'qty': inv_item.qty,
                'product_name': inv_item.product_name
            }

        # VALIDATION 3: Get already credited quantities
        existing_credit_notes = CreditNote.query.filter(
            CreditNote.original_invoice_id == invoice_id,
            CreditNote.status != 'CANCELLED'
        ).all()

        credited_qty = {}
        for cn in existing_credit_notes:
            for item in cn.items:
                if item.product_id:
                    if item.product_id not in credited_qty:
                        credited_qty[item.product_id] = 0
                    credited_qty[item.product_id] += item.qty

        # VALIDATION 4: Validate each item in credit note
        validation_errors = []
        for item in items:
            product_id = item.get('product_id')
            requested_qty = float(item.get('qty', 0))

            if not product_id:
                continue

            # Check if product was in original invoice
            if product_id not in original_qty_map:
                validation_errors.append(f"Product '{item.get('product_name', 'Unknown')}' was not in the original invoice")
                continue

            original_qty = original_qty_map[product_id]['qty']
            already_credited = credited_qty.get(product_id, 0)
            remaining_qty = original_qty - already_credited

            if requested_qty > remaining_qty:
                product_name = original_qty_map[product_id]['product_name']
                if remaining_qty <= 0:
                    validation_errors.append(f"'{product_name}' has already been fully credited")
                else:
                    validation_errors.append(f"'{product_name}': requested {requested_qty}, but only {remaining_qty} remaining (original: {original_qty}, already credited: {already_credited})")

        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400

        # Calculate totals
        calculator = GSTCalculator(seller_state_code)
        cart_total = calculator.calculate_cart(items, buyer_state_code, 0)

        # Create credit note
        credit_note = CreditNote(
            credit_note_number=CreditNote.get_next_credit_note_number(),
            credit_note_date=date.today(),
            original_invoice_id=invoice_id,
            original_invoice_number=invoice_number,
            customer_id=customer_id,
            customer_name=customer_name,
            reason=data.get('reason', 'RETURN'),
            reason_details=data.get('reason_details', ''),
            subtotal=cart_total['subtotal'],
            cgst_total=cart_total['cgst_total'],
            sgst_total=cart_total['sgst_total'],
            igst_total=cart_total['igst_total'],
            grand_total=cart_total['grand_total'],
            status='ACTIVE',
            created_by=current_user.id
        )

        db.session.add(credit_note)
        db.session.flush()

        # Create credit note items and restore stock
        for item_data in cart_total['items']:
            item = CreditNoteItem(
                credit_note_id=credit_note.id,
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

            # Restore stock for returns (use stored reason, not incoming data)
            if item_data['product_id'] and credit_note.reason == 'RETURN':
                product = Product.get_by_id(item_data['product_id'])
                if product:
                    product.update_stock(
                        item_data['qty'],
                        f'Credit Note #{credit_note.credit_note_number}',
                        credit_note.id
                    )

        # UPDATE INVOICE BALANCE
        # Reduce the balance due by credit note amount (or set to 0 if credit exceeds balance)
        credit_amount = cart_total['grand_total']
        if invoice.balance_due > 0:
            new_balance = max(0, invoice.balance_due - credit_amount)
            invoice.balance_due = new_balance
            invoice.amount_paid = invoice.grand_total - new_balance

            # Update payment status
            if new_balance == 0:
                invoice.payment_status = 'PAID'
            elif invoice.amount_paid > 0:
                invoice.payment_status = 'PARTIAL'

        db.session.commit()

        return jsonify({
            'success': True,
            'credit_note_id': credit_note.id,
            'credit_note_number': credit_note.credit_note_number,
            'message': f'Credit Note {credit_note.credit_note_number} created successfully!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@credit_notes_bp.route('/<int:id>')
@login_required
@admin_required
def view_credit_note(id):
    """View credit note details"""
    credit_note = CreditNote.get_by_id(id)
    if not credit_note:
        flash('Credit note not found', 'error')
        return redirect(url_for('credit_notes.index'))

    company = Company.get()
    items = list(credit_note.items)

    # Get tax summary
    item_dicts = [item.to_dict() for item in items]
    tax_summary = GSTCalculator.get_tax_summary_by_rate(item_dicts)

    return render_template(
        'credit_notes/view_credit_note.html',
        credit_note=credit_note,
        items=items,
        company=company,
        tax_summary=tax_summary
    )


@credit_notes_bp.route('/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def update_status(id):
    """Update credit note status"""
    credit_note = CreditNote.get_by_id(id)
    if not credit_note:
        flash('Credit note not found', 'error')
        return redirect(url_for('credit_notes.index'))

    new_status = request.form.get('status')
    if new_status not in CreditNote.STATUSES:
        flash('Invalid status', 'error')
        return redirect(url_for('credit_notes.view_credit_note', id=id))

    if new_status == 'CANCELLED':
        if credit_note.status != 'CANCELLED':
            success, error_msg = _perform_cancellation(credit_note)
            if not success:
                flash(error_msg, 'error')
                return redirect(url_for('credit_notes.view_credit_note', id=id))
            flash(f'Credit Note {credit_note.credit_note_number} has been cancelled', 'success')
        else:
            flash('Credit note is already cancelled', 'warning')
    elif new_status == 'APPLIED':
        credit_note.apply()
        flash(f'Credit Note {credit_note.credit_note_number} marked as applied', 'success')
    else:
        credit_note.status = new_status
        db.session.commit()
        flash(f'Credit Note status updated to {new_status}', 'success')

    return redirect(url_for('credit_notes.view_credit_note', id=id))


@credit_notes_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_credit_note(id):
    """Cancel credit note"""
    credit_note = CreditNote.get_by_id(id)
    if not credit_note:
        flash('Credit note not found', 'error')
        return redirect(url_for('credit_notes.index'))

    if credit_note.status == 'CANCELLED':
        flash('Credit note is already cancelled', 'warning')
        return redirect(url_for('credit_notes.view_credit_note', id=id))

    success, error_msg = _perform_cancellation(credit_note)
    if not success:
        flash(error_msg, 'error')
        return redirect(url_for('credit_notes.view_credit_note', id=id))

    flash(f'Credit Note {credit_note.credit_note_number} has been cancelled', 'success')
    return redirect(url_for('credit_notes.view_credit_note', id=id))


@credit_notes_bp.route('/from-invoice/<int:invoice_id>')
@login_required
@admin_required
def from_invoice(invoice_id):
    """Create credit note from invoice"""
    return redirect(url_for('credit_notes.new_credit_note', invoice_id=invoice_id))


# API endpoints
@credit_notes_bp.route('/api/invoice/<int:invoice_id>')
@login_required
@admin_required
def api_get_invoice(invoice_id):
    """Get invoice details for credit note creation"""
    invoice = Invoice.get_by_id(invoice_id)
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    return jsonify({
        'id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'customer_id': invoice.customer_id,
        'customer_name': invoice.customer_name,
        'items': [item.to_dict() for item in invoice.items]
    })


@credit_notes_bp.route('/<int:id>/pdf')
@login_required
@admin_required
def download_pdf(id):
    """Download credit note as PDF"""
    credit_note = CreditNote.get_by_id(id)
    if not credit_note:
        flash('Credit note not found', 'error')
        return redirect(url_for('credit_notes.index'))

    company = Company.get()
    items = list(credit_note.items)

    try:
        pdf_bytes = pdf_generator.generate_credit_note_pdf(credit_note, company, items)
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{credit_note.credit_note_number.replace("/", "-")}.pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('credit_notes.view_credit_note', id=id))

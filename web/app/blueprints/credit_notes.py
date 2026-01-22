"""Credit Notes blueprint - Create and manage credit notes"""
from datetime import date
from io import BytesIO
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models.product import Product
from app.models.customer import Customer
from app.models.company import Company
from app.models.invoice import Invoice
from app.models.credit_note import CreditNote, CreditNoteItem
from app.services.gst_calculator import GSTCalculator
from app.services.pdf_generator import pdf_generator

credit_notes_bp = Blueprint('credit_notes', __name__, url_prefix='/credit-notes')


@credit_notes_bp.route('/')
@login_required
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
def new_credit_note():
    """New credit note page"""
    invoice_id = request.args.get('invoice_id', type=int)
    invoice = None
    invoice_items = []

    if invoice_id:
        invoice = Invoice.get_by_id(invoice_id)
        if invoice:
            invoice_items = list(invoice.items)

    company = Company.get()
    next_number = CreditNote.get_next_credit_note_number()

    return render_template(
        'credit_notes/new_credit_note.html',
        company=company,
        invoice=invoice,
        invoice_items=invoice_items,
        next_number=next_number,
        today=date.today().isoformat(),
        reasons=CreditNote.REASONS
    )


@credit_notes_bp.route('/create', methods=['POST'])
@login_required
def create_credit_note():
    """Create new credit note"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        items = data.get('items', [])
        if not items:
            return jsonify({'error': 'No items in credit note'}), 400

        # Get company for seller state code
        company = Company.get()
        seller_state_code = company.state_code if company else '32'

        # Get invoice reference
        invoice_id = data.get('invoice_id')
        invoice_number = data.get('invoice_number', '')
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name', '')
        buyer_state_code = seller_state_code

        if invoice_id:
            invoice = Invoice.get_by_id(invoice_id)
            if invoice:
                invoice_number = invoice.invoice_number
                customer_id = invoice.customer_id
                customer_name = invoice.customer_name
                if invoice.customer:
                    buyer_state_code = invoice.customer.state_code

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

            # Restore stock for returns
            if item_data['product_id'] and data.get('reason') == 'RETURN':
                product = Product.get_by_id(item_data['product_id'])
                if product:
                    product.update_stock(
                        item_data['qty'],
                        f'Credit Note #{credit_note.credit_note_number}',
                        credit_note.id
                    )

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
        # Reverse stock if it was a return
        if credit_note.reason == 'RETURN' and credit_note.status != 'CANCELLED':
            for item in credit_note.items:
                if item.product_id:
                    product = Product.get_by_id(item.product_id)
                    if product:
                        product.update_stock(
                            -item.qty,
                            f'Credit Note #{credit_note.credit_note_number} cancelled',
                            credit_note.id
                        )
        credit_note.cancel()
        flash(f'Credit Note {credit_note.credit_note_number} has been cancelled', 'success')
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
def cancel_credit_note(id):
    """Cancel credit note"""
    credit_note = CreditNote.get_by_id(id)
    if not credit_note:
        flash('Credit note not found', 'error')
        return redirect(url_for('credit_notes.index'))

    if credit_note.status == 'CANCELLED':
        flash('Credit note is already cancelled', 'warning')
        return redirect(url_for('credit_notes.view_credit_note', id=id))

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

    credit_note.cancel()
    flash(f'Credit Note {credit_note.credit_note_number} has been cancelled', 'success')
    return redirect(url_for('credit_notes.view_credit_note', id=id))


@credit_notes_bp.route('/from-invoice/<int:invoice_id>')
@login_required
def from_invoice(invoice_id):
    """Create credit note from invoice"""
    return redirect(url_for('credit_notes.new_credit_note', invoice_id=invoice_id))


# API endpoints
@credit_notes_bp.route('/api/invoice/<int:invoice_id>')
@login_required
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

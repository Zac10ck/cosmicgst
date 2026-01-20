"""Credit Note service for handling returns and refunds"""
from datetime import date
from typing import List, Optional, Dict
from database.models import Invoice, InvoiceItem, CreditNote, CreditNoteItem, Product, Customer
from services.gst_calculator import GSTCalculator


class CreditNoteService:
    """Service for creating and managing credit notes"""

    REASONS = ["RETURN", "DAMAGE", "PRICE_ADJUSTMENT", "OTHER"]

    def __init__(self, seller_state_code: str = "32"):
        self.seller_state_code = seller_state_code
        self.gst_calculator = GSTCalculator(seller_state_code)

    def create_credit_note(
        self,
        original_invoice: Invoice,
        items_to_return: List[Dict],  # [{'product_id': x, 'qty': y}]
        reason: str,
        reason_details: str = "",
        restore_stock: bool = True,
        credit_note_date: date = None
    ) -> CreditNote:
        """
        Create a credit note for returned items.
        items_to_return: List of dicts with 'product_id' and 'qty' keys.
        """
        if credit_note_date is None:
            credit_note_date = date.today()

        if reason not in self.REASONS:
            reason = "OTHER"

        # Determine buyer state for GST calculation
        buyer_state_code = "32"  # Default to Kerala
        if original_invoice.customer_id:
            customer = Customer.get_by_id(original_invoice.customer_id)
            if customer:
                buyer_state_code = customer.state_code

        # Build credit note items from original invoice items
        credit_items = []
        subtotal = 0
        cgst_total = 0
        sgst_total = 0
        igst_total = 0

        # Map original invoice items by product_id
        original_items_map = {item.product_id: item for item in original_invoice.items}

        for return_item in items_to_return:
            product_id = return_item.get('product_id')
            return_qty = return_item.get('qty', 0)

            if return_qty <= 0 or product_id not in original_items_map:
                continue

            orig_item = original_items_map[product_id]

            # Validate return qty doesn't exceed original
            if return_qty > orig_item.qty:
                return_qty = orig_item.qty

            # Calculate values using same rate as original invoice
            taxable_value = return_qty * orig_item.rate

            # Calculate GST based on state
            is_inter_state = self.seller_state_code != buyer_state_code
            gst_rate = orig_item.gst_rate

            if is_inter_state:
                igst = taxable_value * gst_rate / 100
                cgst = 0
                sgst = 0
            else:
                cgst = taxable_value * gst_rate / 200
                sgst = taxable_value * gst_rate / 200
                igst = 0

            total = taxable_value + cgst + sgst + igst

            credit_item = CreditNoteItem(
                product_id=product_id,
                product_name=orig_item.product_name,
                hsn_code=orig_item.hsn_code,
                qty=return_qty,
                unit=orig_item.unit,
                rate=orig_item.rate,
                gst_rate=gst_rate,
                taxable_value=taxable_value,
                cgst=cgst,
                sgst=sgst,
                igst=igst,
                total=total
            )
            credit_items.append(credit_item)

            subtotal += taxable_value
            cgst_total += cgst
            sgst_total += sgst
            igst_total += igst

            # Restore stock if requested
            if restore_stock and product_id:
                product = Product.get_by_id(product_id)
                if product:
                    product.update_stock(return_qty, "RETURN", None)

        grand_total = subtotal + cgst_total + sgst_total + igst_total

        # Create credit note
        credit_note = CreditNote(
            credit_note_number=CreditNote.get_next_credit_note_number(),
            credit_note_date=credit_note_date,
            original_invoice_id=original_invoice.id,
            original_invoice_number=original_invoice.invoice_number,
            customer_id=original_invoice.customer_id,
            customer_name=original_invoice.customer_name,
            reason=reason,
            reason_details=reason_details,
            subtotal=subtotal,
            cgst_total=cgst_total,
            sgst_total=sgst_total,
            igst_total=igst_total,
            grand_total=grand_total,
            status="ACTIVE",
            items=credit_items
        )
        credit_note.save()

        return credit_note

    def get_credit_notes_by_date_range(
        self,
        start_date: date,
        end_date: date,
        include_cancelled: bool = False
    ) -> List[CreditNote]:
        """Get credit notes in date range"""
        return CreditNote.get_by_date_range(start_date, end_date, include_cancelled)

    def get_credit_notes_by_customer(self, customer_id: int) -> List[CreditNote]:
        """Get credit notes for a customer"""
        from database.db import get_connection
        conn = get_connection()
        rows = conn.execute("""
            SELECT * FROM credit_notes
            WHERE customer_id = ? AND status != 'CANCELLED'
            ORDER BY credit_note_date DESC
        """, (customer_id,)).fetchall()
        conn.close()
        return [CreditNote.get_by_id(row['id']) for row in rows]

    def get_credit_note_summary(self, start_date: date, end_date: date) -> Dict:
        """Get summary of credit notes for a date range"""
        credit_notes = self.get_credit_notes_by_date_range(start_date, end_date)

        summary = {
            'total_count': len(credit_notes),
            'total_value': 0,
            'subtotal': 0,
            'cgst_total': 0,
            'sgst_total': 0,
            'igst_total': 0,
            'by_reason': {},
            'by_status': {}
        }

        for cn in credit_notes:
            summary['total_value'] += cn.grand_total
            summary['subtotal'] += cn.subtotal
            summary['cgst_total'] += cn.cgst_total
            summary['sgst_total'] += cn.sgst_total
            summary['igst_total'] += cn.igst_total

            # By reason
            if cn.reason not in summary['by_reason']:
                summary['by_reason'][cn.reason] = {'count': 0, 'value': 0}
            summary['by_reason'][cn.reason]['count'] += 1
            summary['by_reason'][cn.reason]['value'] += cn.grand_total

            # By status
            if cn.status not in summary['by_status']:
                summary['by_status'][cn.status] = {'count': 0, 'value': 0}
            summary['by_status'][cn.status]['count'] += 1
            summary['by_status'][cn.status]['value'] += cn.grand_total

        return summary

    def cancel_credit_note(self, credit_note_id: int, reverse_stock: bool = True) -> bool:
        """
        Cancel a credit note.
        Optionally reverses stock changes (deducts stock that was restored).
        """
        credit_note = CreditNote.get_by_id(credit_note_id)
        if not credit_note or credit_note.status == "CANCELLED":
            return False

        # Reverse stock if requested
        if reverse_stock:
            for item in credit_note.items:
                if item.product_id:
                    product = Product.get_by_id(item.product_id)
                    if product:
                        product.update_stock(-item.qty, "CN_CANCELLED", credit_note.id)

        credit_note.cancel()
        return True

    def get_returnable_items(self, invoice: Invoice) -> List[Dict]:
        """
        Get items that can still be returned from an invoice.
        Accounts for existing credit notes.
        """
        # Get all credit notes for this invoice
        existing_credit_notes = CreditNote.get_by_invoice(invoice.id)

        # Calculate already returned quantities
        returned_qty = {}
        for cn in existing_credit_notes:
            if cn.status != "CANCELLED":
                for item in cn.items:
                    if item.product_id not in returned_qty:
                        returned_qty[item.product_id] = 0
                    returned_qty[item.product_id] += item.qty

        # Build returnable items list
        returnable = []
        for item in invoice.items:
            already_returned = returned_qty.get(item.product_id, 0)
            remaining = item.qty - already_returned
            if remaining > 0:
                returnable.append({
                    'product_id': item.product_id,
                    'product_name': item.product_name,
                    'hsn_code': item.hsn_code,
                    'original_qty': item.qty,
                    'returned_qty': already_returned,
                    'returnable_qty': remaining,
                    'rate': item.rate,
                    'gst_rate': item.gst_rate,
                    'unit': item.unit
                })

        return returnable

    def apply_credit_to_invoice(
        self,
        credit_note_id: int,
        target_invoice_id: int
    ) -> bool:
        """Apply credit note value to reduce balance on another invoice"""
        credit_note = CreditNote.get_by_id(credit_note_id)
        target_invoice = Invoice.get_by_id(target_invoice_id)

        if not credit_note or not target_invoice:
            return False

        if credit_note.status != "ACTIVE":
            return False

        # Record as payment on target invoice
        from services.payment_service import PaymentService
        payment_service = PaymentService()

        payment_service.record_payment(
            invoice_id=target_invoice_id,
            payment_mode="CREDIT_NOTE",
            amount=min(credit_note.grand_total, target_invoice.balance_due),
            reference_number=credit_note.credit_note_number,
            notes=f"Applied from Credit Note {credit_note.credit_note_number}"
        )

        # Mark credit note as applied
        credit_note.status = "APPLIED"
        credit_note.save()

        return True

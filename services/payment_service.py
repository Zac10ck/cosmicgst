"""Payment service for handling split payments and payment tracking"""
from datetime import date
from typing import List, Optional, Dict
from database.models import Invoice, InvoicePayment, Customer
from database.db import get_connection


class PaymentService:
    """Service for managing invoice payments"""

    PAYMENT_STATUS = {
        'UNPAID': 'UNPAID',
        'PARTIAL': 'PARTIAL',
        'PAID': 'PAID'
    }

    def record_payment(
        self,
        invoice_id: int,
        payment_mode: str,
        amount: float,
        reference_number: str = "",
        notes: str = "",
        payment_date: date = None
    ) -> InvoicePayment:
        """
        Record a single payment against an invoice.
        Updates invoice amount_paid, balance_due, and payment_status.
        """
        if payment_date is None:
            payment_date = date.today()

        # Create payment record
        payment = InvoicePayment(
            invoice_id=invoice_id,
            payment_mode=payment_mode,
            amount=amount,
            payment_date=payment_date,
            reference_number=reference_number,
            notes=notes
        )
        payment.save()

        # Update invoice totals
        self._update_invoice_payment_totals(invoice_id)

        # Handle credit payment - update customer credit balance
        if payment_mode == "CREDIT":
            invoice = Invoice.get_by_id(invoice_id)
            if invoice and invoice.customer_id:
                customer = Customer.get_by_id(invoice.customer_id)
                if customer:
                    customer.update_credit(-amount)  # Reduce credit balance

        return payment

    def record_split_payment(
        self,
        invoice_id: int,
        payments: List[Dict],  # [{'mode': 'CASH', 'amount': 500, 'reference': ''}]
        payment_date: date = None
    ) -> List[InvoicePayment]:
        """
        Record multiple payments at once (split payment).
        payments: List of dicts with 'mode', 'amount', and optional 'reference' keys.
        """
        if payment_date is None:
            payment_date = date.today()

        recorded_payments = []
        for p in payments:
            if p.get('amount', 0) > 0:
                payment = InvoicePayment(
                    invoice_id=invoice_id,
                    payment_mode=p.get('mode', 'CASH'),
                    amount=p.get('amount', 0),
                    payment_date=payment_date,
                    reference_number=p.get('reference', ''),
                    notes=p.get('notes', '')
                )
                payment.save()
                recorded_payments.append(payment)

                # Handle credit payment
                if p.get('mode') == "CREDIT":
                    invoice = Invoice.get_by_id(invoice_id)
                    if invoice and invoice.customer_id:
                        customer = Customer.get_by_id(invoice.customer_id)
                        if customer:
                            customer.update_credit(-p.get('amount', 0))

        # Update invoice totals
        self._update_invoice_payment_totals(invoice_id)

        return recorded_payments

    def _update_invoice_payment_totals(self, invoice_id: int):
        """Update invoice amount_paid, balance_due, and payment_status"""
        invoice = Invoice.get_by_id(invoice_id)
        if not invoice:
            return

        # Calculate total payments
        payments = InvoicePayment.get_by_invoice(invoice_id)
        total_paid = sum(p.amount for p in payments)

        # Update invoice
        invoice.amount_paid = total_paid
        invoice.balance_due = invoice.grand_total - total_paid

        # Determine payment status
        if invoice.balance_due <= 0:
            invoice.payment_status = self.PAYMENT_STATUS['PAID']
        elif total_paid > 0:
            invoice.payment_status = self.PAYMENT_STATUS['PARTIAL']
        else:
            invoice.payment_status = self.PAYMENT_STATUS['UNPAID']

        invoice.save()

    def get_payment_history(self, invoice_id: int) -> List[InvoicePayment]:
        """Get payment history for an invoice"""
        return InvoicePayment.get_by_invoice(invoice_id)

    def get_outstanding_invoices(self, customer_id: int = None) -> List[Invoice]:
        """Get invoices with balance_due > 0"""
        conn = get_connection()
        if customer_id:
            rows = conn.execute("""
                SELECT * FROM invoices
                WHERE balance_due > 0 AND is_cancelled = 0 AND customer_id = ?
                ORDER BY invoice_date DESC
            """, (customer_id,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM invoices
                WHERE balance_due > 0 AND is_cancelled = 0
                ORDER BY invoice_date DESC
            """).fetchall()
        conn.close()
        return [Invoice.get_by_id(row['id']) for row in rows]

    def get_payment_summary(self, start_date: date, end_date: date) -> Dict:
        """Get payment summary by mode for a date range"""
        payments = InvoicePayment.get_by_date_range(start_date, end_date)

        summary = {
            'total': 0,
            'by_mode': {},
            'count': len(payments)
        }

        for payment in payments:
            summary['total'] += payment.amount
            if payment.payment_mode not in summary['by_mode']:
                summary['by_mode'][payment.payment_mode] = {
                    'amount': 0,
                    'count': 0
                }
            summary['by_mode'][payment.payment_mode]['amount'] += payment.amount
            summary['by_mode'][payment.payment_mode]['count'] += 1

        return summary

    def calculate_payment_status(self, invoice: Invoice) -> str:
        """Calculate payment status based on amounts"""
        if invoice.balance_due <= 0:
            return self.PAYMENT_STATUS['PAID']
        elif invoice.amount_paid > 0:
            return self.PAYMENT_STATUS['PARTIAL']
        else:
            return self.PAYMENT_STATUS['UNPAID']

    def delete_payment(self, payment_id: int) -> bool:
        """Delete a payment record and update invoice totals"""
        conn = get_connection()
        row = conn.execute("SELECT * FROM invoice_payments WHERE id = ?", (payment_id,)).fetchone()
        if not row:
            conn.close()
            return False

        invoice_id = row['invoice_id']
        payment_mode = row['payment_mode']
        amount = row['amount']

        # Delete the payment
        conn.execute("DELETE FROM invoice_payments WHERE id = ?", (payment_id,))
        conn.commit()
        conn.close()

        # Update invoice totals
        self._update_invoice_payment_totals(invoice_id)

        # Restore credit if it was a credit payment
        if payment_mode == "CREDIT":
            invoice = Invoice.get_by_id(invoice_id)
            if invoice and invoice.customer_id:
                customer = Customer.get_by_id(invoice.customer_id)
                if customer:
                    customer.update_credit(amount)  # Restore credit balance

        return True

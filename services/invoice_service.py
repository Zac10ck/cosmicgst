"""Invoice generation and management service"""
from datetime import date, timedelta
from typing import List, Optional, Dict
from database.models import Invoice, InvoiceItem, Product, Customer
from .gst_calculator import GSTCalculator, CartItem


class InvoiceService:
    """Service for creating and managing invoices"""

    def __init__(self, seller_state_code: str = "32"):
        self.gst_calculator = GSTCalculator(seller_state_code)

    def create_invoice(
        self,
        cart_items: List[dict],
        customer: Optional[Customer] = None,
        discount: float = 0,
        payment_mode: str = "CASH",
        invoice_date: date = None
    ) -> Invoice:
        """
        Create a new invoice from cart items

        Args:
            cart_items: List of dicts with product_id, qty
            customer: Optional Customer object
            discount: Discount amount
            payment_mode: Payment mode
            invoice_date: Date of invoice (default: today)

        Returns:
            Created Invoice object
        """
        if invoice_date is None:
            invoice_date = date.today()

        # Build CartItem list for calculation
        items_for_calc = []
        for cart_item in cart_items:
            product = Product.get_by_id(cart_item['product_id'])
            if product:
                items_for_calc.append(CartItem(
                    product_id=product.id,
                    product_name=product.name,
                    hsn_code=product.hsn_code or "",
                    qty=cart_item['qty'],
                    unit=product.unit,
                    rate=product.price,
                    gst_rate=product.gst_rate
                ))

        # Get buyer state code for IGST calculation
        buyer_state_code = customer.state_code if customer else None

        # Calculate totals
        calc_result = self.gst_calculator.calculate_cart_total(
            items=items_for_calc,
            buyer_state_code=buyer_state_code,
            discount=discount
        )

        # Create invoice
        invoice = Invoice(
            invoice_number=Invoice.get_next_invoice_number(),
            invoice_date=invoice_date,
            customer_id=customer.id if customer else None,
            customer_name=customer.name if customer else "Cash Customer",
            subtotal=calc_result['subtotal'],
            cgst_total=calc_result['cgst_total'],
            sgst_total=calc_result['sgst_total'],
            igst_total=calc_result['igst_total'],
            discount=discount,
            grand_total=calc_result['grand_total'],
            payment_mode=payment_mode
        )

        # Create invoice items
        for item_detail in calc_result['items']:
            invoice.items.append(InvoiceItem(
                product_id=item_detail['product_id'],
                product_name=item_detail['product_name'],
                hsn_code=item_detail['hsn_code'],
                qty=item_detail['qty'],
                unit=item_detail['unit'],
                rate=item_detail['rate'],
                gst_rate=item_detail['gst_rate'],
                taxable_value=item_detail['taxable_value'],
                cgst=item_detail['cgst'],
                sgst=item_detail['sgst'],
                igst=item_detail['igst'],
                total=item_detail['total']
            ))

        # Save invoice
        invoice.save()

        # Deduct stock
        for item_detail in calc_result['items']:
            product = Product.get_by_id(item_detail['product_id'])
            if product:
                product.update_stock(
                    qty_change=-item_detail['qty'],
                    reason="SALE",
                    reference_id=invoice.id
                )

        # Queue email if auto-send is enabled
        try:
            from services.email_service import is_email_auto_send_enabled
            if is_email_auto_send_enabled():
                from services.email_queue_service import EmailQueueService
                queue_service = EmailQueueService()
                queue_service.queue_invoice_email(invoice)
        except Exception:
            # Don't fail invoice creation if email queue fails
            pass

        return invoice

    def cancel_invoice(self, invoice_id: int) -> bool:
        """
        Cancel an invoice and restore stock

        Returns True if successful
        """
        invoice = Invoice.get_by_id(invoice_id)
        if not invoice:
            return False

        if invoice.is_cancelled:
            return False  # Already cancelled

        # Mark as cancelled
        invoice.is_cancelled = True
        invoice.save()

        # Restore stock
        for item in invoice.items:
            if item.product_id:
                product = Product.get_by_id(item.product_id)
                if product:
                    product.update_stock(
                        qty_change=item.qty,  # Add back
                        reason="CANCELLED",
                        reference_id=invoice.id
                    )

        return True

    def get_daily_sales(self, sales_date: date = None) -> dict:
        """Get sales summary for a date"""
        if sales_date is None:
            sales_date = date.today()

        invoices = Invoice.get_by_date_range(sales_date, sales_date)

        total_sales = 0
        total_tax = 0
        invoice_count = 0
        payment_breakdown = {}

        for inv in invoices:
            if not inv.is_cancelled:
                total_sales += inv.grand_total
                total_tax += (inv.cgst_total + inv.sgst_total + inv.igst_total)
                invoice_count += 1

                mode = inv.payment_mode
                if mode not in payment_breakdown:
                    payment_breakdown[mode] = 0
                payment_breakdown[mode] += inv.grand_total

        return {
            'date': sales_date,
            'total_sales': round(total_sales, 2),
            'total_tax': round(total_tax, 2),
            'invoice_count': invoice_count,
            'payment_breakdown': payment_breakdown
        }

    def get_sales_by_date_range(self, start_date: date, end_date: date) -> dict:
        """Get sales summary for date range"""
        invoices = Invoice.get_by_date_range(start_date, end_date)

        total_sales = 0
        total_tax = 0
        invoice_count = 0

        for inv in invoices:
            if not inv.is_cancelled:
                total_sales += inv.grand_total
                total_tax += (inv.cgst_total + inv.sgst_total + inv.igst_total)
                invoice_count += 1

        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_sales': round(total_sales, 2),
            'total_tax': round(total_tax, 2),
            'invoice_count': invoice_count
        }

    def get_gst_summary(self, start_date: date, end_date: date) -> dict:
        """Get GST summary for date range"""
        invoices = Invoice.get_by_date_range(start_date, end_date)

        total_taxable = 0
        total_cgst = 0
        total_sgst = 0
        total_igst = 0

        # Group by GST rate
        rate_wise = {}

        for inv in invoices:
            if inv.is_cancelled:
                continue

            total_taxable += inv.subtotal
            total_cgst += inv.cgst_total
            total_sgst += inv.sgst_total
            total_igst += inv.igst_total

            for item in inv.items:
                rate = item.gst_rate
                if rate not in rate_wise:
                    rate_wise[rate] = {
                        'taxable': 0,
                        'cgst': 0,
                        'sgst': 0,
                        'igst': 0
                    }
                rate_wise[rate]['taxable'] += item.taxable_value
                rate_wise[rate]['cgst'] += item.cgst
                rate_wise[rate]['sgst'] += item.sgst
                rate_wise[rate]['igst'] += item.igst

        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_taxable': round(total_taxable, 2),
            'total_cgst': round(total_cgst, 2),
            'total_sgst': round(total_sgst, 2),
            'total_igst': round(total_igst, 2),
            'total_tax': round(total_cgst + total_sgst + total_igst, 2),
            'rate_wise': rate_wise
        }

    def get_sales_trend(self, days: int = 7) -> List[Dict]:
        """
        Get daily sales for the last N days for chart visualization

        Args:
            days: Number of days to fetch (default 7)

        Returns:
            List of dicts with date, total sales, and invoice count
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Get all invoices for the period
        invoices = Invoice.get_by_date_range(start_date, end_date)

        # Group by date
        daily_data = {}
        for i in range(days):
            d = start_date + timedelta(days=i)
            daily_data[d] = {'date': d, 'total': 0.0, 'count': 0}

        for inv in invoices:
            if not inv.is_cancelled and inv.invoice_date in daily_data:
                daily_data[inv.invoice_date]['total'] += inv.grand_total
                daily_data[inv.invoice_date]['count'] += 1

        # Convert to sorted list
        result = sorted(daily_data.values(), key=lambda x: x['date'])
        return result

    def get_payment_mode_distribution(self, start_date: date, end_date: date) -> Dict[str, float]:
        """
        Get payment mode breakdown for date range

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dict with payment mode as key and total amount as value
        """
        invoices = Invoice.get_by_date_range(start_date, end_date)

        distribution = {}
        for inv in invoices:
            if not inv.is_cancelled:
                mode = inv.payment_mode or "CASH"
                if mode not in distribution:
                    distribution[mode] = 0.0
                distribution[mode] += inv.grand_total

        # Round values
        for mode in distribution:
            distribution[mode] = round(distribution[mode], 2)

        return distribution

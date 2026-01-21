"""Quotation/Estimate service"""
from datetime import date, timedelta
from typing import List, Optional, Dict
from database.models import Quotation, QuotationItem, Product, Customer, Invoice, InvoiceItem
from services.gst_calculator import GSTCalculator, CartItem
from services.invoice_service import InvoiceService


class QuotationService:
    """Service for creating and managing quotations/estimates"""

    STATUSES = ["DRAFT", "SENT", "ACCEPTED", "REJECTED", "EXPIRED", "CONVERTED"]
    DEFAULT_VALIDITY_DAYS = 30

    def __init__(self, seller_state_code: str = "32"):
        self.gst_calculator = GSTCalculator(seller_state_code)
        self.seller_state_code = seller_state_code

    def create_quotation(
        self,
        cart_items: List[dict],
        customer: Optional[Customer] = None,
        discount: float = 0,
        validity_days: int = 30,
        notes: str = "",
        terms: str = "",
        quotation_date: date = None,
        status: str = "DRAFT"
    ) -> Quotation:
        """
        Create a new quotation from cart items.
        Does NOT deduct stock.

        Args:
            cart_items: List of dicts with product_id, qty, and optional rate override
            customer: Optional Customer object
            discount: Discount amount
            validity_days: Number of days quotation is valid
            notes: Additional notes
            terms: Terms and conditions
            quotation_date: Date of quotation (default: today)
            status: Initial status (DRAFT or SENT)

        Returns:
            Created Quotation object
        """
        if quotation_date is None:
            quotation_date = date.today()

        validity_date = quotation_date + timedelta(days=validity_days)

        # Build CartItem list for calculation
        items_for_calc = []
        for cart_item in cart_items:
            product = Product.get_by_id(cart_item['product_id'])
            if product:
                # Allow rate override for quotations
                rate = cart_item.get('rate', product.price)
                items_for_calc.append(CartItem(
                    product_id=product.id,
                    product_name=product.name,
                    hsn_code=product.hsn_code or "",
                    qty=cart_item['qty'],
                    unit=product.unit,
                    rate=rate,
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

        # Create quotation
        quotation = Quotation(
            quotation_number=Quotation.get_next_quotation_number(),
            quotation_date=quotation_date,
            validity_date=validity_date,
            customer_id=customer.id if customer else None,
            customer_name=customer.name if customer else "",
            subtotal=calc_result['subtotal'],
            cgst_total=calc_result['cgst_total'],
            sgst_total=calc_result['sgst_total'],
            igst_total=calc_result['igst_total'],
            discount=discount,
            grand_total=calc_result['grand_total'],
            status=status,
            notes=notes,
            terms_conditions=terms
        )

        # Create quotation items
        for item_detail in calc_result['items']:
            quotation.items.append(QuotationItem(
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

        # Save quotation (no stock deduction)
        quotation.save()

        return quotation

    def update_quotation(
        self,
        quotation_id: int,
        cart_items: List[dict] = None,
        customer: Customer = None,
        discount: float = None,
        validity_date: date = None,
        notes: str = None,
        terms: str = None
    ) -> Optional[Quotation]:
        """
        Update an existing quotation (only DRAFT status)

        Returns updated Quotation or None if not found/not editable
        """
        quotation = Quotation.get_by_id(quotation_id)
        if not quotation:
            return None

        # Only allow editing DRAFT quotations
        if quotation.status not in ('DRAFT', 'SENT'):
            return None

        # Update customer if provided
        if customer is not None:
            quotation.customer_id = customer.id
            quotation.customer_name = customer.name

        # Update validity if provided
        if validity_date is not None:
            quotation.validity_date = validity_date

        # Update notes if provided
        if notes is not None:
            quotation.notes = notes

        # Update terms if provided
        if terms is not None:
            quotation.terms_conditions = terms

        # Recalculate if cart items provided
        if cart_items is not None:
            # Determine discount
            new_discount = discount if discount is not None else quotation.discount

            # Recalculate
            items_for_calc = []
            for cart_item in cart_items:
                product = Product.get_by_id(cart_item['product_id'])
                if product:
                    rate = cart_item.get('rate', product.price)
                    items_for_calc.append(CartItem(
                        product_id=product.id,
                        product_name=product.name,
                        hsn_code=product.hsn_code or "",
                        qty=cart_item['qty'],
                        unit=product.unit,
                        rate=rate,
                        gst_rate=product.gst_rate
                    ))

            buyer_state_code = None
            if quotation.customer_id:
                cust = Customer.get_by_id(quotation.customer_id)
                if cust:
                    buyer_state_code = cust.state_code

            calc_result = self.gst_calculator.calculate_cart_total(
                items=items_for_calc,
                buyer_state_code=buyer_state_code,
                discount=new_discount
            )

            # Update totals
            quotation.subtotal = calc_result['subtotal']
            quotation.cgst_total = calc_result['cgst_total']
            quotation.sgst_total = calc_result['sgst_total']
            quotation.igst_total = calc_result['igst_total']
            quotation.discount = new_discount
            quotation.grand_total = calc_result['grand_total']

            # Update items
            quotation.items = []
            for item_detail in calc_result['items']:
                quotation.items.append(QuotationItem(
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
        elif discount is not None:
            # Just update discount
            quotation.discount = discount
            quotation.grand_total = quotation.subtotal + quotation.cgst_total + quotation.sgst_total + quotation.igst_total - discount

        quotation.save()
        return quotation

    def update_status(self, quotation_id: int, new_status: str) -> bool:
        """Update quotation status"""
        if new_status not in self.STATUSES:
            return False

        quotation = Quotation.get_by_id(quotation_id)
        if not quotation:
            return False

        quotation.update_status(new_status)
        return True

    def convert_to_invoice(
        self,
        quotation_id: int,
        payment_mode: str = "CASH",
        invoice_date: date = None,
        deduct_stock: bool = True
    ) -> Optional[Invoice]:
        """
        Convert a quotation to an invoice.
        - Creates invoice from quotation items
        - Deducts stock (if enabled)
        - Marks quotation as CONVERTED
        - Links quotation to invoice

        Returns the created Invoice or None if failed
        """
        quotation = Quotation.get_by_id(quotation_id)
        if not quotation:
            return None

        # Only convert DRAFT, SENT, or ACCEPTED quotations
        if quotation.status not in ('DRAFT', 'SENT', 'ACCEPTED'):
            return None

        if invoice_date is None:
            invoice_date = date.today()

        # Get customer
        customer = None
        if quotation.customer_id:
            customer = Customer.get_by_id(quotation.customer_id)

        # Convert quotation items to cart items
        cart_items = []
        for item in quotation.items:
            cart_items.append({
                'product_id': item.product_id,
                'qty': item.qty
            })

        # Create invoice using InvoiceService
        invoice_service = InvoiceService(self.seller_state_code)
        invoice = invoice_service.create_invoice(
            cart_items=cart_items,
            customer=customer,
            discount=quotation.discount,
            payment_mode=payment_mode,
            invoice_date=invoice_date
        )

        # Mark quotation as converted and link to invoice
        quotation.status = "CONVERTED"
        quotation.converted_invoice_id = invoice.id
        quotation.save()

        return invoice

    def duplicate_quotation(self, quotation_id: int) -> Optional[Quotation]:
        """Create a duplicate quotation with new number"""
        original = Quotation.get_by_id(quotation_id)
        if not original:
            return None

        # Get customer
        customer = None
        if original.customer_id:
            customer = Customer.get_by_id(original.customer_id)

        # Convert items to cart format
        cart_items = []
        for item in original.items:
            cart_items.append({
                'product_id': item.product_id,
                'qty': item.qty,
                'rate': item.rate  # Preserve original rate
            })

        # Create new quotation
        return self.create_quotation(
            cart_items=cart_items,
            customer=customer,
            discount=original.discount,
            validity_days=self.DEFAULT_VALIDITY_DAYS,
            notes=original.notes,
            terms=original.terms_conditions,
            status="DRAFT"
        )

    def get_quotation_summary(self, start_date: date, end_date: date) -> Dict:
        """Get summary statistics for quotations in date range"""
        quotations = Quotation.get_by_date_range(start_date, end_date)

        total_count = len(quotations)
        total_value = 0
        by_status = {}
        converted_count = 0

        for q in quotations:
            total_value += q.grand_total

            if q.status not in by_status:
                by_status[q.status] = {'count': 0, 'value': 0}
            by_status[q.status]['count'] += 1
            by_status[q.status]['value'] += q.grand_total

            if q.status == 'CONVERTED':
                converted_count += 1

        conversion_rate = (converted_count / total_count * 100) if total_count > 0 else 0

        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_count': total_count,
            'total_value': round(total_value, 2),
            'by_status': by_status,
            'converted_count': converted_count,
            'conversion_rate': round(conversion_rate, 1)
        }

    def check_expired_quotations(self) -> List[Quotation]:
        """Check and mark expired quotations"""
        today = date.today()

        # Get quotations that should be expired (past validity, still active)
        from database.db import get_connection
        conn = get_connection()
        rows = conn.execute("""
            SELECT id FROM quotations
            WHERE validity_date < ? AND status IN ('DRAFT', 'SENT')
        """, (today.isoformat(),)).fetchall()
        conn.close()

        expired = []
        for row in rows:
            quotation = Quotation.get_by_id(row['id'])
            if quotation:
                quotation.update_status('EXPIRED')
                expired.append(quotation)

        return expired

    def get_pending_quotations(self) -> List[Quotation]:
        """Get quotations awaiting response (SENT status)"""
        from database.db import get_connection
        conn = get_connection()
        rows = conn.execute("""
            SELECT id FROM quotations
            WHERE status = 'SENT'
            ORDER BY validity_date
        """).fetchall()
        conn.close()
        return [Quotation.get_by_id(row['id']) for row in rows]

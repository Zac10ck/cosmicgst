"""GST calculation engine"""
from dataclasses import dataclass
from typing import List
from config import DEFAULT_STATE_CODE


@dataclass
class TaxBreakdown:
    """Tax breakdown for a single item"""
    taxable_value: float
    cgst_rate: float
    cgst_amount: float
    sgst_rate: float
    sgst_amount: float
    igst_rate: float
    igst_amount: float
    total_tax: float
    total_amount: float


@dataclass
class CartItem:
    """Item in cart for calculation"""
    product_id: int
    product_name: str
    hsn_code: str
    qty: float
    unit: str
    rate: float
    gst_rate: float


class GSTCalculator:
    """
    GST Calculator for Indian taxation

    Intra-state (same state): CGST + SGST (each 50% of GST rate)
    Inter-state (different states): IGST (full GST rate)
    """

    def __init__(self, seller_state_code: str = DEFAULT_STATE_CODE):
        self.seller_state_code = seller_state_code

    def calculate_item_tax(
        self,
        qty: float,
        rate: float,
        gst_rate: float,
        buyer_state_code: str = None
    ) -> TaxBreakdown:
        """
        Calculate tax for a single item

        Args:
            qty: Quantity
            rate: Unit price (exclusive of tax)
            gst_rate: GST rate (0, 5, 12, 18, 28)
            buyer_state_code: Buyer's state code (for IGST determination)

        Returns:
            TaxBreakdown with all tax details
        """
        # Calculate taxable value
        taxable_value = round(qty * rate, 2)

        # Determine if inter-state or intra-state
        is_inter_state = (
            buyer_state_code is not None and
            buyer_state_code != self.seller_state_code
        )

        if is_inter_state:
            # Inter-state: IGST only
            igst_rate = gst_rate
            igst_amount = round(taxable_value * igst_rate / 100, 2)
            cgst_rate = 0
            cgst_amount = 0
            sgst_rate = 0
            sgst_amount = 0
        else:
            # Intra-state: CGST + SGST (each half of GST rate)
            igst_rate = 0
            igst_amount = 0
            cgst_rate = gst_rate / 2
            cgst_amount = round(taxable_value * cgst_rate / 100, 2)
            sgst_rate = gst_rate / 2
            sgst_amount = round(taxable_value * sgst_rate / 100, 2)

        total_tax = cgst_amount + sgst_amount + igst_amount
        total_amount = taxable_value + total_tax

        return TaxBreakdown(
            taxable_value=taxable_value,
            cgst_rate=cgst_rate,
            cgst_amount=cgst_amount,
            sgst_rate=sgst_rate,
            sgst_amount=sgst_amount,
            igst_rate=igst_rate,
            igst_amount=igst_amount,
            total_tax=total_tax,
            total_amount=round(total_amount, 2)
        )

    def calculate_cart_total(
        self,
        items: List[CartItem],
        buyer_state_code: str = None,
        discount: float = 0
    ) -> dict:
        """
        Calculate totals for entire cart

        Args:
            items: List of CartItem
            buyer_state_code: Buyer's state code
            discount: Discount amount (flat)

        Returns:
            Dictionary with all totals
        """
        subtotal = 0
        cgst_total = 0
        sgst_total = 0
        igst_total = 0

        item_details = []

        for item in items:
            tax = self.calculate_item_tax(
                qty=item.qty,
                rate=item.rate,
                gst_rate=item.gst_rate,
                buyer_state_code=buyer_state_code
            )

            subtotal += tax.taxable_value
            cgst_total += tax.cgst_amount
            sgst_total += tax.sgst_amount
            igst_total += tax.igst_amount

            item_details.append({
                'product_id': item.product_id,
                'product_name': item.product_name,
                'hsn_code': item.hsn_code,
                'qty': item.qty,
                'unit': item.unit,
                'rate': item.rate,
                'gst_rate': item.gst_rate,
                'taxable_value': tax.taxable_value,
                'cgst': tax.cgst_amount,
                'sgst': tax.sgst_amount,
                'igst': tax.igst_amount,
                'total': tax.total_amount
            })

        # Apply discount proportionally to taxable value
        # (In actual implementation, discount handling varies)
        total_tax = cgst_total + sgst_total + igst_total
        grand_total = subtotal + total_tax - discount

        return {
            'items': item_details,
            'subtotal': round(subtotal, 2),
            'cgst_total': round(cgst_total, 2),
            'sgst_total': round(sgst_total, 2),
            'igst_total': round(igst_total, 2),
            'total_tax': round(total_tax, 2),
            'discount': round(discount, 2),
            'grand_total': round(grand_total, 2)
        }

    @staticmethod
    def get_gst_rate_options() -> List[dict]:
        """Get GST rate options for dropdown"""
        return [
            {'value': 0, 'label': '0% (Exempt)'},
            {'value': 5, 'label': '5%'},
            {'value': 12, 'label': '12%'},
            {'value': 18, 'label': '18%'},
            {'value': 28, 'label': '28%'},
        ]

    @staticmethod
    def get_tax_summary_by_rate(items: List[dict]) -> List[dict]:
        """
        Group tax by GST rate for invoice summary

        Returns list of: {'gst_rate', 'taxable_value', 'cgst', 'sgst', 'igst'}
        """
        rate_summary = {}

        for item in items:
            rate = item['gst_rate']
            if rate not in rate_summary:
                rate_summary[rate] = {
                    'gst_rate': rate,
                    'taxable_value': 0,
                    'cgst': 0,
                    'sgst': 0,
                    'igst': 0
                }

            rate_summary[rate]['taxable_value'] += item['taxable_value']
            rate_summary[rate]['cgst'] += item.get('cgst', 0)
            rate_summary[rate]['sgst'] += item.get('sgst', 0)
            rate_summary[rate]['igst'] += item.get('igst', 0)

        # Sort by rate and round values
        result = []
        for rate in sorted(rate_summary.keys()):
            summary = rate_summary[rate]
            result.append({
                'gst_rate': rate,
                'taxable_value': round(summary['taxable_value'], 2),
                'cgst': round(summary['cgst'], 2),
                'sgst': round(summary['sgst'], 2),
                'igst': round(summary['igst'], 2)
            })

        return result

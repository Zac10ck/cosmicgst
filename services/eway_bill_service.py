"""e-Way Bill helper service for manual portal entry"""
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import date
from database.models import Invoice, Company, Customer

# e-Way Bill threshold (in INR)
EWAY_BILL_THRESHOLD = 50000

# Transport modes
TRANSPORT_MODES = ["Road", "Rail", "Air", "Ship"]

# Indian state codes for e-Way Bill
STATE_CODES = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "26": "Dadra & Nagar Haveli and Daman & Diu",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman & Nicobar",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
}


@dataclass
class EWayBillData:
    """Data structure for e-Way Bill generation"""
    # Document details
    document_type: str = "INV"  # Invoice
    document_number: str = ""
    document_date: str = ""

    # Supplier details
    supplier_gstin: str = ""
    supplier_name: str = ""
    supplier_address: str = ""
    supplier_state_code: str = ""
    supplier_pin_code: str = ""

    # Recipient details
    recipient_gstin: str = ""
    recipient_name: str = ""
    recipient_address: str = ""
    recipient_state_code: str = ""
    recipient_pin_code: str = ""

    # Supply type
    supply_type: str = "O"  # Outward
    sub_supply_type: str = "1"  # Supply

    # Transaction details
    taxable_value: float = 0.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    igst_amount: float = 0.0
    total_invoice_value: float = 0.0

    # Transport details
    transport_mode: str = "Road"
    vehicle_number: str = ""
    transporter_name: str = ""
    transporter_id: str = ""
    transport_distance: int = 0

    # Item summary
    items: List[Dict] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []


class EWayBillService:
    """Service for e-Way Bill data generation"""

    def __init__(self):
        self.company = Company.get()

    def is_eway_bill_required(self, invoice: Invoice) -> tuple:
        """
        Check if e-Way Bill is required for this invoice

        Returns:
            tuple: (is_required: bool, reason: str)
        """
        reasons = []

        # Check value threshold
        if invoice.grand_total >= EWAY_BILL_THRESHOLD:
            reasons.append(f"Invoice value (₹{invoice.grand_total:,.2f}) exceeds ₹{EWAY_BILL_THRESHOLD:,}")

        # Check inter-state
        if invoice.customer_id:
            customer = Customer.get_by_id(invoice.customer_id)
            if customer and self.company:
                if customer.state_code != self.company.state_code:
                    reasons.append(f"Inter-state transaction (Supplier: {self.company.state_code}, Recipient: {customer.state_code})")

        if reasons:
            return True, "; ".join(reasons)
        return False, "e-Way Bill not required"

    def generate_eway_bill_data(self, invoice: Invoice,
                                 vehicle_number: str = "",
                                 transport_mode: str = "Road",
                                 transporter_name: str = "",
                                 transporter_id: str = "",
                                 transport_distance: int = 0,
                                 recipient_pin: str = "") -> EWayBillData:
        """
        Generate e-Way Bill data from invoice

        Args:
            invoice: Invoice object
            vehicle_number: Vehicle registration number
            transport_mode: Road/Rail/Air/Ship
            transporter_name: Name of transporter
            transporter_id: GSTIN of transporter
            transport_distance: Distance in km
            recipient_pin: PIN code of recipient

        Returns:
            EWayBillData object with all required fields
        """
        company = self.company or Company(name="Your Shop", address="", gstin="", state_code="32")

        # Get customer details
        customer = None
        if invoice.customer_id:
            customer = Customer.get_by_id(invoice.customer_id)

        # Format date
        inv_date = invoice.invoice_date
        if isinstance(inv_date, str):
            inv_date = date.fromisoformat(inv_date)
        date_str = inv_date.strftime("%d/%m/%Y")

        # Build item list
        items = []
        for item in invoice.items:
            items.append({
                "hsn_code": item.hsn_code or "",
                "product_name": item.product_name,
                "quantity": item.qty,
                "unit": item.unit,
                "taxable_value": item.taxable_value,
                "gst_rate": item.gst_rate,
                "cgst": item.cgst,
                "sgst": item.sgst,
                "igst": item.igst,
                "total": item.total
            })

        # Determine supply type based on state codes
        supply_type = "O"  # Outward
        if customer and customer.state_code != company.state_code:
            sub_supply_type = "1"  # Inter-state supply
        else:
            sub_supply_type = "1"  # Intra-state supply

        return EWayBillData(
            # Document
            document_type="INV",
            document_number=invoice.invoice_number,
            document_date=date_str,

            # Supplier (Company)
            supplier_gstin=company.gstin or "",
            supplier_name=company.name,
            supplier_address=company.address or "",
            supplier_state_code=company.state_code or "32",
            supplier_pin_code="",  # Need to add to company settings

            # Recipient (Customer)
            recipient_gstin=customer.gstin if customer else "",
            recipient_name=invoice.customer_name or "Cash Customer",
            recipient_address=customer.address if customer else "",
            recipient_state_code=customer.state_code if customer else company.state_code,
            recipient_pin_code=recipient_pin or (customer.pin_code if customer else ""),

            # Supply type
            supply_type=supply_type,
            sub_supply_type=sub_supply_type,

            # Transaction
            taxable_value=invoice.subtotal,
            cgst_amount=invoice.cgst_total,
            sgst_amount=invoice.sgst_total,
            igst_amount=invoice.igst_total,
            total_invoice_value=invoice.grand_total,

            # Transport
            transport_mode=transport_mode,
            vehicle_number=vehicle_number,
            transporter_name=transporter_name,
            transporter_id=transporter_id,
            transport_distance=transport_distance,

            # Items
            items=items
        )

    def format_for_display(self, data: EWayBillData) -> str:
        """Format e-Way Bill data for display/copying"""
        lines = []
        lines.append("=" * 60)
        lines.append("e-WAY BILL DATA FOR PORTAL ENTRY")
        lines.append("=" * 60)
        lines.append("")

        # Document Details
        lines.append("DOCUMENT DETAILS:")
        lines.append(f"  Document Type: Tax Invoice")
        lines.append(f"  Document Number: {data.document_number}")
        lines.append(f"  Document Date: {data.document_date}")
        lines.append("")

        # Supplier Details
        lines.append("SUPPLIER (FROM) DETAILS:")
        lines.append(f"  GSTIN: {data.supplier_gstin or 'N/A'}")
        lines.append(f"  Name: {data.supplier_name}")
        lines.append(f"  Address: {data.supplier_address}")
        lines.append(f"  State: {STATE_CODES.get(data.supplier_state_code, data.supplier_state_code)} ({data.supplier_state_code})")
        lines.append("")

        # Recipient Details
        lines.append("RECIPIENT (TO) DETAILS:")
        lines.append(f"  GSTIN: {data.recipient_gstin or 'Unregistered'}")
        lines.append(f"  Name: {data.recipient_name}")
        lines.append(f"  Address: {data.recipient_address}")
        lines.append(f"  State: {STATE_CODES.get(data.recipient_state_code, data.recipient_state_code)} ({data.recipient_state_code})")
        lines.append(f"  PIN Code: {data.recipient_pin_code or 'Not provided'}")
        lines.append("")

        # Item Details
        lines.append("ITEM DETAILS:")
        lines.append("-" * 60)
        for i, item in enumerate(data.items, 1):
            lines.append(f"  {i}. {item['product_name']}")
            lines.append(f"     HSN: {item['hsn_code'] or 'N/A'} | Qty: {item['quantity']} {item['unit']}")
            lines.append(f"     Taxable: ₹{item['taxable_value']:,.2f} | GST: {item['gst_rate']}%")
        lines.append("-" * 60)
        lines.append("")

        # Value Details
        lines.append("VALUE DETAILS:")
        lines.append(f"  Taxable Value: ₹{data.taxable_value:,.2f}")
        if data.cgst_amount > 0:
            lines.append(f"  CGST: ₹{data.cgst_amount:,.2f}")
        if data.sgst_amount > 0:
            lines.append(f"  SGST: ₹{data.sgst_amount:,.2f}")
        if data.igst_amount > 0:
            lines.append(f"  IGST: ₹{data.igst_amount:,.2f}")
        lines.append(f"  Total Invoice Value: ₹{data.total_invoice_value:,.2f}")
        lines.append("")

        # Transport Details
        lines.append("TRANSPORT DETAILS:")
        lines.append(f"  Mode: {data.transport_mode}")
        if data.vehicle_number:
            lines.append(f"  Vehicle Number: {data.vehicle_number}")
        if data.transporter_name:
            lines.append(f"  Transporter Name: {data.transporter_name}")
        if data.transporter_id:
            lines.append(f"  Transporter ID: {data.transporter_id}")
        if data.transport_distance:
            lines.append(f"  Approximate Distance: {data.transport_distance} km")
        lines.append("")

        lines.append("=" * 60)
        lines.append("Please enter this data in the e-Way Bill portal:")
        lines.append("https://ewaybillgst.gov.in")
        lines.append("=" * 60)

        return "\n".join(lines)

    def export_to_json(self, data: EWayBillData) -> dict:
        """Export e-Way Bill data as JSON for reference"""
        return {
            "docType": data.document_type,
            "docNo": data.document_number,
            "docDate": data.document_date,
            "fromGstin": data.supplier_gstin,
            "fromTrdName": data.supplier_name,
            "fromAddr1": data.supplier_address,
            "fromStateCode": data.supplier_state_code,
            "toGstin": data.recipient_gstin,
            "toTrdName": data.recipient_name,
            "toAddr1": data.recipient_address,
            "toStateCode": data.recipient_state_code,
            "toPincode": data.recipient_pin_code,
            "transMode": {"Road": "1", "Rail": "2", "Air": "3", "Ship": "4"}.get(data.transport_mode, "1"),
            "vehicleNo": data.vehicle_number,
            "transporterId": data.transporter_id,
            "transDistance": str(data.transport_distance),
            "totInvValue": data.total_invoice_value,
            "cgstValue": data.cgst_amount,
            "sgstValue": data.sgst_amount,
            "igstValue": data.igst_amount,
            "itemList": [
                {
                    "productName": item["product_name"],
                    "hsnCode": item["hsn_code"],
                    "quantity": item["quantity"],
                    "qtyUnit": item["unit"],
                    "taxableAmount": item["taxable_value"],
                    "cgstRate": item["gst_rate"] / 2 if item["cgst"] > 0 else 0,
                    "sgstRate": item["gst_rate"] / 2 if item["sgst"] > 0 else 0,
                    "igstRate": item["gst_rate"] if item["igst"] > 0 else 0
                }
                for item in data.items
            ]
        }

    def save_eway_bill_number(self, invoice_id: int, eway_bill_number: str) -> bool:
        """Save e-Way Bill number to invoice after manual portal entry"""
        from database.db import get_connection
        try:
            conn = get_connection()
            conn.execute(
                "UPDATE invoices SET eway_bill_number = ? WHERE id = ?",
                (eway_bill_number, invoice_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving e-Way Bill number: {e}")
            return False

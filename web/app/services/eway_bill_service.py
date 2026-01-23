"""E-Way Bill service for GST compliance"""
from typing import Tuple, Dict, Any, Optional

# E-Way bill threshold (Rs. 50,000)
EWAY_BILL_THRESHOLD = 50000

# State code to name mapping
STATE_CODES = {
    '01': 'Jammu & Kashmir',
    '02': 'Himachal Pradesh',
    '03': 'Punjab',
    '04': 'Chandigarh',
    '05': 'Uttarakhand',
    '06': 'Haryana',
    '07': 'Delhi',
    '08': 'Rajasthan',
    '09': 'Uttar Pradesh',
    '10': 'Bihar',
    '11': 'Sikkim',
    '12': 'Arunachal Pradesh',
    '13': 'Nagaland',
    '14': 'Manipur',
    '15': 'Mizoram',
    '16': 'Tripura',
    '17': 'Meghalaya',
    '18': 'Assam',
    '19': 'West Bengal',
    '20': 'Jharkhand',
    '21': 'Odisha',
    '22': 'Chhattisgarh',
    '23': 'Madhya Pradesh',
    '24': 'Gujarat',
    '26': 'Dadra & Nagar Haveli and Daman & Diu',
    '27': 'Maharashtra',
    '28': 'Andhra Pradesh (Old)',
    '29': 'Karnataka',
    '30': 'Goa',
    '31': 'Lakshadweep',
    '32': 'Kerala',
    '33': 'Tamil Nadu',
    '34': 'Puducherry',
    '35': 'Andaman & Nicobar Islands',
    '36': 'Telangana',
    '37': 'Andhra Pradesh',
    '38': 'Ladakh',
}


def is_eway_bill_required(grand_total: float, is_inter_state: bool = False) -> Tuple[bool, str]:
    """
    Check if e-Way Bill is required for the transaction.

    Args:
        grand_total: Total invoice value including taxes
        is_inter_state: Whether the supply is inter-state

    Returns:
        Tuple of (required: bool, reason: str)
    """
    reasons = []

    if grand_total >= EWAY_BILL_THRESHOLD:
        reasons.append(f"Invoice value Rs.{grand_total:,.2f} exceeds Rs.{EWAY_BILL_THRESHOLD:,}")

    # For inter-state, e-Way bill may be required for smaller amounts in some states
    if is_inter_state and grand_total >= EWAY_BILL_THRESHOLD:
        reasons.append("Inter-state supply")

    if reasons:
        return True, "; ".join(reasons)
    return False, ""


def calculate_eway_validity(distance_km: int, is_over_dimensional: bool = False) -> int:
    """
    Calculate e-Way Bill validity period in days based on distance.

    Validity rules (as per GST regulations):
    - Regular cargo: 1 day per 100 km (or part thereof)
    - Over dimensional cargo (ODC): 1 day per 20 km (or part thereof)

    Args:
        distance_km: Transport distance in kilometers
        is_over_dimensional: Whether cargo is over dimensional

    Returns:
        Validity period in days
    """
    if distance_km <= 0:
        return 1

    if is_over_dimensional:
        # 1 day per 20 km for ODC
        return max(1, (distance_km + 19) // 20)
    else:
        # 1 day per 100 km for regular cargo
        return max(1, (distance_km + 99) // 100)


def get_transport_mode_code(mode: str) -> str:
    """
    Get transport mode code for e-Way bill.

    Args:
        mode: Transport mode name

    Returns:
        Transport mode code
    """
    modes = {
        'Road': '1',
        'Rail': '2',
        'Air': '3',
        'Ship': '4',
    }
    return modes.get(mode, '1')


def _get_transport_mode_name(code: str) -> str:
    """
    Get transport mode name from code.

    Args:
        code: Transport mode code

    Returns:
        Transport mode name
    """
    modes = {
        '1': 'Road',
        '2': 'Rail',
        '3': 'Air',
        '4': 'Ship',
    }
    return modes.get(code, 'Road')


def get_state_name(state_code: str) -> Optional[str]:
    """
    Get state name from state code.

    Args:
        state_code: 2-digit state code

    Returns:
        State name or None if not found
    """
    return STATE_CODES.get(str(state_code).zfill(2))


def validate_eway_bill_number(eway_number: str) -> Tuple[bool, str]:
    """
    Validate e-Way Bill number format.

    E-Way bill number is 12 digits.

    Args:
        eway_number: E-Way bill number to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not eway_number:
        return False, "E-Way Bill number is required"

    eway_number = str(eway_number).strip()

    if not eway_number.isdigit():
        return False, "E-Way Bill number must contain only digits"

    if len(eway_number) != 12:
        return False, "E-Way Bill number must be exactly 12 digits"

    return True, ""


def generate_eway_bill_data(invoice, company, customer=None) -> Dict[str, Any]:
    """
    Generate e-Way Bill data structure for GST portal upload.

    Args:
        invoice: Invoice model instance
        company: Company model instance
        customer: Optional Customer model instance

    Returns:
        Dictionary with e-Way bill data in GST portal format
    """
    # Determine seller/buyer state codes
    seller_state = company.state_code if company else '32'
    buyer_state = customer.state_code if customer else seller_state

    # Check if inter-state
    is_inter_state = buyer_state != seller_state

    # Build e-Way bill data structure
    eway_data = {
        # Supply details
        "supplyType": "O",  # O = Outward, I = Inward
        "subSupplyType": "1",  # 1 = Supply, 2 = Export, etc.
        "docType": "INV",  # INV = Invoice, BOE = Bill of Entry, etc.
        "docNo": invoice.invoice_number,
        "docDate": invoice.invoice_date.strftime("%d/%m/%Y") if invoice.invoice_date else "",

        # Supplier (From) details
        "fromGstin": company.gstin if company else "",
        "fromTrdName": company.name if company else "",
        "fromAddr1": company.address if company else "",
        "fromAddr2": "",
        "fromPlace": getattr(company, 'city', '') or "",
        "fromPincode": getattr(company, 'pin_code', '') or "",
        "fromStateCode": int(seller_state) if seller_state.isdigit() else 32,

        # Recipient (To) details
        "toGstin": customer.gstin if customer and customer.gstin else "URP",  # URP = Unregistered Person
        "toTrdName": invoice.customer_name or "Cash Customer",
        "toAddr1": customer.address if customer else "",
        "toAddr2": "",
        "toPlace": customer.city if customer else "",
        "toPincode": customer.pin_code if customer else "",
        "toStateCode": int(buyer_state) if buyer_state.isdigit() else int(seller_state),

        # Transport details
        "transMode": get_transport_mode_code(invoice.transport_mode or "Road"),
        "transDistance": str(invoice.transport_distance or 0),
        "transporterId": invoice.transporter_id or "",
        "transporterName": "",
        "vehicleNo": invoice.vehicle_number or "",
        "vehicleType": "R",  # R = Regular, O = Over Dimensional Cargo

        # Value details
        "totalValue": float(invoice.subtotal or 0),
        "cgstValue": float(invoice.cgst_total or 0),
        "sgstValue": float(invoice.sgst_total or 0),
        "igstValue": float(invoice.igst_total or 0),
        "cessValue": 0,
        "cessNonAdvolValue": 0,
        "otherValue": 0,
        "totInvValue": float(invoice.grand_total or 0),

        # Item list
        "itemList": []
    }

    # Add items
    items = list(invoice.items) if hasattr(invoice, 'items') else []
    for item in items:
        item_data = {
            "productName": item.product_name or "",
            "productDesc": item.product_name or "",
            "hsnCode": int(item.hsn_code) if item.hsn_code and item.hsn_code.isdigit() else 0,
            "quantity": float(item.qty or 0),
            "qtyUnit": item.unit or "NOS",
            "taxableAmount": float(item.taxable_value or 0),
        }

        # Set tax rates based on inter/intra state
        if is_inter_state:
            item_data["igstRate"] = float(item.gst_rate or 0)
            item_data["cgstRate"] = 0
            item_data["sgstRate"] = 0
        else:
            item_data["igstRate"] = 0
            item_data["cgstRate"] = float(item.gst_rate / 2) if item.gst_rate else 0
            item_data["sgstRate"] = float(item.gst_rate / 2) if item.gst_rate else 0

        item_data["cessRate"] = 0
        item_data["cessNonadvol"] = 0

        eway_data["itemList"].append(item_data)

    return eway_data


def format_eway_data_for_display(eway_data: Dict[str, Any]) -> str:
    """
    Format e-Way bill data for human-readable display.

    Args:
        eway_data: E-Way bill data dictionary

    Returns:
        Formatted string for display
    """
    lines = [
        "=" * 50,
        "E-WAY BILL DETAILS",
        "=" * 50,
        "",
        "DOCUMENT DETAILS",
        "-" * 30,
        f"Document Type: {eway_data.get('docType', 'INV')}",
        f"Document No: {eway_data.get('docNo', '')}",
        f"Document Date: {eway_data.get('docDate', '')}",
        f"Supply Type: {'Outward' if eway_data.get('supplyType') == 'O' else 'Inward'}",
        "",
        "SUPPLIER DETAILS (FROM)",
        "-" * 30,
        f"GSTIN: {eway_data.get('fromGstin', '')}",
        f"Name: {eway_data.get('fromTrdName', '')}",
        f"Address: {eway_data.get('fromAddr1', '')}",
        f"Place: {eway_data.get('fromPlace', '')}",
        f"PIN Code: {eway_data.get('fromPincode', '')}",
        f"State: {get_state_name(str(eway_data.get('fromStateCode', ''))) or eway_data.get('fromStateCode', '')}",
        "",
        "RECIPIENT DETAILS (TO)",
        "-" * 30,
        f"GSTIN: {eway_data.get('toGstin', '')}",
        f"Name: {eway_data.get('toTrdName', '')}",
        f"Address: {eway_data.get('toAddr1', '')}",
        f"Place: {eway_data.get('toPlace', '')}",
        f"PIN Code: {eway_data.get('toPincode', '')}",
        f"State: {get_state_name(str(eway_data.get('toStateCode', ''))) or eway_data.get('toStateCode', '')}",
        "",
        "TRANSPORT DETAILS",
        "-" * 30,
        f"Mode: {_get_transport_mode_name(eway_data.get('transMode', '1'))}",
        f"Distance: {eway_data.get('transDistance', '0')} km",
        f"Vehicle No: {eway_data.get('vehicleNo', 'N/A')}",
        f"Transporter ID: {eway_data.get('transporterId', 'N/A')}",
        "",
        "VALUE DETAILS",
        "-" * 30,
        f"Taxable Value: Rs. {eway_data.get('totalValue', 0):,.2f}",
        f"CGST: Rs. {eway_data.get('cgstValue', 0):,.2f}",
        f"SGST: Rs. {eway_data.get('sgstValue', 0):,.2f}",
        f"IGST: Rs. {eway_data.get('igstValue', 0):,.2f}",
        f"Total Invoice Value: Rs. {eway_data.get('totInvValue', 0):,.2f}",
        "",
        "=" * 50,
    ]

    return "\n".join(lines)

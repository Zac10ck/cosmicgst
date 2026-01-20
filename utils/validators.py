"""Input validators for GST compliance"""
import re


def validate_gstin(gstin: str) -> tuple[bool, str]:
    """
    Validate GSTIN format (15 characters)
    Format: 22AAAAA0000A1Z5
    - First 2 digits: State Code (01-38)
    - Next 10 chars: PAN
    - 13th char: Entity number (1-9, A-Z)
    - 14th char: Z (default)
    - 15th char: Checksum

    Returns: (is_valid, error_message)
    """
    if not gstin:
        return True, ""  # Empty is valid (for B2C)

    gstin = gstin.upper().strip()

    if len(gstin) != 15:
        return False, "GSTIN must be 15 characters"

    # Pattern: 2 digits + 5 letters + 4 digits + 1 letter + 1 alphanumeric + Z + 1 alphanumeric
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}$'

    if not re.match(pattern, gstin):
        return False, "Invalid GSTIN format"

    # Validate state code (01-38)
    state_code = gstin[:2]
    valid_state_codes = [str(i).zfill(2) for i in range(1, 39)]
    if state_code not in valid_state_codes:
        return False, f"Invalid state code: {state_code}"

    return True, ""


def validate_hsn(hsn_code: str) -> tuple[bool, str]:
    """
    Validate HSN/SAC code
    - HSN codes are 4, 6, or 8 digits (for goods)
    - SAC codes are 6 digits starting with 99 (for services)

    Returns: (is_valid, error_message)
    """
    if not hsn_code:
        return True, ""  # Empty is valid for some cases

    hsn_code = hsn_code.strip()

    # Check if numeric
    if not hsn_code.isdigit():
        return False, "HSN/SAC code must contain only digits"

    # Valid lengths
    if len(hsn_code) not in [4, 6, 8]:
        return False, "HSN code must be 4, 6, or 8 digits"

    return True, ""


def validate_phone(phone: str) -> tuple[bool, str]:
    """
    Validate Indian phone number

    Returns: (is_valid, error_message)
    """
    if not phone:
        return True, ""

    # Remove spaces, dashes, and +91 prefix
    phone = phone.replace(" ", "").replace("-", "")
    if phone.startswith("+91"):
        phone = phone[3:]
    if phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]

    if not phone.isdigit():
        return False, "Phone number must contain only digits"

    if len(phone) != 10:
        return False, "Phone number must be 10 digits"

    if phone[0] not in "6789":
        return False, "Invalid phone number"

    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format

    Returns: (is_valid, error_message)
    """
    if not email:
        return True, ""

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False, "Invalid email format"

    return True, ""


def validate_invoice_number(invoice_number: str) -> tuple[bool, str]:
    """
    Validate invoice number format: INV/YYYY-YY/NNNN

    Returns: (is_valid, error_message)
    """
    if not invoice_number:
        return False, "Invoice number is required"

    pattern = r'^[A-Z]{2,5}/\d{4}-\d{2}/\d{4,}$'

    if not re.match(pattern, invoice_number):
        return False, "Invalid invoice number format"

    return True, ""

"""
Validation utilities for GST billing application.

Includes validators for:
- HSN codes (4, 6, or 8 digits)
- GSTIN (15-character format with checksum)
- Quantity and rate values
"""

import re
from typing import Tuple, Optional


def validate_hsn_code(hsn_code: str) -> Tuple[bool, str]:
    """
    Validate HSN (Harmonized System of Nomenclature) code format.

    HSN codes in India must be:
    - 4 digits for businesses with turnover <= 1.5 crores
    - 6 digits for businesses with turnover <= 5 crores
    - 8 digits for businesses with turnover > 5 crores

    Args:
        hsn_code: The HSN code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not hsn_code:
        return True, ""  # Empty is allowed for non-GST items

    hsn_code = str(hsn_code).strip()

    if not hsn_code.isdigit():
        return False, "HSN code must contain only digits"

    if len(hsn_code) not in [4, 6, 8]:
        return False, "HSN code must be 4, 6, or 8 digits"

    return True, ""


def validate_gstin(gstin: str) -> Tuple[bool, str]:
    """
    Validate GSTIN (Goods and Services Tax Identification Number) format.

    GSTIN format: SSPPPPPPPPPPPPPC (15 characters)
    - SS: 2-digit state code (01-38)
    - PPPPPPPPPP: 10-character PAN
    - P: 13th character (entity type: 1-9 or Z)
    - P: 14th character (default: Z)
    - C: Check digit (mod-36 algorithm)

    Args:
        gstin: The GSTIN to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not gstin:
        return True, ""  # Empty allowed for B2C customers

    gstin = str(gstin).strip().upper()

    if len(gstin) != 15:
        return False, "GSTIN must be exactly 15 characters"

    # Basic pattern validation
    # Format: 2 digits state + 5 letters + 4 digits + 1 letter + 1 alphanumeric + Z + check digit
    pattern = r'^[0-3][0-9][A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$'
    if not re.match(pattern, gstin):
        return False, "Invalid GSTIN format"

    # Validate state code (01-38, excluding some unused codes)
    state_code = int(gstin[:2])
    valid_state_codes = set(range(1, 39)) - {25}  # 25 is not assigned
    if state_code not in valid_state_codes:
        return False, f"Invalid state code: {gstin[:2]}"

    # Validate checksum
    if not _verify_gstin_checksum(gstin):
        return False, "Invalid GSTIN checksum"

    return True, ""


def _verify_gstin_checksum(gstin: str) -> bool:
    """
    Verify GSTIN check digit using mod-36 algorithm.

    The checksum is calculated using a modified Luhn algorithm:
    1. Map characters to values (0-9, A=10, B=11, ..., Z=35)
    2. Multiply odd positions by 1, even positions by 2
    3. Sum the results (with carry handling)
    4. Check digit = (36 - (sum % 36)) % 36

    Args:
        gstin: The GSTIN to verify (must be uppercase)

    Returns:
        True if checksum is valid, False otherwise
    """
    # Character to value mapping
    char_map = {}
    for i in range(10):
        char_map[str(i)] = i
    for i, char in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        char_map[char] = 10 + i

    factor = 1
    total = 0

    for i, char in enumerate(gstin[:-1]):  # Exclude last character (check digit)
        digit = char_map.get(char, 0)
        digit *= factor

        # Handle carry for base-36
        digit = (digit // 36) + (digit % 36)
        total += digit

        # Alternate between 1 and 2
        factor = 2 if factor == 1 else 1

    # Calculate expected check digit
    check_digit = (36 - (total % 36)) % 36

    # Convert to character
    if check_digit < 10:
        expected_char = str(check_digit)
    else:
        expected_char = chr(ord('A') + check_digit - 10)

    return gstin[-1] == expected_char


def validate_quantity(qty, product_name: str = 'item') -> Tuple[bool, str]:
    """
    Validate quantity value.

    Args:
        qty: The quantity to validate
        product_name: Product name for error message

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        qty = float(qty)
    except (TypeError, ValueError):
        return False, f"Invalid quantity for {product_name}"

    if qty <= 0:
        return False, f"Quantity must be greater than 0 for {product_name}"

    return True, ""


def validate_rate(rate, product_name: str = 'item') -> Tuple[bool, str]:
    """
    Validate rate/price value.

    Args:
        rate: The rate to validate
        product_name: Product name for error message

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        rate = float(rate)
    except (TypeError, ValueError):
        return False, f"Invalid rate for {product_name}"

    if rate < 0:
        return False, f"Rate cannot be negative for {product_name}"

    return True, ""


def validate_gst_rate(gst_rate) -> Tuple[bool, str]:
    """
    Validate GST rate value.

    Valid GST rates in India: 0%, 5%, 12%, 18%, 28%
    (Also 0.25% and 3% for special items, but we'll keep it simple)

    Args:
        gst_rate: The GST rate to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        gst_rate = float(gst_rate)
    except (TypeError, ValueError):
        return False, "Invalid GST rate"

    valid_rates = [0, 5, 12, 18, 28]

    if gst_rate not in valid_rates:
        return False, f"Invalid GST rate: {gst_rate}%. Valid rates: {', '.join(map(str, valid_rates))}%"

    return True, ""


def validate_discount(discount, subtotal: float) -> Tuple[bool, str]:
    """
    Validate discount amount.

    Args:
        discount: The discount amount to validate
        subtotal: The subtotal to compare against

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        discount = float(discount) if discount else 0
    except (TypeError, ValueError):
        return False, "Invalid discount amount"

    if discount < 0:
        return False, "Discount cannot be negative"

    if discount > subtotal:
        return False, f"Discount (₹{discount:.2f}) cannot exceed subtotal (₹{subtotal:.2f})"

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address format.

    Args:
        email: The email address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return True, ""  # Empty is allowed (optional field)

    email = str(email).strip()

    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False, "Invalid email address format"

    return True, ""


def validate_vehicle_number(vehicle_no: str) -> Tuple[bool, str]:
    """
    Validate Indian vehicle registration number format.

    Formats accepted:
    - KL-01-AB-1234
    - KL01AB1234
    - KL 01 AB 1234

    Args:
        vehicle_no: The vehicle number to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not vehicle_no:
        return True, ""  # Empty is allowed (optional field)

    # Remove spaces and hyphens, convert to uppercase
    vehicle_no = re.sub(r'[\s-]', '', str(vehicle_no).upper())

    # Indian vehicle number format: SS DD AA NNNN
    # SS: State code (2 letters)
    # DD: District code (2 digits)
    # AA: Series (1-2 letters)
    # NNNN: Number (1-4 digits)
    pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}$'

    if not re.match(pattern, vehicle_no):
        return False, "Invalid vehicle number format. Expected format: KL-01-AB-1234"

    return True, ""


def validate_pin_code(pin_code: str) -> Tuple[bool, str]:
    """
    Validate Indian PIN code.

    Args:
        pin_code: The PIN code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not pin_code:
        return True, ""  # Empty is allowed

    pin_code = str(pin_code).strip()

    if not pin_code.isdigit():
        return False, "PIN code must contain only digits"

    if len(pin_code) != 6:
        return False, "PIN code must be exactly 6 digits"

    # First digit should be 1-9 (not 0)
    if pin_code[0] == '0':
        return False, "Invalid PIN code"

    return True, ""


# State code mapping for validation
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


def get_state_name(state_code: str) -> Optional[str]:
    """
    Get state name from state code.

    Args:
        state_code: 2-digit state code

    Returns:
        State name or None if not found
    """
    return STATE_CODES.get(str(state_code).zfill(2))


def validate_state_code(state_code: str) -> Tuple[bool, str]:
    """
    Validate Indian state code.

    Args:
        state_code: The state code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not state_code:
        return True, ""  # Empty is allowed

    state_code = str(state_code).strip().zfill(2)

    if state_code not in STATE_CODES:
        return False, f"Invalid state code: {state_code}"

    return True, ""

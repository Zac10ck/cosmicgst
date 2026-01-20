"""Formatting utilities for display and printing"""
from datetime import date, datetime

# Try to import num2words, fallback to simple implementation
try:
    from num2words import num2words
    HAS_NUM2WORDS = True
except ImportError:
    HAS_NUM2WORDS = False


def format_currency(amount: float, symbol: str = "") -> str:
    """
    Format amount as Indian currency with lakhs/crores grouping

    Example: 1234567.89 -> 12,34,567.89
    """
    if amount < 0:
        return f"-{format_currency(abs(amount), symbol)}"

    # Split into integer and decimal parts
    int_part = int(amount)
    dec_part = round((amount - int_part) * 100)

    # Format integer part with Indian grouping
    s = str(int_part)
    if len(s) > 3:
        # Last 3 digits
        result = s[-3:]
        s = s[:-3]
        # Group remaining in pairs
        while s:
            if len(s) >= 2:
                result = s[-2:] + "," + result
                s = s[:-2]
            else:
                result = s + "," + result
                break
    else:
        result = s

    # Add decimal part
    if dec_part > 0:
        result = f"{result}.{dec_part:02d}"
    else:
        result = f"{result}.00"

    if symbol:
        return f"{symbol} {result}"
    return result


def _simple_num_to_words(n: int) -> str:
    """Simple number to words fallback (basic implementation)"""
    if n == 0:
        return "Zero"

    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _convert_chunk(num):
        if num == 0:
            return ""
        elif num < 20:
            return ones[num]
        elif num < 100:
            return tens[num // 10] + (" " + ones[num % 10] if num % 10 else "")
        else:
            return ones[num // 100] + " Hundred" + (" " + _convert_chunk(num % 100) if num % 100 else "")

    if n >= 10000000:  # Crores
        crores = n // 10000000
        remainder = n % 10000000
        result = _convert_chunk(crores) + " Crore"
        if remainder:
            result += " " + _simple_num_to_words(remainder)
        return result
    elif n >= 100000:  # Lakhs
        lakhs = n // 100000
        remainder = n % 100000
        result = _convert_chunk(lakhs) + " Lakh"
        if remainder:
            result += " " + _simple_num_to_words(remainder)
        return result
    elif n >= 1000:  # Thousands
        thousands = n // 1000
        remainder = n % 1000
        result = _convert_chunk(thousands) + " Thousand"
        if remainder:
            result += " " + _convert_chunk(remainder)
        return result
    else:
        return _convert_chunk(n)


def number_to_words_indian(amount: float) -> str:
    """
    Convert number to words in Indian format

    Example: 1234.50 -> "One Thousand Two Hundred Thirty-Four Rupees and Fifty Paise Only"
    """
    if amount == 0:
        return "Zero Rupees Only"

    # Split into rupees and paise
    rupees = int(amount)
    paise = round((amount - rupees) * 100)

    result = ""

    if rupees > 0:
        if HAS_NUM2WORDS:
            rupees_words = num2words(rupees, lang='en_IN').title()
        else:
            rupees_words = _simple_num_to_words(rupees)
        result = f"{rupees_words} Rupees"

    if paise > 0:
        if HAS_NUM2WORDS:
            paise_words = num2words(paise, lang='en_IN').title()
        else:
            paise_words = _simple_num_to_words(paise)
        if result:
            result += f" and {paise_words} Paise"
        else:
            result = f"{paise_words} Paise"

    result += " Only"

    return result


def format_date(d: date | datetime, fmt: str = "dd-MMM-yyyy") -> str:
    """
    Format date for display

    Formats:
    - dd-MMM-yyyy: 20-Jan-2026
    - dd/MM/yyyy: 20/01/2026
    - yyyy-MM-dd: 2026-01-20
    """
    if isinstance(d, str):
        d = datetime.fromisoformat(d)

    if fmt == "dd-MMM-yyyy":
        return d.strftime("%d-%b-%Y")
    elif fmt == "dd/MM/yyyy":
        return d.strftime("%d/%m/%Y")
    elif fmt == "yyyy-MM-dd":
        return d.strftime("%Y-%m-%d")
    else:
        return d.strftime("%d-%b-%Y")


def format_quantity(qty: float, unit: str = "") -> str:
    """Format quantity with appropriate decimal places"""
    if qty == int(qty):
        result = str(int(qty))
    else:
        result = f"{qty:.2f}".rstrip('0').rstrip('.')

    if unit:
        result = f"{result} {unit}"

    return result


def format_gst_rate(rate: float) -> str:
    """Format GST rate for display"""
    if rate == int(rate):
        return f"{int(rate)}%"
    return f"{rate:.1f}%"


def format_invoice_number(number: str) -> str:
    """Format invoice number for display"""
    return number.upper()

"""Premium PDF Generator for GST Invoices - Modern Professional Design"""
from io import BytesIO
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, KeepTogether, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF


# State code to name mapping (India)
STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra & Nagar Haveli", "27": "Maharashtra", "28": "Andhra Pradesh",
    "29": "Karnataka", "30": "Goa", "31": "Lakshadweep",
    "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry",
    "35": "Andaman & Nicobar", "36": "Telangana", "37": "Andhra Pradesh (New)",
    "38": "Ladakh"
}

# Premium Modern Color Scheme
COLORS = {
    # Primary Colors - Deep Professional Blue
    'primary': colors.HexColor('#1a237e'),         # Indigo 900
    'primary_light': colors.HexColor('#3949ab'),   # Indigo 600
    'primary_dark': colors.HexColor('#0d1b5e'),    # Darker Indigo

    # Accent Colors
    'accent': colors.HexColor('#00bfa5'),          # Teal A700
    'accent_light': colors.HexColor('#64ffda'),    # Teal A200

    # Header Gradient Effect Colors
    'header_start': colors.HexColor('#1a237e'),    # Deep Blue
    'header_end': colors.HexColor('#283593'),      # Indigo 800

    # Status Colors
    'success': colors.HexColor('#00c853'),         # Green A700
    'warning': colors.HexColor('#ff6d00'),         # Orange A700
    'danger': colors.HexColor('#d50000'),          # Red A700

    # Backgrounds
    'bg_light': colors.HexColor('#f5f7ff'),        # Very light blue
    'bg_card': colors.HexColor('#e8eaf6'),         # Indigo 50
    'bg_highlight': colors.HexColor('#c5cae9'),    # Indigo 100
    'bg_white': colors.white,

    # Borders
    'border': colors.HexColor('#c5cae9'),          # Indigo 100
    'border_dark': colors.HexColor('#7986cb'),     # Indigo 300

    # Text Colors
    'text_primary': colors.HexColor('#1a237e'),    # Match primary
    'text_dark': colors.HexColor('#212121'),       # Grey 900
    'text_secondary': colors.HexColor('#616161'),  # Grey 700
    'text_muted': colors.HexColor('#9e9e9e'),      # Grey 500
    'text_white': colors.white,

    # Table Colors
    'table_header': colors.HexColor('#1a237e'),    # Primary
    'table_row_alt': colors.HexColor('#f5f7ff'),   # Light alternating
    'table_border': colors.HexColor('#e0e0e0'),    # Light grey

    # Total Section
    'total_bg': colors.HexColor('#1a237e'),        # Primary for grand total
    'subtotal_bg': colors.HexColor('#e8eaf6'),     # Light for subtotals
}


def get_state_name(state_code):
    """Get state name from code"""
    return STATE_CODES.get(str(state_code), f"State {state_code}")


def format_currency(amount):
    """Format amount as Indian currency"""
    if amount is None:
        amount = 0
    return f"₹ {amount:,.2f}"


def format_number(amount):
    """Format number with commas"""
    if amount is None:
        amount = 0
    return f"{amount:,.2f}"


def number_to_words_indian(num):
    """Convert number to words using Indian numbering system"""
    if num is None:
        num = 0

    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
            'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
            'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

    if num == 0:
        return 'Zero Rupees Only'

    def words(n):
        if n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + ('' if n % 10 == 0 else ' ' + ones[n % 10])
        elif n < 1000:
            return ones[n // 100] + ' Hundred' + ('' if n % 100 == 0 else ' and ' + words(n % 100))
        elif n < 100000:
            return words(n // 1000) + ' Thousand' + ('' if n % 1000 == 0 else ' ' + words(n % 1000))
        elif n < 10000000:
            return words(n // 100000) + ' Lakh' + ('' if n % 100000 == 0 else ' ' + words(n % 100000))
        else:
            return words(n // 10000000) + ' Crore' + ('' if n % 10000000 == 0 else ' ' + words(n % 10000000))

    rupees = int(num)
    paise = int(round((num - rupees) * 100))

    result = words(rupees) + ' Rupees'
    if paise > 0:
        result += ' and ' + words(paise) + ' Paise'
    result += ' Only'
    return result


class PDFGenerator:
    """Premium PDF Generator with Modern Professional Design"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.page_width, self.page_height = A4
        self.margin = 10 * mm
        self.content_width = self.page_width - (2 * self.margin)

    def _setup_styles(self):
        """Set up premium paragraph styles"""

        # Company Name - Large and Premium
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            fontSize=22,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            alignment=TA_LEFT,
            spaceAfter=2*mm,
            leading=26
        ))

        # Company Tagline
        self.styles.add(ParagraphStyle(
            name='CompanyTagline',
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=COLORS['text_secondary'],
            alignment=TA_LEFT,
            spaceAfter=1*mm,
            leading=11
        ))

        # Company Details
        self.styles.add(ParagraphStyle(
            name='CompanyDetails',
            fontSize=9,
            fontName='Helvetica',
            textColor=COLORS['text_dark'],
            alignment=TA_LEFT,
            spaceAfter=0.5*mm,
            leading=12
        ))

        # Document Title (TAX INVOICE)
        self.styles.add(ParagraphStyle(
            name='DocTitle',
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=COLORS['text_white'],
            alignment=TA_CENTER,
            leading=20
        ))

        # Section Header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            spaceBefore=3*mm,
            spaceAfter=2*mm,
            leading=14
        ))

        # Party Name (Customer/Company)
        self.styles.add(ParagraphStyle(
            name='PartyName',
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=COLORS['text_dark'],
            leading=14
        ))

        self.styles.add(ParagraphStyle(
            name='PartyDetails',
            fontSize=9,
            fontName='Helvetica',
            textColor=COLORS['text_secondary'],
            leading=12
        ))

        # Invoice Number Style
        self.styles.add(ParagraphStyle(
            name='InvoiceNumber',
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            alignment=TA_RIGHT,
            leading=15
        ))

        self.styles.add(ParagraphStyle(
            name='InvoiceInfo',
            fontSize=9,
            fontName='Helvetica',
            textColor=COLORS['text_dark'],
            alignment=TA_RIGHT,
            leading=12
        ))

        # Amount in Words
        self.styles.add(ParagraphStyle(
            name='AmountWords',
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=COLORS['text_dark'],
            alignment=TA_LEFT,
            leading=12,
            backColor=COLORS['bg_light'],
            borderPadding=3*mm
        ))

        # Footer
        self.styles.add(ParagraphStyle(
            name='Footer',
            fontSize=8,
            fontName='Helvetica',
            textColor=COLORS['text_muted'],
            alignment=TA_LEFT,
            leading=10
        ))

        self.styles.add(ParagraphStyle(
            name='FooterCenter',
            fontSize=8,
            fontName='Helvetica',
            textColor=COLORS['text_secondary'],
            alignment=TA_CENTER,
            leading=10
        ))

        # Bank Details
        self.styles.add(ParagraphStyle(
            name='BankHeader',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            leading=13
        ))

        self.styles.add(ParagraphStyle(
            name='BankDetails',
            fontSize=9,
            fontName='Helvetica',
            textColor=COLORS['text_dark'],
            leading=12
        ))

        # Badge Style for Status
        self.styles.add(ParagraphStyle(
            name='Badge',
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=COLORS['text_white'],
            alignment=TA_CENTER,
            leading=10
        ))

    def generate_invoice_pdf(self, invoice, company, items):
        """Generate premium invoice PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )

        elements = []

        # Determine invoice type
        invoice_type = getattr(invoice, 'invoice_type', 'TAX_INVOICE')
        is_cancelled = getattr(invoice, 'is_cancelled', False)
        doc_title = 'BILL OF SUPPLY' if invoice_type == 'BILL_OF_SUPPLY' else 'TAX INVOICE'

        # 1. Compact Header
        elements.extend(self._build_compact_header(company, doc_title, invoice, is_cancelled))

        # 2. Billing Parties (From/To) - Compact
        elements.extend(self._build_compact_billing_parties(company, invoice))

        # 3. Items Table with modern styling
        elements.extend(self._build_modern_items_table(items))

        # 4. Totals Section with Amount in Words
        elements.extend(self._build_compact_totals(invoice))

        # 5. HSN Summary (compact)
        hsn_summary = self._calculate_hsn_summary(items)
        if hsn_summary:
            elements.extend(self._build_compact_hsn_summary(hsn_summary))

        # 6. E-Way Bill Info (if exists)
        eway_number = getattr(invoice, 'eway_bill_number', '')
        if eway_number:
            elements.extend(self._build_eway_bill_section(invoice))

        # 7. Bank Details & Payment Info
        elements.extend(self._build_compact_footer_section(company, invoice))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_premium_header(self, company, doc_type, doc, is_cancelled=False):
        """Build premium header with modern design"""
        elements = []

        # Get document details
        if hasattr(doc, 'invoice_number'):
            doc_number = doc.invoice_number
            doc_date = doc.invoice_date
        elif hasattr(doc, 'quotation_number'):
            doc_number = doc.quotation_number
            doc_date = doc.quotation_date
        elif hasattr(doc, 'credit_note_number'):
            doc_number = doc.credit_note_number
            doc_date = doc.credit_note_date
        else:
            doc_number = 'N/A'
            doc_date = date.today()

        # === LEFT SIDE: Company Info ===
        company_name = company.name if company else 'Company Name'
        left_content = []

        # Company Name with accent line
        left_content.append([Paragraph(f"<font color='#1a237e'>{company_name}</font>", self.styles['CompanyName'])])

        if company:
            # Tagline
            left_content.append([Paragraph("Premium Surgical Equipment Supplier", self.styles['CompanyTagline'])])

            # Address
            if company.address:
                left_content.append([Paragraph(f"📍 {company.address}", self.styles['CompanyDetails'])])

            # Contact
            contact_parts = []
            if company.phone:
                contact_parts.append(f"📞 {company.phone}")
            if company.email:
                contact_parts.append(f"✉ {company.email}")
            if contact_parts:
                left_content.append([Paragraph('  |  '.join(contact_parts), self.styles['CompanyDetails'])])

            # GSTIN & PAN
            if company.gstin:
                left_content.append([Paragraph(f"<b>GSTIN:</b> {company.gstin}", self.styles['CompanyDetails'])])

        left_table = Table(left_content, colWidths=[115*mm])
        left_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5*mm),
        ]))

        # === RIGHT SIDE: Invoice Info Box ===
        right_content = []

        # Invoice number - large
        right_content.append([Paragraph(f"<font size='14'><b>{doc_number}</b></font>", self.styles['InvoiceNumber'])])
        right_content.append([Spacer(1, 2*mm)])
        right_content.append([Paragraph(f"<b>Date:</b> {doc_date.strftime('%d %b %Y') if doc_date else ''}", self.styles['InvoiceInfo'])])

        # Payment status badge
        payment_status = getattr(doc, 'payment_status', 'UNPAID')
        if payment_status == 'PAID':
            status_color = '#00c853'
        elif payment_status == 'PARTIAL':
            status_color = '#ff6d00'
        else:
            status_color = '#d50000'

        right_content.append([Paragraph(f"<font color='{status_color}'><b>● {payment_status}</b></font>", self.styles['InvoiceInfo'])])

        right_table = Table(right_content, colWidths=[65*mm])
        right_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_card']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))

        # Combine header
        header_table = Table([[left_table, right_table]], colWidths=[120*mm, 70*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 4*mm))

        # === DOCUMENT TITLE BAR ===
        if is_cancelled:
            title_text = f"{doc_type} - CANCELLED"
            title_bg = COLORS['danger']
        else:
            title_text = doc_type
            title_bg = COLORS['primary']

        title_table = Table(
            [[Paragraph(title_text, self.styles['DocTitle'])]],
            colWidths=[self.content_width]
        )
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), title_bg),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
        ]))
        elements.append(title_table)
        elements.append(Spacer(1, 4*mm))

        return elements

    def _build_invoice_summary_cards(self, invoice):
        """Build summary info cards"""
        elements = []

        supply_type = getattr(invoice, 'supply_type', 'B2C')
        buyer_state = getattr(invoice, 'buyer_state_code', '32')
        is_rcm = getattr(invoice, 'is_reverse_charge', False)
        customer_gstin = getattr(invoice, 'customer_gstin', '')

        # Create info cards
        cards_data = []

        # Supply Type
        cards_data.append(self._create_info_card("Supply Type", supply_type, COLORS['accent']))

        # Place of Supply
        pos_name = get_state_name(buyer_state)
        cards_data.append(self._create_info_card("Place of Supply", f"{pos_name} ({buyer_state})", COLORS['primary_light']))

        # Reverse Charge
        rcm_text = "Yes" if is_rcm else "No"
        cards_data.append(self._create_info_card("Reverse Charge", rcm_text, COLORS['warning'] if is_rcm else COLORS['success']))

        # Payment Mode
        payment_mode = getattr(invoice, 'payment_mode', 'CASH')
        cards_data.append(self._create_info_card("Payment", payment_mode, COLORS['primary']))

        cards_table = Table([cards_data], colWidths=[self.content_width/4]*4)
        cards_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1*mm),
        ]))
        elements.append(cards_table)
        elements.append(Spacer(1, 4*mm))

        return elements

    def _create_info_card(self, label, value, accent_color):
        """Create a mini info card"""
        card_content = [
            [Paragraph(f"<font size='7' color='#616161'>{label}</font>", self.styles['CompanyDetails'])],
            [Paragraph(f"<font size='10'><b>{value}</b></font>", self.styles['CompanyDetails'])]
        ]
        card = Table(card_content, colWidths=[45*mm])
        card.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_light']),
            ('LINEABOVE', (0, 0), (-1, 0), 3, accent_color),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        return card

    def _build_modern_billing_parties(self, company, invoice):
        """Build modern billing parties section"""
        elements = []

        # Get customer details
        customer = getattr(invoice, 'customer', None)
        customer_name = invoice.customer_name or 'Walk-in Customer'

        # === BILL FROM ===
        from_header = Paragraph("<font color='#1a237e'><b>BILL FROM</b></font>", self.styles['SectionHeader'])
        from_content = []
        if company:
            from_content.append(Paragraph(f"<b>{company.name}</b>", self.styles['PartyName']))
            if company.address:
                from_content.append(Paragraph(company.address, self.styles['PartyDetails']))
            if company.gstin:
                from_content.append(Paragraph(f"<b>GSTIN:</b> {company.gstin}", self.styles['PartyDetails']))
            if company.state_code:
                from_content.append(Paragraph(f"<b>State:</b> {get_state_name(company.state_code)} ({company.state_code})", self.styles['PartyDetails']))
            if company.phone:
                from_content.append(Paragraph(f"<b>Phone:</b> {company.phone}", self.styles['PartyDetails']))

        from_table_data = [[from_header]] + [[p] for p in from_content]
        from_table = Table(from_table_data, colWidths=[90*mm])
        from_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_white']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
            ('LINEBELOW', (0, 0), (-1, 0), 2, COLORS['primary']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))

        # === BILL TO ===
        to_header = Paragraph("<font color='#1a237e'><b>BILL TO</b></font>", self.styles['SectionHeader'])
        to_content = []
        to_content.append(Paragraph(f"<b>{customer_name}</b>", self.styles['PartyName']))
        if customer:
            if customer.address:
                to_content.append(Paragraph(customer.address, self.styles['PartyDetails']))
            if customer.gstin:
                to_content.append(Paragraph(f"<b>GSTIN:</b> {customer.gstin}", self.styles['PartyDetails']))
            if customer.state_code:
                to_content.append(Paragraph(f"<b>State:</b> {get_state_name(customer.state_code)} ({customer.state_code})", self.styles['PartyDetails']))
            if hasattr(customer, 'phone') and customer.phone:
                to_content.append(Paragraph(f"<b>Phone:</b> {customer.phone}", self.styles['PartyDetails']))

        to_table_data = [[to_header]] + [[p] for p in to_content]
        to_table = Table(to_table_data, colWidths=[90*mm])
        to_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_card']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['primary']),
            ('LINEBELOW', (0, 0), (-1, 0), 2, COLORS['primary']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))

        # Combine
        parties_table = Table([[from_table, to_table]], colWidths=[95*mm, 95*mm])
        parties_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 5*mm))

        return elements

    def _build_modern_items_table(self, items):
        """Build modern items table with premium styling"""
        elements = []

        # Section header
        elements.append(Paragraph("<font color='#1a237e'><b>ITEM DETAILS</b></font>", self.styles['SectionHeader']))

        # Headers
        headers = ['#', 'Product Description', 'HSN', 'Qty', 'Unit', 'Rate', 'GST%', 'Amount']
        data = [headers]

        # Rows
        for i, item in enumerate(items, 1):
            product_name = (item.product_name or '')[:35]
            batch = getattr(item, 'batch_number', '')
            if batch:
                product_name += f"\n<font size='7' color='#616161'>Batch: {batch}</font>"

            data.append([
                str(i),
                Paragraph(product_name, self.styles['PartyDetails']),
                item.hsn_code or '-',
                f"{item.qty:.0f}" if item.qty == int(item.qty) else f"{item.qty:.2f}",
                item.unit or 'NOS',
                format_number(item.rate),
                f"{item.gst_rate:.0f}%",
                format_number(item.total)
            ])

        # Column widths
        col_widths = [8*mm, 58*mm, 18*mm, 15*mm, 15*mm, 22*mm, 15*mm, 25*mm]
        table = Table(data, colWidths=col_widths)

        # Styling
        style_commands = [
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['text_white']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),

            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),    # #
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),      # Description
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),    # HSN
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),    # Numbers
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 2.5*mm),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2.5*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),

            # Borders
            ('BOX', (0, 0), (-1, -1), 1, COLORS['primary']),
            ('LINEBELOW', (0, 0), (-1, 0), 2, COLORS['primary']),
            ('INNERGRID', (0, 1), (-1, -1), 0.5, COLORS['table_border']),
        ]

        # Alternating rows
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), COLORS['table_row_alt']))

        table.setStyle(TableStyle(style_commands))
        elements.append(table)

        return elements

    def _calculate_hsn_summary(self, items):
        """Calculate HSN-wise summary"""
        hsn_data = {}
        for item in items:
            hsn = item.hsn_code or 'NA'
            if hsn not in hsn_data:
                hsn_data[hsn] = {'taxable': 0, 'cgst': 0, 'sgst': 0, 'igst': 0, 'gst_rate': item.gst_rate or 0}
            hsn_data[hsn]['taxable'] += item.taxable_value or 0
            hsn_data[hsn]['cgst'] += item.cgst or 0
            hsn_data[hsn]['sgst'] += item.sgst or 0
            hsn_data[hsn]['igst'] += item.igst or 0
        return hsn_data

    def _build_modern_hsn_summary(self, hsn_summary):
        """Build modern HSN summary table"""
        elements = []
        elements.append(Spacer(1, 4*mm))
        elements.append(Paragraph("<font color='#1a237e'><b>TAX SUMMARY (HSN-WISE)</b></font>", self.styles['SectionHeader']))

        has_igst = any(v['igst'] > 0 for v in hsn_summary.values())

        if has_igst:
            headers = ['HSN Code', 'Taxable Value', 'IGST Rate', 'IGST Amount']
            col_widths = [40*mm, 50*mm, 35*mm, 45*mm]
        else:
            headers = ['HSN Code', 'Taxable Value', 'CGST', 'SGST', 'Total Tax']
            col_widths = [35*mm, 45*mm, 30*mm, 30*mm, 35*mm]

        data = [headers]
        total_taxable = total_cgst = total_sgst = total_igst = 0

        for hsn, values in hsn_summary.items():
            total_taxable += values['taxable']
            if has_igst:
                total_igst += values['igst']
                data.append([hsn, format_number(values['taxable']), f"{values['gst_rate']:.0f}%", format_number(values['igst'])])
            else:
                total_cgst += values['cgst']
                total_sgst += values['sgst']
                data.append([hsn, format_number(values['taxable']), format_number(values['cgst']),
                            format_number(values['sgst']), format_number(values['cgst'] + values['sgst'])])

        # Totals
        if has_igst:
            data.append(['TOTAL', format_number(total_taxable), '', format_number(total_igst)])
        else:
            data.append(['TOTAL', format_number(total_taxable), format_number(total_cgst),
                        format_number(total_sgst), format_number(total_cgst + total_sgst)])

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary_light']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['text_white']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, COLORS['table_border']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['bg_card']),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(table)

        return elements

    def _build_premium_totals(self, invoice):
        """Build premium totals section"""
        elements = []
        elements.append(Spacer(1, 4*mm))

        # Build totals rows
        totals_data = []

        totals_data.append([Paragraph("Subtotal", self.styles['PartyDetails']),
                          Paragraph(f"<b>{format_currency(invoice.subtotal)}</b>", self.styles['PartyDetails'])])

        if invoice.cgst_total and invoice.cgst_total > 0:
            totals_data.append([Paragraph("CGST", self.styles['PartyDetails']),
                              Paragraph(format_currency(invoice.cgst_total), self.styles['PartyDetails'])])
            totals_data.append([Paragraph("SGST", self.styles['PartyDetails']),
                              Paragraph(format_currency(invoice.sgst_total), self.styles['PartyDetails'])])

        if invoice.igst_total and invoice.igst_total > 0:
            totals_data.append([Paragraph("IGST", self.styles['PartyDetails']),
                              Paragraph(format_currency(invoice.igst_total), self.styles['PartyDetails'])])

        if invoice.discount and invoice.discount > 0:
            totals_data.append([Paragraph("Discount", self.styles['PartyDetails']),
                              Paragraph(f"<font color='#d50000'>- {format_currency(invoice.discount)}</font>", self.styles['PartyDetails'])])

        # Grand Total - Special Row
        grand_total_row = [
            Paragraph("<font color='white'><b>GRAND TOTAL</b></font>", self.styles['PartyDetails']),
            Paragraph(f"<font color='white' size='14'><b>{format_currency(invoice.grand_total)}</b></font>", self.styles['PartyDetails'])
        ]

        totals_table = Table(totals_data, colWidths=[40*mm, 45*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_card']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
        ]))

        # Grand total table
        grand_table = Table([grand_total_row], colWidths=[40*mm, 45*mm])
        grand_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['primary']),
            ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))

        # Combine totals
        combined_data = [[totals_table], [grand_table]]
        combined_table = Table(combined_data, colWidths=[85*mm])
        combined_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        # Right-align the totals
        wrapper = Table([['', combined_table]], colWidths=[self.content_width - 90*mm, 90*mm])
        wrapper.setStyle(TableStyle([('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
        elements.append(wrapper)

        return elements

    def _build_eway_bill_section(self, invoice):
        """Build e-Way bill section"""
        elements = []
        elements.append(Spacer(1, 4*mm))

        eway_data = [
            [Paragraph("<b>E-WAY BILL DETAILS</b>", self.styles['SectionHeader']), '', '', ''],
            [
                Paragraph(f"<b>E-Way Bill No:</b> {invoice.eway_bill_number}", self.styles['PartyDetails']),
                Paragraph(f"<b>Vehicle:</b> {getattr(invoice, 'vehicle_number', '-')}", self.styles['PartyDetails']),
                Paragraph(f"<b>Mode:</b> {getattr(invoice, 'transport_mode', 'Road')}", self.styles['PartyDetails']),
                Paragraph(f"<b>Distance:</b> {getattr(invoice, 'transport_distance', 0)} km", self.styles['PartyDetails'])
            ]
        ]

        eway_table = Table(eway_data, colWidths=[self.content_width/4]*4)
        eway_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_light']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
            ('LINEBELOW', (0, 0), (-1, 0), 2, COLORS['accent']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))
        elements.append(eway_table)

        return elements

    def _build_modern_bank_details(self, company):
        """Build modern bank details section"""
        elements = []
        elements.append(Spacer(1, 5*mm))

        bank_content = [
            [Paragraph("<font color='#1a237e'><b>BANK DETAILS FOR PAYMENT</b></font>", self.styles['BankHeader']), ''],
        ]

        if company.bank_name:
            bank_content.append([Paragraph(f"<b>Bank Name:</b>", self.styles['BankDetails']),
                               Paragraph(company.bank_name, self.styles['BankDetails'])])
        if company.bank_account:
            bank_content.append([Paragraph(f"<b>Account No:</b>", self.styles['BankDetails']),
                               Paragraph(company.bank_account, self.styles['BankDetails'])])
        if company.bank_ifsc:
            bank_content.append([Paragraph(f"<b>IFSC Code:</b>", self.styles['BankDetails']),
                               Paragraph(company.bank_ifsc, self.styles['BankDetails'])])

        bank_table = Table(bank_content, colWidths=[30*mm, 70*mm])
        bank_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (-1, 0)),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_card']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
            ('LINEBELOW', (0, 0), (-1, 0), 2, COLORS['primary']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(bank_table)

        return elements

    def _build_premium_footer(self, company):
        """Build premium footer"""
        elements = []
        elements.append(Spacer(1, 8*mm))

        # Terms and Signature in two columns
        terms_text = company.invoice_terms if company and company.invoice_terms else \
            "1. Goods once sold will not be taken back.\n2. Subject to local jurisdiction.\n3. E&OE"

        terms_para = Paragraph(f"<b>Terms & Conditions:</b><br/><font size='8'>{terms_text}</font>", self.styles['Footer'])

        # Signature
        company_name = company.name if company else 'Company Name'
        sig_content = [
            [''],
            [Paragraph(f"For <b>{company_name}</b>", self.styles['PartyDetails'])],
            [Spacer(1, 15*mm)],
            [Paragraph("_____________________", self.styles['FooterCenter'])],
            [Paragraph("Authorized Signatory", self.styles['FooterCenter'])]
        ]
        sig_table = Table(sig_content, colWidths=[60*mm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ]))

        footer_table = Table([[terms_para, sig_table]], colWidths=[115*mm, 70*mm])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),
        ]))
        elements.append(footer_table)

        # Thank you
        elements.append(Spacer(1, 5*mm))
        elements.append(HRFlowable(width="100%", thickness=1, color=COLORS['primary']))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(
            "<font color='#1a237e'><b>Thank you for your business!</b></font>",
            self.styles['FooterCenter']
        ))
        elements.append(Paragraph(
            "<font size='7' color='#9e9e9e'>This is a computer-generated invoice and does not require a physical signature.</font>",
            self.styles['FooterCenter']
        ))

        return elements

    # ============ COMPACT INVOICE METHODS ============

    def _build_compact_header(self, company, doc_type, doc, is_cancelled=False):
        """Build compact header"""
        elements = []

        # Get document details
        if hasattr(doc, 'invoice_number'):
            doc_number = doc.invoice_number
            doc_date = doc.invoice_date
        elif hasattr(doc, 'quotation_number'):
            doc_number = doc.quotation_number
            doc_date = doc.quotation_date
        elif hasattr(doc, 'credit_note_number'):
            doc_number = doc.credit_note_number
            doc_date = doc.credit_note_date
        else:
            doc_number = 'N/A'
            doc_date = date.today()

        # Company Name & Details (Left)
        company_name = company.name if company else 'Company Name'
        left_content = []
        left_content.append([Paragraph(f"<font color='#1a237e' size='18'><b>{company_name}</b></font>", self.styles['CompanyName'])])

        if company:
            if company.address:
                left_content.append([Paragraph(f"{company.address}", self.styles['CompanyDetails'])])
            contact_parts = []
            if company.phone:
                contact_parts.append(f"Ph: {company.phone}")
            if company.email:
                contact_parts.append(f"{company.email}")
            if contact_parts:
                left_content.append([Paragraph(' | '.join(contact_parts), self.styles['CompanyDetails'])])
            if company.gstin:
                left_content.append([Paragraph(f"<b>GSTIN:</b> {company.gstin}", self.styles['CompanyDetails'])])

        left_table = Table(left_content, colWidths=[110*mm])
        left_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.3*mm),
        ]))

        # Invoice Info (Right)
        payment_status = getattr(doc, 'payment_status', 'UNPAID')
        status_color = '#00c853' if payment_status == 'PAID' else '#ff6d00' if payment_status == 'PARTIAL' else '#d50000'

        right_content = [
            [Paragraph(f"<font size='12'><b>{doc_number}</b></font>", self.styles['InvoiceNumber'])],
            [Paragraph(f"{doc_date.strftime('%d %b %Y') if doc_date else ''}", self.styles['InvoiceInfo'])],
            [Paragraph(f"<font color='{status_color}'><b>{payment_status}</b></font>", self.styles['InvoiceInfo'])]
        ]
        right_table = Table(right_content, colWidths=[60*mm])
        right_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_card']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))

        header_table = Table([[left_table, right_table]], colWidths=[125*mm, 65*mm])
        elements.append(header_table)
        elements.append(Spacer(1, 2*mm))

        # Document Title Bar
        title_bg = COLORS['danger'] if is_cancelled else COLORS['primary']
        title_text = f"{doc_type} - CANCELLED" if is_cancelled else doc_type

        title_table = Table([[Paragraph(title_text, self.styles['DocTitle'])]], colWidths=[self.content_width])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), title_bg),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(title_table)
        elements.append(Spacer(1, 3*mm))

        return elements

    def _build_compact_billing_parties(self, company, invoice):
        """Build compact billing parties - two columns"""
        elements = []

        customer = getattr(invoice, 'customer', None)
        customer_name = invoice.customer_name or 'Walk-in Customer'

        # FROM Section
        from_lines = []
        if company:
            from_lines.append(Paragraph(f"<b>{company.name}</b>", self.styles['PartyName']))
            if company.address:
                from_lines.append(Paragraph(company.address, self.styles['PartyDetails']))
            if company.gstin:
                from_lines.append(Paragraph(f"GSTIN: {company.gstin}", self.styles['PartyDetails']))
            if company.phone:
                from_lines.append(Paragraph(f"Ph: {company.phone}", self.styles['PartyDetails']))

        from_content = [[Paragraph("<font color='#1a237e'><b>FROM</b></font>", self.styles['SectionHeader'])]]
        from_content.extend([[p] for p in from_lines])

        from_table = Table(from_content, colWidths=[90*mm])
        from_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_white']),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, COLORS['primary']),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))

        # TO Section
        to_lines = []
        to_lines.append(Paragraph(f"<b>{customer_name}</b>", self.styles['PartyName']))
        if customer:
            if customer.address:
                to_lines.append(Paragraph(customer.address, self.styles['PartyDetails']))
            if customer.gstin:
                to_lines.append(Paragraph(f"GSTIN: {customer.gstin}", self.styles['PartyDetails']))
            if hasattr(customer, 'phone') and customer.phone:
                to_lines.append(Paragraph(f"Ph: {customer.phone}", self.styles['PartyDetails']))

        to_content = [[Paragraph("<font color='#1a237e'><b>TO</b></font>", self.styles['SectionHeader'])]]
        to_content.extend([[p] for p in to_lines])

        to_table = Table(to_content, colWidths=[90*mm])
        to_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_card']),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['primary']),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, COLORS['primary']),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))

        parties_table = Table([[from_table, to_table]], colWidths=[95*mm, 95*mm])
        elements.append(parties_table)
        elements.append(Spacer(1, 3*mm))

        return elements

    def _build_compact_totals(self, invoice):
        """Build compact totals with amount in words"""
        elements = []
        elements.append(Spacer(1, 2*mm))

        # Build totals rows
        totals_data = []
        totals_data.append(['Subtotal', format_currency(invoice.subtotal)])

        if invoice.cgst_total and invoice.cgst_total > 0:
            totals_data.append(['CGST', format_currency(invoice.cgst_total)])
            totals_data.append(['SGST', format_currency(invoice.sgst_total)])
        if invoice.igst_total and invoice.igst_total > 0:
            totals_data.append(['IGST', format_currency(invoice.igst_total)])
        if invoice.discount and invoice.discount > 0:
            totals_data.append(['Discount', f"- {format_currency(invoice.discount)}"])

        totals_table = Table(totals_data, colWidths=[30*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['bg_light']),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))

        # Grand Total
        grand_table = Table([['GRAND TOTAL', format_currency(invoice.grand_total)]], colWidths=[30*mm, 40*mm])
        grand_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, -1), COLORS['text_white']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))

        # Combine
        combined = Table([[totals_table], [grand_table]], colWidths=[70*mm])
        combined.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        # Amount in words (left side)
        words_para = Paragraph(f"<b>In Words:</b> {number_to_words_indian(invoice.grand_total)}", self.styles['PartyDetails'])

        # Layout: words on left, totals on right
        layout = Table([[words_para, combined]], colWidths=[115*mm, 75*mm])
        layout.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(layout)

        return elements

    def _build_compact_hsn_summary(self, hsn_summary):
        """Build compact HSN summary"""
        elements = []
        elements.append(Spacer(1, 2*mm))

        has_igst = any(v['igst'] > 0 for v in hsn_summary.values())

        if has_igst:
            headers = ['HSN', 'Taxable', 'Rate', 'IGST']
            col_widths = [25*mm, 35*mm, 20*mm, 30*mm]
        else:
            headers = ['HSN', 'Taxable', 'CGST', 'SGST']
            col_widths = [25*mm, 35*mm, 25*mm, 25*mm]

        data = [headers]
        for hsn, values in hsn_summary.items():
            if has_igst:
                data.append([hsn, format_number(values['taxable']), f"{values['gst_rate']:.0f}%", format_number(values['igst'])])
            else:
                data.append([hsn, format_number(values['taxable']), format_number(values['cgst']), format_number(values['sgst'])])

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary_light']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['text_white']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, COLORS['table_border']),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
        ]))

        # Wrap with label
        hsn_label = Paragraph("<font size='8' color='#616161'><b>HSN Summary</b></font>", self.styles['PartyDetails'])
        wrapper = Table([[hsn_label], [table]], colWidths=[110*mm])

        elements.append(wrapper)
        return elements

    def _build_compact_footer_section(self, company, invoice):
        """Build compact footer with bank details and payment info"""
        elements = []
        elements.append(Spacer(1, 3*mm))

        # Payment Mode
        payment_mode = getattr(invoice, 'payment_mode', 'CASH')
        payment_labels = {'CASH': 'Cash', 'CARD': 'Card', 'UPI': 'UPI', 'BANK': 'Bank Transfer', 'CREDIT': 'Credit'}
        payment_text = payment_labels.get(payment_mode, payment_mode)

        # Left: Bank Details | Right: Payment & Signature
        left_content = []

        if company and (company.bank_name or company.bank_account):
            left_content.append([Paragraph("<b>Bank Details</b>", self.styles['BankHeader'])])
            if company.bank_name:
                left_content.append([Paragraph(f"Bank: {company.bank_name}", self.styles['BankDetails'])])
            if company.bank_account:
                left_content.append([Paragraph(f"A/C: {company.bank_account}", self.styles['BankDetails'])])
            if company.bank_ifsc:
                left_content.append([Paragraph(f"IFSC: {company.bank_ifsc}", self.styles['BankDetails'])])

        # Terms
        terms_text = company.invoice_terms if company and company.invoice_terms else "E&OE. Goods once sold will not be taken back."
        left_content.append([Spacer(1, 2*mm)])
        left_content.append([Paragraph(f"<font size='7' color='#616161'>{terms_text}</font>", self.styles['Footer'])])

        left_table = Table(left_content, colWidths=[100*mm])
        left_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))

        # Right: Payment + Signature
        company_name = company.name if company else 'Company'
        right_content = [
            [Paragraph(f"<b>Payment Mode:</b> {payment_text}", self.styles['PartyDetails'])],
            [Spacer(1, 8*mm)],
            [Paragraph(f"For <b>{company_name}</b>", self.styles['PartyDetails'])],
            [Spacer(1, 10*mm)],
            [Paragraph("____________________", self.styles['FooterCenter'])],
            [Paragraph("Authorized Signatory", self.styles['FooterCenter'])]
        ]
        right_table = Table(right_content, colWidths=[70*mm])
        right_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        footer_table = Table([[left_table, right_table]], colWidths=[115*mm, 75*mm])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('VALIGN', (1, 0), (1, 0), 'TOP'),
        ]))
        elements.append(footer_table)

        # Thank you line
        elements.append(Spacer(1, 3*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=COLORS['border']))
        elements.append(Spacer(1, 1*mm))
        elements.append(Paragraph(
            "<font size='8' color='#1a237e'><b>Thank you for your business!</b></font>",
            self.styles['FooterCenter']
        ))

        return elements

    # ============ QUOTATION & CREDIT NOTE METHODS ============

    def generate_quotation_pdf(self, quotation, company, items):
        """Generate quotation PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=self.margin, rightMargin=self.margin,
                               topMargin=self.margin, bottomMargin=self.margin)
        elements = []

        elements.extend(self._build_premium_header(company, 'QUOTATION', quotation))

        if quotation.validity_date:
            elements.append(Paragraph(f"<b>Valid Until:</b> {quotation.validity_date.strftime('%d %b %Y')}", self.styles['PartyDetails']))
            elements.append(Spacer(1, 2*mm))

        # Create a mock invoice object for billing parties
        class MockInvoice:
            def __init__(self, q):
                self.customer_name = q.customer_name
                self.customer = q.customer
        elements.extend(self._build_modern_billing_parties(company, MockInvoice(quotation)))
        elements.extend(self._build_modern_items_table(items))
        elements.extend(self._build_quotation_totals(quotation))

        if quotation.notes:
            elements.append(Spacer(1, 3*mm))
            elements.append(Paragraph(f"<b>Notes:</b> {quotation.notes}", self.styles['PartyDetails']))
        if quotation.terms_conditions:
            elements.append(Spacer(1, 2*mm))
            elements.append(Paragraph(f"<b>Terms:</b> {quotation.terms_conditions}", self.styles['PartyDetails']))

        elements.extend(self._build_premium_footer(company))
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_credit_note_pdf(self, credit_note, company, items):
        """Generate credit note PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=self.margin, rightMargin=self.margin,
                               topMargin=self.margin, bottomMargin=self.margin)
        elements = []

        elements.extend(self._build_premium_header(company, 'CREDIT NOTE', credit_note))

        if credit_note.original_invoice_number:
            elements.append(Paragraph(f"<b>Against Invoice:</b> {credit_note.original_invoice_number}", self.styles['PartyDetails']))

        reason_labels = {'RETURN': 'Product Return', 'DAMAGE': 'Damaged Goods',
                        'PRICE_ADJUSTMENT': 'Price Adjustment', 'OTHER': 'Other'}
        elements.append(Paragraph(f"<b>Reason:</b> {reason_labels.get(credit_note.reason, credit_note.reason)}", self.styles['PartyDetails']))
        if credit_note.reason_details:
            elements.append(Paragraph(f"<b>Details:</b> {credit_note.reason_details}", self.styles['PartyDetails']))
        elements.append(Spacer(1, 2*mm))

        customer = credit_note.original_invoice.customer if credit_note.original_invoice else None

        class MockInvoice:
            def __init__(self, cn, cust):
                self.customer_name = cn.customer_name
                self.customer = cust
        elements.extend(self._build_modern_billing_parties(company, MockInvoice(credit_note, customer)))
        elements.extend(self._build_modern_items_table(items))
        elements.extend(self._build_credit_note_totals(credit_note))
        elements.extend(self._build_premium_footer(company))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_quotation_totals(self, quotation):
        """Build quotation totals"""
        elements = []
        elements.append(Spacer(1, 4*mm))

        totals_data = []
        totals_data.append(['Subtotal', format_currency(quotation.subtotal)])
        if quotation.cgst_total and quotation.cgst_total > 0:
            totals_data.append(['CGST', format_currency(quotation.cgst_total)])
            totals_data.append(['SGST', format_currency(quotation.sgst_total)])
        if quotation.igst_total and quotation.igst_total > 0:
            totals_data.append(['IGST', format_currency(quotation.igst_total)])
        if quotation.discount and quotation.discount > 0:
            totals_data.append(['Discount', f"- {format_currency(quotation.discount)}"])
        totals_data.append(['TOTAL', format_currency(quotation.grand_total)])

        totals_table = Table(totals_data, colWidths=[35*mm, 45*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['warning']),
            ('TEXTCOLOR', (0, -1), (-1, -1), COLORS['text_white']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))

        wrapper = Table([['', totals_table]], colWidths=[self.content_width - 85*mm, 85*mm])
        wrapper.setStyle(TableStyle([('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
        elements.append(wrapper)
        return elements

    def _build_credit_note_totals(self, credit_note):
        """Build credit note totals"""
        elements = []
        elements.append(Spacer(1, 4*mm))

        totals_data = []
        totals_data.append(['Subtotal', format_currency(credit_note.subtotal)])
        if credit_note.cgst_total and credit_note.cgst_total > 0:
            totals_data.append(['CGST', format_currency(credit_note.cgst_total)])
            totals_data.append(['SGST', format_currency(credit_note.sgst_total)])
        if credit_note.igst_total and credit_note.igst_total > 0:
            totals_data.append(['IGST', format_currency(credit_note.igst_total)])
        totals_data.append(['CREDIT AMOUNT', format_currency(credit_note.grand_total)])

        totals_table = Table(totals_data, colWidths=[40*mm, 45*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['danger']),
            ('TEXTCOLOR', (0, -1), (-1, -1), COLORS['text_white']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))

        wrapper = Table([['', totals_table]], colWidths=[self.content_width - 90*mm, 90*mm])
        wrapper.setStyle(TableStyle([('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
        elements.append(wrapper)
        return elements


# Create singleton instance
pdf_generator = PDFGenerator()

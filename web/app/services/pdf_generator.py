"""Professional PDF Generator for GST Invoices, Quotations, and Credit Notes"""
from io import BytesIO
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


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

# Medical/Healthcare Professional Color Scheme
COLORS = {
    'primary': colors.HexColor('#008B8B'),        # Dark Cyan/Teal - main headers
    'primary_dark': colors.HexColor('#006666'),   # Darker Teal - accent
    'primary_light': colors.HexColor('#20B2AA'),  # Light Sea Green
    'header_bg': colors.HexColor('#008080'),      # Teal - table headers
    'success': colors.HexColor('#2E8B57'),        # Sea Green - success
    'warning': colors.HexColor('#FF9800'),        # Orange - quotations
    'danger': colors.HexColor('#c0392b'),         # Red - credit notes
    'light_bg': colors.HexColor('#E0F7FA'),       # Very Light Cyan background
    'lighter_bg': colors.HexColor('#F0FFFF'),     # Azure - alternating rows
    'border': colors.HexColor('#B2DFDB'),         # Light Teal Border
    'border_dark': colors.HexColor('#80CBC4'),    # Medium Teal Border
    'text_dark': colors.HexColor('#004D40'),      # Dark Teal Text
    'text_muted': colors.HexColor('#607D8B'),     # Blue Grey - secondary text
    'white': colors.white,
    'total_bg': colors.HexColor('#E0F2F1'),       # Teal Light Background for totals
}


def get_state_name(state_code):
    """Get state name from code"""
    return STATE_CODES.get(str(state_code), f"State {state_code}")


def format_currency(amount):
    """Format amount as Indian currency with proper formatting"""
    if amount is None:
        amount = 0
    return f"Rs. {amount:,.2f}"


def format_inr(amount):
    """Format with Rupee symbol"""
    if amount is None:
        amount = 0
    return f"₹ {amount:,.2f}"


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
    """Professional PDF Generator for GST-compliant documents"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.page_width, self.page_height = A4
        self.margin = 12 * mm
        self.content_width = self.page_width - (2 * self.margin)

    def _setup_styles(self):
        """Set up custom paragraph styles"""
        # Company Name - Large and Bold
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            alignment=TA_LEFT,
            spaceAfter=1*mm,
            leading=22
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

        # Document Title (TAX INVOICE, etc.)
        self.styles.add(ParagraphStyle(
            name='DocTitle',
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=COLORS['white'],
            alignment=TA_CENTER,
            leading=18
        ))

        # Section Header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            spaceBefore=2*mm,
            spaceAfter=1*mm
        ))

        # Customer/Party Details
        self.styles.add(ParagraphStyle(
            name='PartyName',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=COLORS['text_dark'],
            leading=14
        ))

        self.styles.add(ParagraphStyle(
            name='PartyDetails',
            fontSize=9,
            fontName='Helvetica',
            textColor=COLORS['text_dark'],
            leading=12
        ))

        # Invoice Info (right side)
        self.styles.add(ParagraphStyle(
            name='InvoiceInfo',
            fontSize=9,
            fontName='Helvetica',
            textColor=COLORS['text_dark'],
            alignment=TA_RIGHT,
            leading=12
        ))

        self.styles.add(ParagraphStyle(
            name='InvoiceInfoBold',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=COLORS['text_dark'],
            alignment=TA_RIGHT,
            leading=14
        ))

        # Amount in Words
        self.styles.add(ParagraphStyle(
            name='AmountWords',
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=COLORS['text_dark'],
            alignment=TA_LEFT,
            leading=12
        ))

        # Footer text
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
            textColor=COLORS['text_muted'],
            alignment=TA_CENTER,
            leading=10
        ))

        # Bank Details
        self.styles.add(ParagraphStyle(
            name='BankHeader',
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            leading=12
        ))

        self.styles.add(ParagraphStyle(
            name='BankDetails',
            fontSize=8,
            fontName='Helvetica',
            textColor=COLORS['text_dark'],
            leading=11
        ))

    def generate_invoice_pdf(self, invoice, company, items):
        """Generate professional invoice PDF"""
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

        # Determine invoice type (TAX INVOICE or BILL OF SUPPLY)
        invoice_type = getattr(invoice, 'invoice_type', 'TAX_INVOICE')
        doc_title = 'BILL OF SUPPLY' if invoice_type == 'BILL_OF_SUPPLY' else 'TAX INVOICE'

        # 1. Header Section (Company + Invoice Info)
        elements.extend(self._build_professional_header(company, doc_title, invoice))

        # 2. GST Compliance Info Section
        elements.extend(self._build_gst_compliance_info(invoice, company))

        # 3. Bill From / Bill To Section
        elements.extend(self._build_billing_parties(company, invoice.customer_name, invoice.customer))

        # 4. Items Table
        elements.extend(self._build_professional_items_table(items))

        # 5. HSN Summary (GST Compliance)
        hsn_summary = self._calculate_hsn_summary(items)
        if hsn_summary:
            elements.extend(self._build_hsn_summary_table(hsn_summary))

        # 6. Totals Section
        elements.extend(self._build_professional_totals(invoice))

        # 7. Amount in Words
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(
            f"<b>Amount in Words:</b> {number_to_words_indian(invoice.grand_total)}",
            self.styles['AmountWords']
        ))

        # 8. E-Way Bill Info (if generated)
        eway_number = getattr(invoice, 'eway_bill_number', '')
        if eway_number:
            elements.extend(self._build_eway_bill_info(invoice))

        # 9. Bank Details (if available)
        if company and (company.bank_name or company.bank_account):
            elements.extend(self._build_bank_details(company))

        # 10. Footer Section
        elements.extend(self._build_professional_footer(company))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_gst_compliance_info(self, invoice, company):
        """Build GST compliance information section"""
        elements = []

        # Get values with defaults
        supply_type = getattr(invoice, 'supply_type', 'B2C')
        is_rcm = getattr(invoice, 'is_reverse_charge', False)
        buyer_state_code = getattr(invoice, 'buyer_state_code', '')
        seller_state_code = company.state_code if company else '32'

        # Determine Place of Supply
        pos_code = buyer_state_code or seller_state_code
        pos_name = get_state_name(pos_code)

        # Build info items
        info_items = [
            f"<b>Supply Type:</b> {supply_type}",
            f"<b>Place of Supply:</b> {pos_name} ({pos_code})",
            f"<b>Reverse Charge:</b> {'Yes' if is_rcm else 'No'}",
        ]

        # Customer GSTIN if B2B
        customer_gstin = getattr(invoice, 'customer_gstin', '')
        if customer_gstin:
            info_items.append(f"<b>Customer GSTIN:</b> {customer_gstin}")

        # Create a compact info bar
        info_text = " | ".join(info_items)
        info_para = Paragraph(info_text, self.styles['CompanyDetails'])

        info_table = Table([[info_para]], colWidths=[self.content_width])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['lighter_bg']),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 2*mm))

        return elements

    def _build_eway_bill_info(self, invoice):
        """Build e-Way bill information section"""
        elements = []

        eway_number = getattr(invoice, 'eway_bill_number', '')
        vehicle_number = getattr(invoice, 'vehicle_number', '')
        transport_mode = getattr(invoice, 'transport_mode', 'Road')
        transport_distance = getattr(invoice, 'transport_distance', 0)

        elements.append(Spacer(1, 2*mm))

        # E-Way Bill header
        eway_header = Paragraph("<b>E-Way Bill Details</b>", self.styles['SectionHeader'])

        # E-Way Bill details
        eway_items = [f"<b>E-Way Bill No:</b> {eway_number}"]
        if vehicle_number:
            eway_items.append(f"<b>Vehicle:</b> {vehicle_number}")
        if transport_mode:
            eway_items.append(f"<b>Mode:</b> {transport_mode}")
        if transport_distance:
            eway_items.append(f"<b>Distance:</b> {transport_distance} km")

        eway_text = " | ".join(eway_items)
        eway_para = Paragraph(eway_text, self.styles['CompanyDetails'])

        eway_table = Table([[eway_header], [eway_para]], colWidths=[self.content_width])
        eway_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
            ('BACKGROUND', (0, 1), (-1, -1), COLORS['light_bg']),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))

        elements.append(eway_table)

        return elements

    def generate_quotation_pdf(self, quotation, company, items):
        """Generate professional quotation PDF"""
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

        # Header
        elements.extend(self._build_professional_header(company, 'QUOTATION', quotation, is_quotation=True))

        # Validity info
        if quotation.validity_date:
            elements.append(Paragraph(
                f"<b>Valid Until:</b> {quotation.validity_date.strftime('%d %b %Y')}",
                self.styles['PartyDetails']
            ))
            elements.append(Spacer(1, 2*mm))

        # Billing parties
        elements.extend(self._build_billing_parties(company, quotation.customer_name, quotation.customer))

        # Items table
        elements.extend(self._build_professional_items_table(items))

        # Totals
        elements.extend(self._build_quotation_totals(quotation))

        # Notes and terms
        if quotation.notes:
            elements.append(Spacer(1, 3*mm))
            elements.append(Paragraph("<b>Notes:</b>", self.styles['SectionHeader']))
            elements.append(Paragraph(quotation.notes, self.styles['PartyDetails']))

        if quotation.terms_conditions:
            elements.append(Spacer(1, 3*mm))
            elements.append(Paragraph("<b>Terms & Conditions:</b>", self.styles['SectionHeader']))
            elements.append(Paragraph(quotation.terms_conditions, self.styles['PartyDetails']))

        # Footer
        elements.extend(self._build_professional_footer(company))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_credit_note_pdf(self, credit_note, company, items):
        """Generate professional credit note PDF"""
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

        # Header
        elements.extend(self._build_professional_header(company, 'CREDIT NOTE', credit_note, is_credit_note=True))

        # Original invoice reference
        if credit_note.original_invoice_number:
            elements.append(Paragraph(
                f"<b>Against Invoice:</b> {credit_note.original_invoice_number}",
                self.styles['PartyDetails']
            ))

        # Reason
        reason_labels = {'RETURN': 'Product Return', 'DAMAGE': 'Damaged Goods',
                        'PRICE_ADJUSTMENT': 'Price Adjustment', 'OTHER': 'Other'}
        reason_text = reason_labels.get(credit_note.reason, credit_note.reason)
        elements.append(Paragraph(f"<b>Reason:</b> {reason_text}", self.styles['PartyDetails']))
        if credit_note.reason_details:
            elements.append(Paragraph(f"<b>Details:</b> {credit_note.reason_details}", self.styles['PartyDetails']))
        elements.append(Spacer(1, 2*mm))

        # Customer details
        customer = credit_note.original_invoice.customer if credit_note.original_invoice else None
        elements.extend(self._build_billing_parties(company, credit_note.customer_name, customer))

        # Items table
        elements.extend(self._build_professional_items_table(items))

        # Totals
        elements.extend(self._build_credit_note_totals(credit_note))

        # Footer
        elements.extend(self._build_professional_footer(company))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_professional_header(self, company, doc_type, doc, is_quotation=False, is_credit_note=False):
        """Build professional header with company info and document details"""
        elements = []

        # Determine document number and date
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

        # Build company info (left side)
        company_name = company.name if company else 'Company Name'
        company_lines = [Paragraph(company_name, self.styles['CompanyName'])]

        if company:
            if company.address:
                company_lines.append(Paragraph(company.address, self.styles['CompanyDetails']))

            contact_parts = []
            if company.phone:
                contact_parts.append(f"Ph: {company.phone}")
            if company.email:
                contact_parts.append(f"Email: {company.email}")
            if contact_parts:
                company_lines.append(Paragraph(' | '.join(contact_parts), self.styles['CompanyDetails']))

            if company.gstin:
                company_lines.append(Paragraph(f"<b>GSTIN:</b> {company.gstin}", self.styles['CompanyDetails']))
            if company.pan:
                company_lines.append(Paragraph(f"<b>PAN:</b> {company.pan}", self.styles['CompanyDetails']))

        # Build invoice info (right side)
        invoice_lines = []
        invoice_lines.append(Paragraph(f"<b>{doc_type}</b>", self.styles['InvoiceInfoBold']))
        invoice_lines.append(Paragraph(f"<b>No:</b> {doc_number}", self.styles['InvoiceInfo']))
        invoice_lines.append(Paragraph(f"<b>Date:</b> {doc_date.strftime('%d %b %Y') if doc_date else ''}", self.styles['InvoiceInfo']))

        # Create two-column header table
        left_content = []
        for line in company_lines:
            left_content.append([line])
        left_table = Table(left_content, colWidths=[110*mm])
        left_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        right_content = []
        for line in invoice_lines:
            right_content.append([line])
        right_table = Table(right_content, colWidths=[60*mm])
        right_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['light_bg']),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
        ]))

        header_table = Table([[left_table, right_table]], colWidths=[120*mm, 66*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 3*mm))

        # Document title bar
        if is_credit_note:
            title_bg = COLORS['danger']
        elif is_quotation:
            title_bg = COLORS['warning']
        else:
            title_bg = COLORS['primary']

        title_data = [[Paragraph(doc_type, self.styles['DocTitle'])]]
        title_table = Table(title_data, colWidths=[self.content_width])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), title_bg),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5*mm),
        ]))
        elements.append(title_table)
        elements.append(Spacer(1, 4*mm))

        return elements

    def _build_billing_parties(self, company, customer_name, customer):
        """Build Bill From / Bill To section in two columns"""
        elements = []

        # Bill From content
        from_content = [Paragraph("<b>BILL FROM</b>", self.styles['SectionHeader'])]
        if company:
            from_content.append(Paragraph(company.name or 'Company Name', self.styles['PartyName']))
            if company.address:
                from_content.append(Paragraph(company.address, self.styles['PartyDetails']))
            if company.gstin:
                from_content.append(Paragraph(f"GSTIN: {company.gstin}", self.styles['PartyDetails']))
            state_name = get_state_name(company.state_code) if company.state_code else ''
            if state_name:
                from_content.append(Paragraph(f"State: {state_name} ({company.state_code})", self.styles['PartyDetails']))

        # Bill To content
        to_content = [Paragraph("<b>BILL TO</b>", self.styles['SectionHeader'])]
        to_content.append(Paragraph(customer_name or 'Walk-in Customer', self.styles['PartyName']))
        if customer:
            if customer.address:
                to_content.append(Paragraph(customer.address, self.styles['PartyDetails']))
            if customer.gstin:
                to_content.append(Paragraph(f"GSTIN: {customer.gstin}", self.styles['PartyDetails']))
            if customer.state_code:
                state_name = get_state_name(customer.state_code)
                to_content.append(Paragraph(f"State: {state_name} ({customer.state_code})", self.styles['PartyDetails']))
            if hasattr(customer, 'phone') and customer.phone:
                to_content.append(Paragraph(f"Phone: {customer.phone}", self.styles['PartyDetails']))

        # Create tables for each column
        from_table_data = [[item] for item in from_content]
        from_table = Table(from_table_data, colWidths=[88*mm])
        from_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['light_bg']),
        ]))

        to_table_data = [[item] for item in to_content]
        to_table = Table(to_table_data, colWidths=[88*mm])
        to_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
        ]))

        # Combine into two-column layout
        parties_table = Table([[from_table, to_table]], colWidths=[93*mm, 93*mm])
        parties_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 4*mm))

        return elements

    def _build_professional_items_table(self, items):
        """Build professional items table with modern styling"""
        elements = []

        # Table headers
        headers = ['#', 'Description', 'HSN', 'Qty', 'Rate', 'Taxable', 'GST%', 'Tax', 'Total']
        data = [headers]

        # Table rows
        for i, item in enumerate(items, 1):
            tax = (item.cgst or 0) + (item.sgst or 0) + (item.igst or 0)
            product_name = (item.product_name or '')[:35]  # Truncate long names
            data.append([
                str(i),
                product_name,
                item.hsn_code or '-',
                f"{item.qty:.2f}",
                f"{item.rate:,.2f}",
                f"{item.taxable_value:,.2f}",
                f"{item.gst_rate:.0f}%",
                f"{tax:,.2f}",
                f"{item.total:,.2f}"
            ])

        # Column widths
        col_widths = [8*mm, 48*mm, 16*mm, 16*mm, 22*mm, 24*mm, 14*mm, 18*mm, 22*mm]
        table = Table(data, colWidths=col_widths)

        # Table styling
        style_commands = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),

            # Body rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # # column
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Description
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # HSN
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),  # Numbers right-aligned
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),

            # Borders
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border_dark']),
            ('LINEBELOW', (0, 0), (-1, 0), 1, COLORS['primary']),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, COLORS['border']),

            # Padding
            ('TOPPADDING', (0, 0), (-1, 0), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
            ('TOPPADDING', (0, 1), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1.5*mm),
        ]

        # Alternating row colors
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), COLORS['lighter_bg']))

        table.setStyle(TableStyle(style_commands))
        elements.append(table)

        return elements

    def _calculate_hsn_summary(self, items):
        """Calculate HSN-wise tax summary"""
        hsn_data = {}
        for item in items:
            hsn = item.hsn_code or 'NA'
            if hsn not in hsn_data:
                hsn_data[hsn] = {
                    'taxable': 0,
                    'cgst': 0,
                    'sgst': 0,
                    'igst': 0,
                    'gst_rate': item.gst_rate or 0
                }
            hsn_data[hsn]['taxable'] += item.taxable_value or 0
            hsn_data[hsn]['cgst'] += item.cgst or 0
            hsn_data[hsn]['sgst'] += item.sgst or 0
            hsn_data[hsn]['igst'] += item.igst or 0
        return hsn_data

    def _build_hsn_summary_table(self, hsn_summary):
        """Build HSN-wise tax summary table (GST compliance)"""
        elements = []
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("<b>HSN-wise Tax Summary</b>", self.styles['SectionHeader']))

        # Determine if we have IGST or CGST/SGST
        has_igst = any(v['igst'] > 0 for v in hsn_summary.values())

        if has_igst:
            headers = ['HSN Code', 'Taxable Value', 'IGST Rate', 'IGST Amount']
            col_widths = [35*mm, 50*mm, 30*mm, 40*mm]
        else:
            headers = ['HSN Code', 'Taxable Value', 'CGST', 'SGST', 'Total Tax']
            col_widths = [30*mm, 40*mm, 30*mm, 30*mm, 30*mm]

        data = [headers]

        total_taxable = 0
        total_cgst = 0
        total_sgst = 0
        total_igst = 0

        for hsn, values in hsn_summary.items():
            total_taxable += values['taxable']
            if has_igst:
                total_igst += values['igst']
                data.append([
                    hsn,
                    f"{values['taxable']:,.2f}",
                    f"{values['gst_rate']:.0f}%",
                    f"{values['igst']:,.2f}"
                ])
            else:
                total_cgst += values['cgst']
                total_sgst += values['sgst']
                total_tax = values['cgst'] + values['sgst']
                data.append([
                    hsn,
                    f"{values['taxable']:,.2f}",
                    f"{values['cgst']:,.2f}",
                    f"{values['sgst']:,.2f}",
                    f"{total_tax:,.2f}"
                ])

        # Totals row
        if has_igst:
            data.append(['Total', f"{total_taxable:,.2f}", '', f"{total_igst:,.2f}"])
        else:
            data.append(['Total', f"{total_taxable:,.2f}", f"{total_cgst:,.2f}",
                        f"{total_sgst:,.2f}", f"{total_cgst + total_sgst:,.2f}"])

        table = Table(data, colWidths=col_widths)
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary_light']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['light_bg']),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]
        table.setStyle(TableStyle(style_commands))
        elements.append(table)

        return elements

    def _build_professional_totals(self, invoice):
        """Build professional totals section"""
        elements = []
        elements.append(Spacer(1, 3*mm))

        # Build totals data
        totals_data = []
        totals_data.append(['Subtotal', format_currency(invoice.subtotal)])

        if invoice.cgst_total and invoice.cgst_total > 0:
            totals_data.append(['CGST', format_currency(invoice.cgst_total)])
            totals_data.append(['SGST', format_currency(invoice.sgst_total)])

        if invoice.igst_total and invoice.igst_total > 0:
            totals_data.append(['IGST', format_currency(invoice.igst_total)])

        if invoice.discount and invoice.discount > 0:
            totals_data.append(['Discount', f"- {format_currency(invoice.discount)}"])

        totals_data.append(['GRAND TOTAL', format_currency(invoice.grand_total)])

        # Create totals table (right-aligned)
        totals_table = Table(totals_data, colWidths=[30*mm, 40*mm])

        style_commands = [
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
            # Grand total row
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['primary']),
            ('TEXTCOLOR', (0, -1), (-1, -1), COLORS['white']),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
        ]
        totals_table.setStyle(TableStyle(style_commands))

        # Wrapper to right-align the totals table
        wrapper_data = [['', totals_table]]
        wrapper_table = Table(wrapper_data, colWidths=[self.content_width - 75*mm, 75*mm])
        wrapper_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(wrapper_table)

        return elements

    def _build_quotation_totals(self, quotation):
        """Build quotation totals section"""
        elements = []
        elements.append(Spacer(1, 3*mm))

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

        totals_table = Table(totals_data, colWidths=[30*mm, 40*mm])
        style_commands = [
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['warning']),
            ('TEXTCOLOR', (0, -1), (-1, -1), COLORS['white']),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
        ]
        totals_table.setStyle(TableStyle(style_commands))

        wrapper_data = [['', totals_table]]
        wrapper_table = Table(wrapper_data, colWidths=[self.content_width - 75*mm, 75*mm])
        wrapper_table.setStyle(TableStyle([('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
        elements.append(wrapper_table)

        return elements

    def _build_credit_note_totals(self, credit_note):
        """Build credit note totals section"""
        elements = []
        elements.append(Spacer(1, 3*mm))

        totals_data = []
        totals_data.append(['Subtotal', format_currency(credit_note.subtotal)])

        if credit_note.cgst_total and credit_note.cgst_total > 0:
            totals_data.append(['CGST', format_currency(credit_note.cgst_total)])
            totals_data.append(['SGST', format_currency(credit_note.sgst_total)])

        if credit_note.igst_total and credit_note.igst_total > 0:
            totals_data.append(['IGST', format_currency(credit_note.igst_total)])

        totals_data.append(['CREDIT AMOUNT', format_currency(credit_note.grand_total)])

        totals_table = Table(totals_data, colWidths=[35*mm, 40*mm])
        style_commands = [
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['danger']),
            ('TEXTCOLOR', (0, -1), (-1, -1), COLORS['white']),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
        ]
        totals_table.setStyle(TableStyle(style_commands))

        wrapper_data = [['', totals_table]]
        wrapper_table = Table(wrapper_data, colWidths=[self.content_width - 80*mm, 80*mm])
        wrapper_table.setStyle(TableStyle([('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
        elements.append(wrapper_table)

        return elements

    def _build_bank_details(self, company):
        """Build bank details section"""
        elements = []
        elements.append(Spacer(1, 4*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=COLORS['border']))
        elements.append(Spacer(1, 2*mm))

        bank_content = []
        bank_content.append(Paragraph("<b>Bank Details for Payment</b>", self.styles['BankHeader']))

        if company.bank_name:
            bank_content.append(Paragraph(f"Bank: {company.bank_name}", self.styles['BankDetails']))
        if company.bank_account:
            bank_content.append(Paragraph(f"Account No: {company.bank_account}", self.styles['BankDetails']))
        if company.bank_ifsc:
            bank_content.append(Paragraph(f"IFSC Code: {company.bank_ifsc}", self.styles['BankDetails']))

        bank_table_data = [[item] for item in bank_content]
        bank_table = Table(bank_table_data, colWidths=[90*mm])
        bank_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['light_bg']),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
        ]))
        elements.append(bank_table)

        return elements

    def _build_professional_footer(self, company):
        """Build professional footer with terms and signature"""
        elements = []
        elements.append(Spacer(1, 8*mm))

        # Terms & Conditions and Signature in two columns
        terms_text = ""
        if company and company.invoice_terms:
            terms_text = company.invoice_terms
        else:
            terms_text = "1. Goods once sold will not be taken back.\n2. Subject to local jurisdiction."

        terms_content = Paragraph(
            f"<b>Terms & Conditions:</b><br/>{terms_text}",
            self.styles['Footer']
        )

        # Signature area
        company_name = company.name if company else 'Company Name'
        sig_content = []
        sig_content.append([''])
        sig_content.append([Paragraph(f"For <b>{company_name}</b>", self.styles['PartyDetails'])])
        sig_content.append([''])
        sig_content.append([Paragraph("Authorized Signatory", self.styles['Footer'])])

        sig_table = Table(sig_content, colWidths=[60*mm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, 0), 15*mm),
            ('LINEABOVE', (0, -1), (-1, -1), 0.5, COLORS['text_dark']),
        ]))

        footer_table = Table([[terms_content, sig_table]], colWidths=[110*mm, 70*mm])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),
        ]))
        elements.append(footer_table)

        # Thank you message
        elements.append(Spacer(1, 5*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=COLORS['border']))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("Thank you for choosing us for your healthcare needs!", self.styles['FooterCenter']))

        return elements


# Create singleton instance
pdf_generator = PDFGenerator()

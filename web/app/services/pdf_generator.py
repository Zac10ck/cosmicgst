"""PDF Generator for invoices, quotations, and credit notes using ReportLab"""
from io import BytesIO
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# State code to name mapping
STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra & Nagar Haveli", "27": "Maharashtra",
    "29": "Karnataka", "30": "Goa", "31": "Lakshadweep",
    "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry",
    "35": "Andaman & Nicobar", "36": "Telangana", "37": "Andhra Pradesh",
    "38": "Ladakh"
}

# Color scheme
COLORS = {
    'primary': colors.HexColor('#1a5276'),
    'secondary': colors.HexColor('#2980b9'),
    'light_bg': colors.HexColor('#f8f9fa'),
    'border': colors.HexColor('#dee2e6'),
    'text_dark': colors.HexColor('#2c3e50'),
    'header_bg': colors.HexColor('#1a5276'),
    'row_alt': colors.HexColor('#f1f4f8'),
}


def get_state_name(state_code):
    """Get state name from code"""
    return STATE_CODES.get(state_code, f"State {state_code}")


def format_currency(amount):
    """Format amount as Indian currency"""
    return f"Rs. {amount:,.2f}"


def number_to_words_indian(num):
    """Convert number to words (Indian system)"""
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
            'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
            'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

    if num == 0:
        return 'Zero'

    def words(n):
        if n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + ('' if n % 10 == 0 else ' ' + ones[n % 10])
        elif n < 1000:
            return ones[n // 100] + ' Hundred' + ('' if n % 100 == 0 else ' ' + words(n % 100))
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
    """Generate PDF documents for invoices, quotations, and credit notes"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.page_width, self.page_height = A4
        self.margin = 15 * mm

    def _setup_styles(self):
        """Set up custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            alignment=TA_LEFT,
            spaceAfter=2*mm
        ))

        self.styles.add(ParagraphStyle(
            name='CompanyDetails',
            fontSize=9,
            textColor=COLORS['text_dark'],
            alignment=TA_LEFT,
            spaceAfter=1*mm
        ))

        self.styles.add(ParagraphStyle(
            name='DocTitle',
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_CENTER,
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            spaceBefore=3*mm,
            spaceAfter=2*mm
        ))

        self.styles.add(ParagraphStyle(
            name='CustomerDetails',
            fontSize=9,
            textColor=COLORS['text_dark'],
            alignment=TA_LEFT,
        ))

        self.styles.add(ParagraphStyle(
            name='AmountWords',
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=COLORS['text_dark'],
            alignment=TA_LEFT,
        ))

    def generate_invoice_pdf(self, invoice, company, items):
        """Generate invoice PDF"""
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

        # Header with company info
        elements.extend(self._build_header(company, 'TAX INVOICE', invoice.invoice_number, invoice.invoice_date))

        # Customer details
        elements.extend(self._build_customer_section(invoice.customer_name, invoice.customer))

        # Items table
        elements.extend(self._build_items_table(items))

        # Totals
        elements.extend(self._build_totals(invoice))

        # Amount in words
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(
            f"<b>Amount in Words:</b> {number_to_words_indian(invoice.grand_total)}",
            self.styles['AmountWords']
        ))

        # Footer
        elements.extend(self._build_footer(company))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_quotation_pdf(self, quotation, company, items):
        """Generate quotation PDF"""
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
        elements.extend(self._build_header(company, 'QUOTATION', quotation.quotation_number, quotation.quotation_date))

        # Validity info
        elements.append(Paragraph(
            f"<b>Valid Until:</b> {quotation.validity_date.strftime('%d %b %Y') if quotation.validity_date else 'N/A'}",
            self.styles['CustomerDetails']
        ))
        elements.append(Spacer(1, 2*mm))

        # Customer details
        elements.extend(self._build_customer_section(quotation.customer_name, quotation.customer))

        # Items table
        elements.extend(self._build_items_table(items))

        # Totals
        elements.extend(self._build_quotation_totals(quotation))

        # Notes and terms
        if quotation.notes:
            elements.append(Spacer(1, 3*mm))
            elements.append(Paragraph("<b>Notes:</b>", self.styles['SectionHeader']))
            elements.append(Paragraph(quotation.notes, self.styles['CustomerDetails']))

        if quotation.terms_conditions:
            elements.append(Spacer(1, 3*mm))
            elements.append(Paragraph("<b>Terms & Conditions:</b>", self.styles['SectionHeader']))
            elements.append(Paragraph(quotation.terms_conditions, self.styles['CustomerDetails']))

        # Footer
        elements.extend(self._build_footer(company))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_credit_note_pdf(self, credit_note, company, items):
        """Generate credit note PDF"""
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
        elements.extend(self._build_header(company, 'CREDIT NOTE', credit_note.credit_note_number, credit_note.credit_note_date))

        # Original invoice reference
        if credit_note.original_invoice_number:
            elements.append(Paragraph(
                f"<b>Against Invoice:</b> {credit_note.original_invoice_number}",
                self.styles['CustomerDetails']
            ))
            elements.append(Spacer(1, 2*mm))

        # Reason
        reason_labels = dict(CreditNote.REASONS) if hasattr(credit_note, 'REASONS') else {}
        reason_text = reason_labels.get(credit_note.reason, credit_note.reason)
        elements.append(Paragraph(f"<b>Reason:</b> {reason_text}", self.styles['CustomerDetails']))
        if credit_note.reason_details:
            elements.append(Paragraph(f"<b>Details:</b> {credit_note.reason_details}", self.styles['CustomerDetails']))
        elements.append(Spacer(1, 2*mm))

        # Customer details
        elements.extend(self._build_customer_section(credit_note.customer_name, credit_note.original_invoice.customer if credit_note.original_invoice else None))

        # Items table
        elements.extend(self._build_items_table(items))

        # Totals
        elements.extend(self._build_credit_note_totals(credit_note))

        # Footer
        elements.extend(self._build_footer(company))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_header(self, company, doc_type, doc_number, doc_date):
        """Build document header"""
        elements = []

        # Company name
        company_name = company.name if company else 'Company Name'
        elements.append(Paragraph(company_name, self.styles['CompanyName']))

        # Company details
        if company:
            if company.address:
                elements.append(Paragraph(company.address, self.styles['CompanyDetails']))
            details = []
            if company.phone:
                details.append(f"Phone: {company.phone}")
            if company.email:
                details.append(f"Email: {company.email}")
            if details:
                elements.append(Paragraph(' | '.join(details), self.styles['CompanyDetails']))
            if company.gstin:
                elements.append(Paragraph(f"GSTIN: {company.gstin}", self.styles['CompanyDetails']))

        elements.append(Spacer(1, 3*mm))

        # Document title bar
        title_data = [[
            Paragraph(doc_type, self.styles['DocTitle']),
            Paragraph(f"No: {doc_number}", self.styles['DocTitle']),
            Paragraph(f"Date: {doc_date.strftime('%d %b %Y') if doc_date else ''}", self.styles['DocTitle'])
        ]]
        title_table = Table(title_data, colWidths=[80*mm, 50*mm, 50*mm])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['header_bg']),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))
        elements.append(title_table)
        elements.append(Spacer(1, 3*mm))

        return elements

    def _build_customer_section(self, customer_name, customer):
        """Build customer details section"""
        elements = []
        elements.append(Paragraph("<b>Bill To:</b>", self.styles['SectionHeader']))
        elements.append(Paragraph(customer_name or 'Walk-in Customer', self.styles['CustomerDetails']))

        if customer:
            if customer.address:
                elements.append(Paragraph(customer.address, self.styles['CustomerDetails']))
            if customer.gstin:
                elements.append(Paragraph(f"GSTIN: {customer.gstin}", self.styles['CustomerDetails']))
            if customer.state_code:
                elements.append(Paragraph(f"State: {get_state_name(customer.state_code)} ({customer.state_code})", self.styles['CustomerDetails']))

        elements.append(Spacer(1, 3*mm))
        return elements

    def _build_items_table(self, items):
        """Build items table"""
        elements = []

        # Table headers
        headers = ['#', 'Product', 'HSN', 'Qty', 'Rate', 'Taxable', 'GST%', 'Tax', 'Total']
        data = [headers]

        # Table rows
        for i, item in enumerate(items, 1):
            tax = item.cgst + item.sgst + item.igst
            data.append([
                str(i),
                item.product_name[:30],
                item.hsn_code or '-',
                f"{item.qty:.2f}",
                f"{item.rate:.2f}",
                f"{item.taxable_value:.2f}",
                f"{item.gst_rate:.0f}%",
                f"{tax:.2f}",
                f"{item.total:.2f}"
            ])

        col_widths = [8*mm, 45*mm, 18*mm, 18*mm, 20*mm, 22*mm, 15*mm, 18*mm, 22*mm]
        table = Table(data, colWidths=col_widths)

        style = TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['header_bg']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Body
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ])

        # Alternate row colors
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), COLORS['row_alt'])

        table.setStyle(style)
        elements.append(table)

        return elements

    def _build_totals(self, invoice):
        """Build invoice totals section"""
        elements = []
        elements.append(Spacer(1, 2*mm))

        totals_data = [
            ['Subtotal:', format_currency(invoice.subtotal)],
        ]
        if invoice.cgst_total > 0:
            totals_data.append(['CGST:', format_currency(invoice.cgst_total)])
            totals_data.append(['SGST:', format_currency(invoice.sgst_total)])
        if invoice.igst_total > 0:
            totals_data.append(['IGST:', format_currency(invoice.igst_total)])
        if invoice.discount > 0:
            totals_data.append(['Discount:', f"- {format_currency(invoice.discount)}"])
        totals_data.append(['Grand Total:', format_currency(invoice.grand_total)])

        totals_table = Table(totals_data, colWidths=[140*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['light_bg']),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
        ]))
        elements.append(totals_table)

        return elements

    def _build_quotation_totals(self, quotation):
        """Build quotation totals section"""
        elements = []
        elements.append(Spacer(1, 2*mm))

        totals_data = [
            ['Subtotal:', format_currency(quotation.subtotal)],
        ]
        if quotation.cgst_total > 0:
            totals_data.append(['CGST:', format_currency(quotation.cgst_total)])
            totals_data.append(['SGST:', format_currency(quotation.sgst_total)])
        if quotation.igst_total > 0:
            totals_data.append(['IGST:', format_currency(quotation.igst_total)])
        if quotation.discount > 0:
            totals_data.append(['Discount:', f"- {format_currency(quotation.discount)}"])
        totals_data.append(['Grand Total:', format_currency(quotation.grand_total)])

        totals_table = Table(totals_data, colWidths=[140*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['light_bg']),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
        ]))
        elements.append(totals_table)

        return elements

    def _build_credit_note_totals(self, credit_note):
        """Build credit note totals section"""
        elements = []
        elements.append(Spacer(1, 2*mm))

        totals_data = [
            ['Subtotal:', format_currency(credit_note.subtotal)],
        ]
        if credit_note.cgst_total > 0:
            totals_data.append(['CGST:', format_currency(credit_note.cgst_total)])
            totals_data.append(['SGST:', format_currency(credit_note.sgst_total)])
        if credit_note.igst_total > 0:
            totals_data.append(['IGST:', format_currency(credit_note.igst_total)])
        totals_data.append(['Credit Amount:', format_currency(credit_note.grand_total)])

        totals_table = Table(totals_data, colWidths=[140*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['light_bg']),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
        ]))
        elements.append(totals_table)

        return elements

    def _build_footer(self, company):
        """Build document footer"""
        elements = []
        elements.append(Spacer(1, 10*mm))

        # Signature line
        sig_data = [['', 'Authorized Signatory']]
        sig_table = Table(sig_data, colWidths=[120*mm, 60*mm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (1, 0), (1, 0), 15*mm),
            ('LINEABOVE', (1, 0), (1, 0), 0.5, COLORS['border']),
        ]))
        elements.append(sig_table)

        return elements


# Create singleton instance
pdf_generator = PDFGenerator()

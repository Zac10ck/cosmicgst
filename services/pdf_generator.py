"""Professional PDF invoice generator using ReportLab"""
from io import BytesIO
from datetime import date
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF

from database.models import Invoice, Company, CreditNote, Quotation
from utils.formatters import format_currency, number_to_words_indian, format_date


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
    "26": "Dadra & Nagar Haveli and Daman & Diu", "27": "Maharashtra",
    "28": "Andhra Pradesh (Old)", "29": "Karnataka", "30": "Goa",
    "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman & Nicobar", "36": "Telangana",
    "37": "Andhra Pradesh", "38": "Ladakh"
}


def get_state_name(state_code: str) -> str:
    """Get state name from code"""
    return STATE_CODES.get(state_code, f"State {state_code}")


# Professional color scheme
COLORS = {
    'primary': colors.HexColor('#1a5276'),      # Dark blue
    'secondary': colors.HexColor('#2980b9'),    # Medium blue
    'accent': colors.HexColor('#27ae60'),       # Green
    'light_bg': colors.HexColor('#f8f9fa'),     # Light gray
    'border': colors.HexColor('#dee2e6'),       # Border gray
    'text_dark': colors.HexColor('#2c3e50'),    # Dark text
    'text_light': colors.HexColor('#7f8c8d'),   # Light text
    'header_bg': colors.HexColor('#1a5276'),    # Header background
    'row_alt': colors.HexColor('#f1f4f8'),      # Alternate row
    'total_bg': colors.HexColor('#e8f4f8'),     # Total row background
}


class PDFGenerator:
    """Generate professional A4 PDF invoices"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.page_width, self.page_height = A4
        self.margin = 15 * mm

    def _setup_styles(self):
        """Set up custom paragraph styles"""
        # Company name - large and bold
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            alignment=TA_LEFT,
            spaceAfter=1*mm
        ))

        # Company details
        self.styles.add(ParagraphStyle(
            name='CompanyDetails',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=COLORS['text_dark'],
            alignment=TA_LEFT,
            spaceAfter=0.5*mm
        ))

        # Invoice title
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceBefore=0,
            spaceAfter=0
        ))

        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=COLORS['primary'],
            spaceBefore=3*mm,
            spaceAfter=2*mm
        ))

        # Normal text
        self.styles.add(ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=COLORS['text_dark']
        ))

        # Amount in words
        self.styles.add(ParagraphStyle(
            name='AmountWords',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=COLORS['text_dark']
        ))

        # Footer text
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=COLORS['text_light'],
            alignment=TA_CENTER
        ))

        # Bank details
        self.styles.add(ParagraphStyle(
            name='BankDetails',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=COLORS['text_dark']
        ))

    def generate_invoice_pdf(self, invoice: Invoice, output_path: str = None) -> bytes:
        """
        Generate professional PDF for an invoice

        Args:
            invoice: Invoice object with items
            output_path: Optional path to save PDF file

        Returns:
            PDF bytes if no output_path, else saves to file
        """
        # Get company details
        company = Company.get()
        if not company:
            company = Company(
                name="Your Shop Name",
                address="Address Line, City, State - PIN",
                gstin="",
                phone=""
            )

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )

        elements = []
        content_width = self.page_width - 2 * self.margin

        # ==================== HEADER SECTION ====================
        elements.extend(self._build_header(company, content_width))

        # ==================== INVOICE TITLE BAR ====================
        elements.append(Spacer(1, 5*mm))
        elements.extend(self._build_title_bar(content_width))

        # ==================== INVOICE INFO & CUSTOMER ====================
        elements.append(Spacer(1, 5*mm))
        elements.extend(self._build_invoice_info(invoice, company, content_width))

        # ==================== ITEMS TABLE ====================
        elements.append(Spacer(1, 5*mm))
        elements.extend(self._build_items_table(invoice, content_width))

        # ==================== HSN SUMMARY TABLE ====================
        elements.append(Spacer(1, 5*mm))
        elements.extend(self._build_hsn_summary(invoice, content_width))

        # ==================== TOTALS SECTION ====================
        elements.append(Spacer(1, 3*mm))
        elements.extend(self._build_totals_section(invoice, content_width))

        # ==================== AMOUNT IN WORDS ====================
        elements.append(Spacer(1, 3*mm))
        amount_words = number_to_words_indian(invoice.grand_total)
        elements.append(Paragraph(
            f"<b>Amount in Words:</b> {amount_words}",
            self.styles['AmountWords']
        ))

        # ==================== PAYMENT & BANK DETAILS ====================
        elements.append(Spacer(1, 5*mm))
        elements.extend(self._build_payment_section(invoice, company, content_width))

        # ==================== FOOTER ====================
        elements.append(Spacer(1, 10*mm))
        elements.extend(self._build_footer(company, content_width))

        # Build PDF
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes

    def _build_header(self, company: Company, content_width: float) -> list:
        """Build header section with logo and company details"""
        elements = []

        # Check for logo
        logo_path = company.logo_path if company.logo_path and Path(company.logo_path).exists() else None

        if logo_path:
            # Header with logo on left, company info on right
            try:
                logo = Image(logo_path, width=25*mm, height=25*mm)
                logo.hAlign = 'LEFT'

                company_info = [
                    Paragraph(company.name, self.styles['CompanyName']),
                    Paragraph(company.address, self.styles['CompanyDetails']),
                ]
                if company.gstin:
                    company_info.append(Paragraph(f"<b>GSTIN:</b> {company.gstin}", self.styles['CompanyDetails']))
                if company.phone:
                    company_info.append(Paragraph(f"<b>Phone:</b> {company.phone}", self.styles['CompanyDetails']))
                if company.email:
                    company_info.append(Paragraph(f"<b>Email:</b> {company.email}", self.styles['CompanyDetails']))

                header_table = Table(
                    [[logo, company_info]],
                    colWidths=[30*mm, content_width - 30*mm]
                )
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                elements.append(header_table)
            except Exception:
                # Fallback if logo fails to load
                elements.extend(self._build_text_header(company))
        else:
            # Text-only header
            elements.extend(self._build_text_header(company))

        return elements

    def _build_text_header(self, company: Company) -> list:
        """Build text-only header"""
        elements = []
        elements.append(Paragraph(company.name, self.styles['CompanyName']))
        elements.append(Paragraph(company.address, self.styles['CompanyDetails']))

        if company.gstin:
            elements.append(Paragraph(f"<b>GSTIN:</b> {company.gstin}", self.styles['CompanyDetails']))

        details_parts = []
        if company.phone:
            details_parts.append(f"<b>Phone:</b> {company.phone}")
        if company.email:
            details_parts.append(f"<b>Email:</b> {company.email}")
        if details_parts:
            elements.append(Paragraph(" | ".join(details_parts), self.styles['CompanyDetails']))

        return elements

    def _build_title_bar(self, content_width: float) -> list:
        """Build TAX INVOICE title bar"""
        elements = []

        # Create a colored title bar
        title_table = Table(
            [[Paragraph("TAX INVOICE", self.styles['InvoiceTitle'])]],
            colWidths=[content_width]
        )
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['header_bg']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(title_table)

        return elements

    def _build_invoice_info(self, invoice: Invoice, company: Company, content_width: float) -> list:
        """Build invoice info and customer details section"""
        elements = []

        # Invoice details on left, Customer on right
        inv_date = invoice.invoice_date
        if isinstance(inv_date, str):
            inv_date = date.fromisoformat(inv_date)

        # Determine Place of Supply (buyer state)
        buyer_state_code = "32"  # Default Kerala
        if invoice.customer_id:
            from database.models import Customer
            customer = Customer.get_by_id(invoice.customer_id)
            if customer:
                buyer_state_code = customer.state_code or "32"

        place_of_supply = f"{get_state_name(buyer_state_code)} ({buyer_state_code})"
        is_inter_state = company.state_code != buyer_state_code

        # Left column - Invoice details
        invoice_details = [
            [Paragraph("<b>Invoice No:</b>", self.styles['NormalText']),
             Paragraph(invoice.invoice_number, self.styles['NormalText'])],
            [Paragraph("<b>Date:</b>", self.styles['NormalText']),
             Paragraph(format_date(inv_date), self.styles['NormalText'])],
            [Paragraph("<b>Place of Supply:</b>", self.styles['NormalText']),
             Paragraph(place_of_supply, self.styles['NormalText'])],
            [Paragraph("<b>Reverse Charge:</b>", self.styles['NormalText']),
             Paragraph("No", self.styles['NormalText'])],
        ]

        left_table = Table(invoice_details, colWidths=[32*mm, 50*mm])
        left_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        # Right column - Customer details (in a box)
        customer_content = []
        customer_content.append(Paragraph("<b>Bill To:</b>", self.styles['NormalText']))
        customer_content.append(Paragraph(invoice.customer_name or "Cash Customer", self.styles['NormalText']))

        # Get customer details if available
        if invoice.customer_id:
            customer = Customer.get_by_id(invoice.customer_id)
            if customer:
                if customer.address:
                    customer_content.append(Paragraph(customer.address, self.styles['NormalText']))
                if customer.gstin:
                    customer_content.append(Paragraph(f"<b>GSTIN:</b> {customer.gstin}", self.styles['NormalText']))
                customer_content.append(Paragraph(f"<b>State:</b> {get_state_name(customer.state_code)} ({customer.state_code})", self.styles['NormalText']))
                if customer.phone:
                    customer_content.append(Paragraph(f"<b>Phone:</b> {customer.phone}", self.styles['NormalText']))

        right_table = Table([[customer_content]], colWidths=[content_width/2 - 10*mm])
        right_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['light_bg']),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

        # Combine left and right
        main_table = Table(
            [[left_table, right_table]],
            colWidths=[content_width/2 + 10*mm, content_width/2 - 10*mm]
        )
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(main_table)

        return elements

    def _build_items_table(self, invoice: Invoice, content_width: float) -> list:
        """Build professional items table"""
        elements = []

        # Column headers (with Batch# column)
        headers = ['#', 'Description', 'Batch#', 'HSN', 'Qty', 'Rate', 'GST%', 'CGST', 'SGST', 'Amount']

        # Column widths (total should equal content_width)
        col_widths = [8*mm, 38*mm, 16*mm, 16*mm, 14*mm, 20*mm, 12*mm, 16*mm, 16*mm, 24*mm]

        # Build header row
        header_row = [Paragraph(f"<b>{h}</b>", ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_CENTER
        )) for h in headers]

        items_data = [header_row]

        # Build item rows
        for idx, item in enumerate(invoice.items, 1):
            batch_number = getattr(item, 'batch_number', '') or '-'
            row = [
                str(idx),
                item.product_name[:25],  # Truncate long names
                batch_number[:10] if len(batch_number) > 10 else batch_number,  # Truncate batch
                item.hsn_code or '-',
                f"{item.qty:.2f}".rstrip('0').rstrip('.'),
                format_currency(item.rate),
                f"{int(item.gst_rate)}%",
                format_currency(item.cgst),
                format_currency(item.sgst),
                format_currency(item.total)
            ]
            items_data.append(row)

        items_table = Table(items_data, colWidths=col_widths)

        # Professional table styling
        style_commands = [
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['header_bg']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),

            # Alignments
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),   # #
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),     # Description
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),   # Batch#
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),   # HSN
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),   # Qty
            ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),   # Rate onwards

            # Borders
            ('BOX', (0, 0), (-1, -1), 1, COLORS['primary']),
            ('LINEBELOW', (0, 0), (-1, 0), 1, COLORS['primary']),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, COLORS['border']),

            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),

            # Vertical alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Add alternating row colors
        for i in range(1, len(items_data)):
            if i % 2 == 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), COLORS['row_alt']))

        items_table.setStyle(TableStyle(style_commands))
        elements.append(items_table)

        return elements

    def _build_hsn_summary(self, invoice: Invoice, content_width: float) -> list:
        """Build HSN-wise tax summary table (GST requirement)"""
        elements = []

        # Group items by HSN code
        hsn_data = {}
        for item in invoice.items:
            hsn = item.hsn_code or "N/A"
            if hsn not in hsn_data:
                hsn_data[hsn] = {
                    'taxable': 0,
                    'cgst': 0,
                    'sgst': 0,
                    'igst': 0,
                    'gst_rate': item.gst_rate,
                    'total': 0
                }
            hsn_data[hsn]['taxable'] += item.taxable_value
            hsn_data[hsn]['cgst'] += item.cgst
            hsn_data[hsn]['sgst'] += item.sgst
            hsn_data[hsn]['igst'] += item.igst
            hsn_data[hsn]['total'] += item.total

        if not hsn_data:
            return elements

        # Section header
        elements.append(Paragraph("<b>HSN-wise Tax Summary</b>", self.styles['SectionHeader']))

        # Build table
        headers = ['HSN Code', 'Taxable Value', 'GST Rate', 'CGST', 'SGST', 'IGST', 'Total Tax']
        col_widths = [25*mm, 35*mm, 20*mm, 25*mm, 25*mm, 25*mm, 25*mm]

        header_row = [Paragraph(f"<b>{h}</b>", ParagraphStyle(
            'HSNHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_CENTER
        )) for h in headers]

        table_data = [header_row]

        totals = {'taxable': 0, 'cgst': 0, 'sgst': 0, 'igst': 0, 'total_tax': 0}

        for hsn, data in hsn_data.items():
            total_tax = data['cgst'] + data['sgst'] + data['igst']
            row = [
                hsn,
                format_currency(data['taxable']),
                f"{int(data['gst_rate'])}%",
                format_currency(data['cgst']),
                format_currency(data['sgst']),
                format_currency(data['igst']),
                format_currency(total_tax)
            ]
            table_data.append(row)
            totals['taxable'] += data['taxable']
            totals['cgst'] += data['cgst']
            totals['sgst'] += data['sgst']
            totals['igst'] += data['igst']
            totals['total_tax'] += total_tax

        # Total row
        table_data.append([
            Paragraph("<b>Total</b>", ParagraphStyle('HSNTotal', fontSize=8, fontName='Helvetica-Bold')),
            Paragraph(f"<b>{format_currency(totals['taxable'])}</b>", ParagraphStyle('HSNTotal', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
            '',
            Paragraph(f"<b>{format_currency(totals['cgst'])}</b>", ParagraphStyle('HSNTotal', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
            Paragraph(f"<b>{format_currency(totals['sgst'])}</b>", ParagraphStyle('HSNTotal', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
            Paragraph(f"<b>{format_currency(totals['igst'])}</b>", ParagraphStyle('HSNTotal', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
            Paragraph(f"<b>{format_currency(totals['total_tax'])}</b>", ParagraphStyle('HSNTotal', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        ])

        hsn_table = Table(table_data, colWidths=col_widths)
        hsn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['secondary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, COLORS['border']),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['light_bg']),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(hsn_table)

        return elements

    def _build_totals_section(self, invoice: Invoice, content_width: float) -> list:
        """Build totals section with tax breakup"""
        elements = []

        # Totals data
        totals_rows = [
            ['Subtotal (Taxable Value):', format_currency(invoice.subtotal)],
        ]

        if invoice.cgst_total > 0:
            totals_rows.append(['CGST:', format_currency(invoice.cgst_total)])
        if invoice.sgst_total > 0:
            totals_rows.append(['SGST:', format_currency(invoice.sgst_total)])
        if invoice.igst_total > 0:
            totals_rows.append(['IGST:', format_currency(invoice.igst_total)])

        if invoice.discount > 0:
            totals_rows.append(['Discount:', f"- {format_currency(invoice.discount)}"])

        # Grand total row
        totals_rows.append(['GRAND TOTAL:', format_currency(invoice.grand_total)])

        # Right-aligned totals table
        totals_table = Table(totals_rows, colWidths=[content_width - 50*mm, 50*mm])

        style_commands = [
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),

            # Grand total row styling
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['total_bg']),
            ('LINEABOVE', (0, -1), (-1, -1), 1.5, COLORS['primary']),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), COLORS['primary']),

            # Box around totals
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
        ]

        totals_table.setStyle(TableStyle(style_commands))
        elements.append(totals_table)

        return elements

    def _build_payment_section(self, invoice: Invoice, company: Company, content_width: float) -> list:
        """Build payment and bank details section"""
        elements = []

        # Horizontal line
        elements.append(HRFlowable(
            width=content_width,
            thickness=0.5,
            color=COLORS['border'],
            spaceBefore=3*mm,
            spaceAfter=3*mm
        ))

        # Bank details if available
        if company.bank_details:
            bank_box = Table(
                [[Paragraph(f"<b>Bank Details:</b><br/>{company.bank_details.replace(chr(10), '<br/>')}",
                           self.styles['BankDetails'])]],
                colWidths=[content_width/2]
            )
            bank_box.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
                ('BACKGROUND', (0, 0), (-1, -1), COLORS['light_bg']),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(bank_box)
            elements.append(Spacer(1, 5*mm))

        return elements

    def _build_footer(self, company: Company, content_width: float) -> list:
        """Build footer with terms and signature"""
        elements = []

        # Terms and signature table
        terms_text = """<b>Terms & Conditions:</b><br/>
1. Goods once sold will not be taken back or exchanged.<br/>
2. All disputes are subject to local jurisdiction.<br/>
3. E. & O.E."""

        footer_data = [
            [
                Paragraph(terms_text, ParagraphStyle(
                    'Terms',
                    parent=self.styles['Normal'],
                    fontSize=7,
                    textColor=COLORS['text_light'],
                    leading=10
                )),
                '',
                [
                    Paragraph(f"<b>For {company.name}</b>", ParagraphStyle(
                        'Signatory',
                        parent=self.styles['Normal'],
                        fontSize=9,
                        alignment=TA_CENTER,
                        textColor=COLORS['text_dark']
                    )),
                    Spacer(1, 15*mm),
                    Paragraph("Authorized Signatory", ParagraphStyle(
                        'SignatoryLabel',
                        parent=self.styles['Normal'],
                        fontSize=8,
                        alignment=TA_CENTER,
                        textColor=COLORS['text_light']
                    )),
                ]
            ],
        ]

        footer_table = Table(footer_data, colWidths=[content_width*0.5, content_width*0.1, content_width*0.4])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),
            ('LINEABOVE', (2, 0), (2, 0), 0.5, COLORS['border']),
        ]))
        elements.append(footer_table)

        # Thank you message
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph(
            "Thank you for your business!",
            ParagraphStyle(
                'ThankYou',
                parent=self.styles['Normal'],
                fontSize=10,
                fontName='Helvetica-Oblique',
                textColor=COLORS['secondary'],
                alignment=TA_CENTER
            )
        ))

        return elements

    def print_invoice(self, invoice: Invoice) -> bool:
        """
        Generate and print invoice

        Returns True if print initiated successfully
        """
        import tempfile
        import subprocess
        import platform
        import os

        try:
            # Generate PDF to temp file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                pdf_path = f.name

            self.generate_invoice_pdf(invoice, pdf_path)

            # Print based on OS
            system = platform.system()

            if system == 'Windows':
                # Try to print, if fails open the PDF instead
                try:
                    os.startfile(pdf_path, 'print')
                except Exception:
                    # Fallback: just open the PDF
                    os.startfile(pdf_path)
            elif system == 'Darwin':  # macOS
                subprocess.run(['lpr', pdf_path], check=False)
            else:  # Linux
                subprocess.run(['lpr', pdf_path], check=False)

            return True

        except Exception as e:
            print(f"Print error: {e}")
            # Try to at least open the PDF
            try:
                if platform.system() == 'Windows':
                    os.startfile(pdf_path)
            except Exception:
                pass
            raise e

    def generate_credit_note_pdf(self, credit_note: CreditNote, output_path: str = None) -> bytes:
        """
        Generate professional PDF for a credit note

        Args:
            credit_note: CreditNote object with items
            output_path: Optional path to save PDF file

        Returns:
            PDF bytes if no output_path, else saves to file
        """
        # Get company details
        company = Company.get()
        if not company:
            company = Company(
                name="Your Shop Name",
                address="Address Line, City, State - PIN",
                gstin="",
                phone=""
            )

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )

        elements = []
        content_width = self.page_width - 2 * self.margin

        # ==================== HEADER SECTION ====================
        elements.extend(self._build_header(company, content_width))

        # ==================== CREDIT NOTE TITLE BAR ====================
        elements.append(Spacer(1, 5*mm))
        title_table = Table(
            [[Paragraph("CREDIT NOTE", self.styles['InvoiceTitle'])]],
            colWidths=[content_width]
        )
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#c0392b')),  # Red for credit note
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(title_table)

        # ==================== CREDIT NOTE INFO ====================
        elements.append(Spacer(1, 5*mm))
        elements.extend(self._build_credit_note_info(credit_note, company, content_width))

        # ==================== ITEMS TABLE ====================
        elements.append(Spacer(1, 5*mm))
        elements.extend(self._build_credit_note_items_table(credit_note, content_width))

        # ==================== TOTALS SECTION ====================
        elements.append(Spacer(1, 3*mm))
        elements.extend(self._build_credit_note_totals(credit_note, content_width))

        # ==================== AMOUNT IN WORDS ====================
        elements.append(Spacer(1, 3*mm))
        amount_words = number_to_words_indian(credit_note.grand_total)
        elements.append(Paragraph(
            f"<b>Credit Amount in Words:</b> {amount_words}",
            self.styles['AmountWords']
        ))

        # ==================== FOOTER ====================
        elements.append(Spacer(1, 10*mm))
        elements.extend(self._build_footer(company, content_width))

        # Build PDF
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes

    def _build_credit_note_info(self, credit_note: CreditNote, company: Company, content_width: float) -> list:
        """Build credit note info section"""
        elements = []

        cn_date = credit_note.credit_note_date
        if isinstance(cn_date, str):
            cn_date = date.fromisoformat(cn_date)

        # Left column - Credit Note details
        info_details = [
            [Paragraph("<b>Credit Note No:</b>", self.styles['NormalText']),
             Paragraph(credit_note.credit_note_number, self.styles['NormalText'])],
            [Paragraph("<b>Date:</b>", self.styles['NormalText']),
             Paragraph(format_date(cn_date), self.styles['NormalText'])],
            [Paragraph("<b>Original Invoice:</b>", self.styles['NormalText']),
             Paragraph(credit_note.original_invoice_number or "-", self.styles['NormalText'])],
            [Paragraph("<b>Reason:</b>", self.styles['NormalText']),
             Paragraph(credit_note.reason, self.styles['NormalText'])],
        ]

        left_table = Table(info_details, colWidths=[35*mm, 50*mm])
        left_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        # Right column - Customer details
        customer_content = []
        customer_content.append(Paragraph("<b>Customer:</b>", self.styles['NormalText']))
        customer_content.append(Paragraph(credit_note.customer_name or "Cash Customer", self.styles['NormalText']))

        if credit_note.customer_id:
            from database.models import Customer
            customer = Customer.get_by_id(credit_note.customer_id)
            if customer:
                if customer.address:
                    customer_content.append(Paragraph(customer.address, self.styles['NormalText']))
                if customer.gstin:
                    customer_content.append(Paragraph(f"<b>GSTIN:</b> {customer.gstin}", self.styles['NormalText']))

        right_table = Table([[customer_content]], colWidths=[content_width/2 - 10*mm])
        right_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['light_bg']),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

        main_table = Table(
            [[left_table, right_table]],
            colWidths=[content_width/2 + 10*mm, content_width/2 - 10*mm]
        )
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(main_table)

        return elements

    def _build_credit_note_items_table(self, credit_note: CreditNote, content_width: float) -> list:
        """Build credit note items table"""
        elements = []

        headers = ['#', 'Description', 'HSN', 'Qty', 'Rate', 'GST%', 'CGST', 'SGST', 'Amount']
        col_widths = [8*mm, 45*mm, 18*mm, 15*mm, 22*mm, 12*mm, 18*mm, 18*mm, 24*mm]

        header_row = [Paragraph(f"<b>{h}</b>", ParagraphStyle(
            'TableHeader',
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_CENTER
        )) for h in headers]

        items_data = [header_row]

        for idx, item in enumerate(credit_note.items, 1):
            row = [
                str(idx),
                item.product_name[:30],
                item.hsn_code or '-',
                f"{item.qty:.2f}".rstrip('0').rstrip('.'),
                format_currency(item.rate),
                f"{int(item.gst_rate)}%",
                format_currency(item.cgst),
                format_currency(item.sgst),
                format_currency(item.total)
            ]
            items_data.append(row)

        items_table = Table(items_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#c0392b')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(items_table)

        return elements

    def _build_credit_note_totals(self, credit_note: CreditNote, content_width: float) -> list:
        """Build credit note totals section"""
        elements = []

        totals_rows = [
            ['Taxable Value:', format_currency(credit_note.subtotal)],
        ]

        if credit_note.cgst_total > 0:
            totals_rows.append(['CGST:', format_currency(credit_note.cgst_total)])
        if credit_note.sgst_total > 0:
            totals_rows.append(['SGST:', format_currency(credit_note.sgst_total)])
        if credit_note.igst_total > 0:
            totals_rows.append(['IGST:', format_currency(credit_note.igst_total)])

        totals_rows.append(['CREDIT TOTAL:', format_currency(credit_note.grand_total)])

        totals_table = Table(totals_rows, colWidths=[content_width - 50*mm, 50*mm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fadbd8')),
            ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#c0392b')),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#c0392b')),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
        ]))
        elements.append(totals_table)

        return elements

    def print_credit_note(self, credit_note: CreditNote) -> bool:
        """Generate and print credit note"""
        import tempfile
        import subprocess
        import platform

        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                pdf_path = f.name
                self.generate_credit_note_pdf(credit_note, pdf_path)

            system = platform.system()
            if system == 'Windows':
                import os
                os.startfile(pdf_path, 'print')
            elif system == 'Darwin':
                subprocess.run(['lpr', pdf_path])
            else:
                subprocess.run(['lpr', pdf_path])

            return True
        except Exception as e:
            print(f"Print error: {e}")
            return False

    # === QUOTATION PDF GENERATION ===

    def generate_quotation_pdf(self, quotation: Quotation, output_path: str = None) -> bytes:
        """
        Generate professional PDF for a quotation with orange color scheme

        Args:
            quotation: Quotation object with items
            output_path: Optional file path. If None, returns bytes.

        Returns:
            PDF as bytes if no output_path, else None
        """
        # Get company details
        company = Company.get() or Company(
            name="Your Company Name",
            address="Company Address",
            gstin=""
        )

        # Create PDF
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
        content_width = self.page_width - 2 * self.margin

        # Quotation-specific colors (orange theme)
        quotation_colors = {
            'primary': colors.HexColor('#e67e22'),      # Orange
            'secondary': colors.HexColor('#d35400'),    # Dark orange
            'header_bg': colors.HexColor('#e67e22'),    # Header background
        }

        # Build document sections
        elements.extend(self._build_quotation_header(company, content_width))
        elements.append(Spacer(1, 5*mm))
        elements.extend(self._build_quotation_title_bar(quotation, content_width, quotation_colors))
        elements.append(Spacer(1, 5*mm))
        elements.extend(self._build_quotation_info(quotation, company, content_width))
        elements.append(Spacer(1, 8*mm))
        elements.extend(self._build_quotation_items_table(quotation, content_width))
        elements.append(Spacer(1, 5*mm))
        elements.extend(self._build_quotation_totals(quotation, content_width))
        elements.append(Spacer(1, 8*mm))

        # Add notes if present
        if quotation.notes:
            elements.extend(self._build_quotation_notes(quotation, content_width))
            elements.append(Spacer(1, 5*mm))

        # Add terms if present
        if quotation.terms_conditions:
            elements.extend(self._build_quotation_terms(quotation, content_width))
            elements.append(Spacer(1, 5*mm))

        elements.extend(self._build_quotation_footer(company, content_width, quotation_colors))

        # Build PDF
        doc.build(elements)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            return None

        return pdf_bytes

    def _build_quotation_header(self, company: Company, content_width: float) -> list:
        """Build quotation header with company details"""
        # Same as invoice header
        return self._build_header(company, content_width)

    def _build_quotation_title_bar(self, quotation: Quotation, content_width: float, qcolors: dict) -> list:
        """Build QUOTATION title bar with orange color"""
        elements = []

        # Status badge
        status_color = {
            'DRAFT': colors.HexColor('#95a5a6'),
            'SENT': colors.HexColor('#3498db'),
            'ACCEPTED': colors.HexColor('#27ae60'),
            'REJECTED': colors.HexColor('#e74c3c'),
            'EXPIRED': colors.HexColor('#7f8c8d'),
            'CONVERTED': colors.HexColor('#9b59b6')
        }.get(quotation.status, colors.gray)

        # Title table with orange background
        title_data = [[
            Paragraph(f"QUOTATION", self.styles['InvoiceTitle']),
            Paragraph(f"Status: {quotation.status}", ParagraphStyle(
                'StatusBadge',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.white,
                alignment=TA_RIGHT
            ))
        ]]

        title_table = Table(title_data, colWidths=[content_width * 0.6, content_width * 0.4])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), qcolors['header_bg']),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(title_table)

        return elements

    def _build_quotation_info(self, quotation: Quotation, company: Company, content_width: float) -> list:
        """Build quotation info section with validity date"""
        elements = []

        # Left side - Quotation details
        quote_details = []
        quote_details.append(f"<b>Quotation No:</b> {quotation.quotation_number}")
        quote_details.append(f"<b>Date:</b> {format_date(quotation.quotation_date)}")
        quote_details.append(f"<b>Valid Until:</b> {format_date(quotation.validity_date)}")

        left_text = "<br/>".join(quote_details)
        left_para = Paragraph(left_text, self.styles['CompanyDetails'])

        # Right side - Customer details
        right_details = []
        right_details.append("<b>Quotation To:</b>")
        if quotation.customer_name:
            right_details.append(quotation.customer_name)

            # Get customer details
            if quotation.customer_id:
                from database.models import Customer
                customer = Customer.get_by_id(quotation.customer_id)
                if customer:
                    if customer.address:
                        right_details.append(customer.address.replace('\n', '<br/>'))
                    if customer.gstin:
                        right_details.append(f"GSTIN: {customer.gstin}")
                    if customer.phone:
                        right_details.append(f"Phone: {customer.phone}")
        else:
            right_details.append("Customer details not specified")

        right_text = "<br/>".join(right_details)
        right_para = Paragraph(right_text, self.styles['CompanyDetails'])

        # Create info table
        info_table = Table(
            [[left_para, right_para]],
            colWidths=[content_width * 0.5, content_width * 0.5]
        )
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('LINEAFTER', (0, 0), (0, -1), 0.5, COLORS['border']),
            ('BACKGROUND', (0, 0), (-1, -1), COLORS['light_bg']),
        ]))
        elements.append(info_table)

        return elements

    def _build_quotation_items_table(self, quotation: Quotation, content_width: float) -> list:
        """Build quotation items table"""
        elements = []

        # Determine if IGST or CGST/SGST
        has_igst = quotation.igst_total > 0

        # Define columns based on tax type
        if has_igst:
            headers = ['#', 'Description', 'HSN', 'Qty', 'Unit', 'Rate', 'IGST%', 'IGST', 'Total']
            col_widths = [0.05, 0.25, 0.08, 0.08, 0.08, 0.12, 0.08, 0.12, 0.14]
        else:
            headers = ['#', 'Description', 'HSN', 'Qty', 'Unit', 'Rate', 'GST%', 'CGST', 'SGST', 'Total']
            col_widths = [0.05, 0.22, 0.08, 0.07, 0.06, 0.11, 0.07, 0.1, 0.1, 0.14]

        col_widths = [w * content_width for w in col_widths]

        # Create header row
        header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_CENTER
        )
        header_row = [Paragraph(h, header_style) for h in headers]

        # Create data rows
        data = [header_row]
        cell_style = ParagraphStyle(
            'TableCell',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER
        )
        cell_style_left = ParagraphStyle(
            'TableCellLeft',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT
        )

        for idx, item in enumerate(quotation.items, 1):
            if has_igst:
                row = [
                    Paragraph(str(idx), cell_style),
                    Paragraph(item.product_name, cell_style_left),
                    Paragraph(item.hsn_code or '', cell_style),
                    Paragraph(str(item.qty), cell_style),
                    Paragraph(item.unit, cell_style),
                    Paragraph(format_currency(item.rate, ''), cell_style),
                    Paragraph(f"{item.gst_rate}%", cell_style),
                    Paragraph(format_currency(item.igst, ''), cell_style),
                    Paragraph(format_currency(item.total, ''), cell_style),
                ]
            else:
                row = [
                    Paragraph(str(idx), cell_style),
                    Paragraph(item.product_name, cell_style_left),
                    Paragraph(item.hsn_code or '', cell_style),
                    Paragraph(str(item.qty), cell_style),
                    Paragraph(item.unit, cell_style),
                    Paragraph(format_currency(item.rate, ''), cell_style),
                    Paragraph(f"{item.gst_rate}%", cell_style),
                    Paragraph(format_currency(item.cgst, ''), cell_style),
                    Paragraph(format_currency(item.sgst, ''), cell_style),
                    Paragraph(format_currency(item.total, ''), cell_style),
                ]
            data.append(row)

        # Create table
        table = Table(data, colWidths=col_widths, repeatRows=1)

        # Style the table
        table_style = [
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]

        # Alternating row colors
        for i in range(1, len(data)):
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), COLORS['row_alt']))

        table.setStyle(TableStyle(table_style))
        elements.append(table)

        return elements

    def _build_quotation_totals(self, quotation: Quotation, content_width: float) -> list:
        """Build quotation totals section"""
        elements = []

        has_igst = quotation.igst_total > 0

        totals_data = [
            ['Subtotal:', format_currency(quotation.subtotal, '')],
        ]

        if quotation.discount > 0:
            totals_data.append(['Discount:', f"- {format_currency(quotation.discount, '')}"])

        if has_igst:
            totals_data.append(['IGST:', format_currency(quotation.igst_total, '')])
        else:
            totals_data.append(['CGST:', format_currency(quotation.cgst_total, '')])
            totals_data.append(['SGST:', format_currency(quotation.sgst_total, '')])

        totals_data.append(['GRAND TOTAL:', format_currency(quotation.grand_total, '')])

        # Amount in words
        amount_words = number_to_words_indian(quotation.grand_total)

        totals_table = Table(
            totals_data,
            colWidths=[content_width * 0.35, content_width * 0.25],
            hAlign='RIGHT'
        )
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 9),
            ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#e67e22')),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#e67e22')),
            ('BOX', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('BACKGROUND', (0, -1), (-1, -1), COLORS['light_bg']),
        ]))
        elements.append(totals_table)

        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(
            f"<b>Amount in Words:</b> {amount_words}",
            self.styles['CompanyDetails']
        ))

        return elements

    def _build_quotation_notes(self, quotation: Quotation, content_width: float) -> list:
        """Build notes section"""
        elements = []

        elements.append(Paragraph("<b>Notes:</b>", self.styles['CompanyDetails']))
        elements.append(Paragraph(quotation.notes, self.styles['CompanyDetails']))

        return elements

    def _build_quotation_terms(self, quotation: Quotation, content_width: float) -> list:
        """Build terms and conditions section"""
        elements = []

        elements.append(Paragraph("<b>Terms & Conditions:</b>", self.styles['CompanyDetails']))
        elements.append(Paragraph(quotation.terms_conditions, self.styles['CompanyDetails']))

        return elements

    def _build_quotation_footer(self, company: Company, content_width: float, qcolors: dict) -> list:
        """Build quotation footer"""
        elements = []

        # Footer text
        footer_style = ParagraphStyle(
            'QuotationFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=COLORS['text_light'],
            alignment=TA_CENTER
        )

        elements.append(HRFlowable(
            width=content_width,
            thickness=0.5,
            color=COLORS['border'],
            spaceBefore=5*mm,
            spaceAfter=3*mm
        ))

        elements.append(Paragraph(
            "This is a quotation and not a tax invoice. Prices are valid until the validity date mentioned above.",
            footer_style
        ))
        elements.append(Paragraph(
            f"For {company.name}",
            ParagraphStyle(
                'SignatureLine',
                parent=self.styles['Normal'],
                fontSize=9,
                alignment=TA_RIGHT,
                spaceBefore=10*mm
            )
        ))
        elements.append(Paragraph(
            "Authorized Signatory",
            ParagraphStyle(
                'SignatureLabel',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=COLORS['text_light'],
                alignment=TA_RIGHT
            )
        ))

        return elements

    def print_quotation(self, quotation: Quotation) -> bool:
        """Generate and print quotation"""
        import tempfile
        import subprocess
        import platform

        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                pdf_path = f.name
                self.generate_quotation_pdf(quotation, pdf_path)

            system = platform.system()
            if system == 'Windows':
                import os
                os.startfile(pdf_path, 'print')
            elif system == 'Darwin':
                subprocess.run(['lpr', pdf_path])
            else:
                subprocess.run(['lpr', pdf_path])

            return True
        except Exception as e:
            print(f"Print error: {e}")
            return False

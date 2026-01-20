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

from database.models import Invoice, Company
from utils.formatters import format_currency, number_to_words_indian, format_date


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

        # Left column - Invoice details
        invoice_details = [
            [Paragraph("<b>Invoice No:</b>", self.styles['NormalText']),
             Paragraph(invoice.invoice_number, self.styles['NormalText'])],
            [Paragraph("<b>Date:</b>", self.styles['NormalText']),
             Paragraph(format_date(inv_date), self.styles['NormalText'])],
            [Paragraph("<b>Payment:</b>", self.styles['NormalText']),
             Paragraph(invoice.payment_mode, self.styles['NormalText'])],
        ]

        left_table = Table(invoice_details, colWidths=[25*mm, 50*mm])
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
            from database.models import Customer
            customer = Customer.get_by_id(invoice.customer_id)
            if customer:
                if customer.address:
                    customer_content.append(Paragraph(customer.address, self.styles['NormalText']))
                if customer.gstin:
                    customer_content.append(Paragraph(f"<b>GSTIN:</b> {customer.gstin}", self.styles['NormalText']))
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

        # Column headers
        headers = ['#', 'Description', 'HSN', 'Qty', 'Rate', 'GST%', 'CGST', 'SGST', 'Amount']

        # Column widths (total should equal content_width)
        col_widths = [8*mm, 45*mm, 18*mm, 15*mm, 22*mm, 12*mm, 18*mm, 18*mm, 24*mm]

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
            row = [
                str(idx),
                item.product_name[:30],  # Truncate long names
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
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),   # HSN
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),   # Qty
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),   # Rate onwards

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

        try:
            # Generate PDF to temp file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                pdf_path = f.name
                self.generate_invoice_pdf(invoice, pdf_path)

            # Print based on OS
            system = platform.system()

            if system == 'Windows':
                import os
                os.startfile(pdf_path, 'print')
            elif system == 'Darwin':  # macOS
                subprocess.run(['lpr', pdf_path])
            else:  # Linux
                subprocess.run(['lpr', pdf_path])

            return True

        except Exception as e:
            print(f"Print error: {e}")
            return False

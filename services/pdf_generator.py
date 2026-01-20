"""PDF invoice generator using ReportLab"""
from io import BytesIO
from datetime import date
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from database.models import Invoice, Company
from utils.formatters import format_currency, number_to_words_indian, format_date


class PDFGenerator:
    """Generate A4 PDF invoices"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Set up custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=2*mm
        ))

        self.styles.add(ParagraphStyle(
            name='CompanyAddress',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=1*mm
        ))

        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceBefore=5*mm,
            spaceAfter=5*mm
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceBefore=3*mm,
            spaceAfter=2*mm
        ))

        self.styles.add(ParagraphStyle(
            name='AmountWords',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique'
        ))

        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER
        ))

    def generate_invoice_pdf(self, invoice: Invoice, output_path: str = None) -> bytes:
        """
        Generate PDF for an invoice

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
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )

        elements = []

        # Company Header
        elements.append(Paragraph(company.name, self.styles['CompanyName']))
        elements.append(Paragraph(company.address, self.styles['CompanyAddress']))

        if company.gstin:
            elements.append(Paragraph(
                f"GSTIN: {company.gstin}",
                self.styles['CompanyAddress']
            ))

        if company.phone:
            elements.append(Paragraph(
                f"Phone: {company.phone}",
                self.styles['CompanyAddress']
            ))

        # Invoice Title
        elements.append(Paragraph("TAX INVOICE", self.styles['InvoiceTitle']))

        # Invoice Details Table
        invoice_info = [
            ['Invoice No:', invoice.invoice_number, 'Date:', format_date(invoice.invoice_date)],
        ]

        invoice_table = Table(invoice_info, colWidths=[25*mm, 55*mm, 20*mm, 40*mm])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(invoice_table)
        elements.append(Spacer(1, 5*mm))

        # Bill To Section
        elements.append(Paragraph("Bill To:", self.styles['SectionHeader']))

        bill_to_text = invoice.customer_name
        elements.append(Paragraph(bill_to_text, self.styles['Normal']))
        elements.append(Spacer(1, 5*mm))

        # Items Table
        items_header = ['#', 'Item Description', 'HSN', 'Qty', 'Rate', 'GST%', 'Amount']

        items_data = [items_header]

        for idx, item in enumerate(invoice.items, 1):
            items_data.append([
                str(idx),
                item.product_name,
                item.hsn_code or '-',
                f"{item.qty} {item.unit}",
                format_currency(item.rate),
                f"{int(item.gst_rate)}%",
                format_currency(item.total)
            ])

        # Column widths
        col_widths = [8*mm, 60*mm, 18*mm, 20*mm, 25*mm, 15*mm, 30*mm]

        items_table = Table(items_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # #
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # HSN
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Qty
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Rate, GST%, Amount

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),

            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(items_table)
        elements.append(Spacer(1, 5*mm))

        # Totals Section
        totals_data = [
            ['Subtotal:', format_currency(invoice.subtotal)],
        ]

        if invoice.cgst_total > 0:
            totals_data.append([f'CGST:', format_currency(invoice.cgst_total)])
        if invoice.sgst_total > 0:
            totals_data.append([f'SGST:', format_currency(invoice.sgst_total)])
        if invoice.igst_total > 0:
            totals_data.append([f'IGST:', format_currency(invoice.igst_total)])

        if invoice.discount > 0:
            totals_data.append(['Discount:', f'- {format_currency(invoice.discount)}'])

        totals_data.append(['Grand Total:', format_currency(invoice.grand_total)])

        totals_table = Table(totals_data, colWidths=[120*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ]))

        elements.append(totals_table)
        elements.append(Spacer(1, 5*mm))

        # Amount in Words
        amount_words = number_to_words_indian(invoice.grand_total)
        elements.append(Paragraph(
            f"<b>Amount in Words:</b> {amount_words}",
            self.styles['AmountWords']
        ))

        elements.append(Spacer(1, 5*mm))

        # Payment Mode
        elements.append(Paragraph(
            f"<b>Payment Mode:</b> {invoice.payment_mode}",
            self.styles['Normal']
        ))

        elements.append(Spacer(1, 15*mm))

        # Footer Section
        footer_data = [
            ['Terms & Conditions:', '', 'For ' + company.name],
            ['1. Goods once sold will not be taken back', '', ''],
            ['2. Subject to local jurisdiction', '', ''],
            ['', '', ''],
            ['', '', 'Authorized Signatory'],
        ]

        footer_table = Table(footer_data, colWidths=[90*mm, 20*mm, 60*mm])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(footer_table)

        # Build PDF
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes

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

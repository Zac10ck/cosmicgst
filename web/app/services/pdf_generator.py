"""Professional Indian GST Invoice PDF Generator
Based on standard Indian GST invoice formats as per Rule 46 of CGST Rules
"""
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


# Indian State Codes
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


def get_state_name(state_code):
    """Get state name from code"""
    return STATE_CODES.get(str(state_code), "")


def number_to_words_indian(num):
    """Convert number to words using Indian numbering system"""
    if num is None or num == 0:
        return 'Zero Rupees Only'

    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
            'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
            'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

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
    """Professional Indian GST Invoice Generator"""

    # Color scheme - Professional blue theme
    PRIMARY = colors.HexColor('#1a5276')      # Dark blue
    SECONDARY = colors.HexColor('#2874a6')    # Medium blue
    LIGHT_BG = colors.HexColor('#eaf2f8')     # Very light blue
    BORDER = colors.HexColor('#aed6f1')       # Light border
    TEXT_DARK = colors.HexColor('#1c2833')    # Almost black
    TEXT_MUTED = colors.HexColor('#5d6d7e')   # Grey

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.page_width, self.page_height = A4
        self.margin = 12 * mm
        self.content_width = self.page_width - (2 * self.margin)

    def _setup_styles(self):
        """Setup paragraph styles"""
        # Company name - Large bold
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=self.PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=1*mm
        ))

        # Normal text
        self.styles.add(ParagraphStyle(
            name='Normal8',
            fontSize=8,
            fontName='Helvetica',
            textColor=self.TEXT_DARK,
            leading=10
        ))

        self.styles.add(ParagraphStyle(
            name='Normal8Center',
            fontSize=8,
            fontName='Helvetica',
            textColor=self.TEXT_DARK,
            alignment=TA_CENTER,
            leading=10
        ))

        self.styles.add(ParagraphStyle(
            name='Normal9',
            fontSize=9,
            fontName='Helvetica',
            textColor=self.TEXT_DARK,
            leading=11
        ))

        self.styles.add(ParagraphStyle(
            name='Bold9',
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=self.TEXT_DARK,
            leading=11
        ))

        self.styles.add(ParagraphStyle(
            name='Bold10',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=self.TEXT_DARK,
            leading=12
        ))

        self.styles.add(ParagraphStyle(
            name='Title',
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHead',
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=self.PRIMARY,
            leading=11
        ))

    def generate_invoice_pdf(self, invoice, company, items):
        """Generate professional GST invoice PDF"""
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
        is_cancelled = getattr(invoice, 'is_cancelled', False)

        # 1. Company Header
        elements.extend(self._build_header(company, invoice, is_cancelled))

        # 2. Billing Parties (Bill From / Bill To)
        elements.extend(self._build_parties(company, invoice))

        # 3. Items Table
        elements.extend(self._build_items_table(items, invoice))

        # 4. Tax Summary (HSN-wise) + Totals
        elements.extend(self._build_summary_and_totals(items, invoice))

        # 5. Amount in Words
        elements.extend(self._build_amount_words(invoice))

        # 6. Bank Details & Signature
        elements.extend(self._build_footer(company, invoice))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_header(self, company, invoice, is_cancelled):
        """Build invoice header with company details"""
        elements = []

        # Company Name (centered, large)
        company_name = company.name if company else 'COMPANY NAME'
        elements.append(Paragraph(company_name.upper(), self.styles['CompanyName']))

        # Company Address & Contact (centered)
        if company:
            address_parts = []
            if company.address:
                address_parts.append(company.address)
            contact_parts = []
            if company.phone:
                contact_parts.append(f"Phone: {company.phone}")
            if company.email:
                contact_parts.append(f"Email: {company.email}")

            if address_parts:
                elements.append(Paragraph(' | '.join(address_parts), self.styles['Normal8Center']))
            if contact_parts:
                elements.append(Paragraph(' | '.join(contact_parts), self.styles['Normal8Center']))

            # GSTIN
            if company.gstin:
                elements.append(Paragraph(f"<b>GSTIN: {company.gstin}</b>", self.styles['Normal8Center']))

        elements.append(Spacer(1, 2*mm))

        # TAX INVOICE Title Bar
        invoice_type = getattr(invoice, 'invoice_type', 'TAX_INVOICE')
        if invoice_type == 'BILL_OF_SUPPLY':
            title_text = "BILL OF SUPPLY"
        else:
            title_text = "TAX INVOICE"

        if is_cancelled:
            title_text += " - CANCELLED"
            bg_color = colors.HexColor('#c0392b')
        else:
            bg_color = self.PRIMARY

        title_table = Table([[Paragraph(title_text, self.styles['Title'])]], colWidths=[self.content_width])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5*mm),
        ]))
        elements.append(title_table)

        # Invoice Number and Date Row
        inv_date = invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else ''
        info_data = [
            [f"Invoice No: {invoice.invoice_number}", f"Date: {inv_date}"]
        ]
        info_table = Table(info_data, colWidths=[self.content_width/2, self.content_width/2])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 2*mm))

        return elements

    def _build_parties(self, company, invoice):
        """Build Bill From / Bill To section"""
        elements = []

        customer = getattr(invoice, 'customer', None)
        customer_name = invoice.customer_name or 'Cash Customer'

        # LEFT: Bill From (Seller)
        from_data = [[Paragraph("<b>Bill From (Seller)</b>", self.styles['SectionHead'])]]
        if company:
            from_data.append([Paragraph(f"<b>{company.name}</b>", self.styles['Normal9'])])
            if company.address:
                from_data.append([Paragraph(company.address, self.styles['Normal8'])])
            if company.gstin:
                from_data.append([Paragraph(f"GSTIN: {company.gstin}", self.styles['Normal8'])])
            if company.state_code:
                state_name = get_state_name(company.state_code)
                from_data.append([Paragraph(f"State: {state_name} ({company.state_code})", self.styles['Normal8'])])
            if company.phone:
                from_data.append([Paragraph(f"Phone: {company.phone}", self.styles['Normal8'])])

        from_table = Table(from_data, colWidths=[90*mm])
        from_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))

        # RIGHT: Bill To (Buyer)
        to_data = [[Paragraph("<b>Bill To (Buyer)</b>", self.styles['SectionHead'])]]
        to_data.append([Paragraph(f"<b>{customer_name}</b>", self.styles['Normal9'])])
        if customer:
            if customer.address:
                to_data.append([Paragraph(customer.address, self.styles['Normal8'])])
            if customer.gstin:
                to_data.append([Paragraph(f"GSTIN: {customer.gstin}", self.styles['Normal8'])])
            if customer.state_code:
                state_name = get_state_name(customer.state_code)
                to_data.append([Paragraph(f"State: {state_name} ({customer.state_code})", self.styles['Normal8'])])
            if hasattr(customer, 'phone') and customer.phone:
                to_data.append([Paragraph(f"Phone: {customer.phone}", self.styles['Normal8'])])
            if hasattr(customer, 'dl_number') and customer.dl_number:
                to_data.append([Paragraph(f"DL No: {customer.dl_number}", self.styles['Normal8'])])

        to_table = Table(to_data, colWidths=[90*mm])
        to_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))

        # Combine
        parties = Table([[from_table, to_table]], colWidths=[95*mm, 95*mm])
        parties.setStyle(TableStyle([
            ('BOX', (0, 0), (0, 0), 0.5, self.PRIMARY),
            ('BOX', (1, 0), (1, 0), 0.5, self.PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(parties)
        elements.append(Spacer(1, 2*mm))

        return elements

    def _build_items_table(self, items, invoice):
        """Build items table with GST columns"""
        elements = []

        # Determine if IGST or CGST/SGST
        has_igst = any((getattr(item, 'igst', 0) or 0) > 0 for item in items)

        # Build header row
        if has_igst:
            headers = ['#', 'Description', 'HSN', 'Qty', 'Unit', 'Rate', 'Taxable', 'IGST %', 'IGST Amt', 'Total']
            col_widths = [7*mm, 50*mm, 15*mm, 12*mm, 12*mm, 18*mm, 22*mm, 14*mm, 18*mm, 22*mm]
        else:
            headers = ['#', 'Description', 'HSN', 'Qty', 'Unit', 'Rate', 'Taxable', 'CGST %', 'SGST %', 'Total']
            col_widths = [7*mm, 50*mm, 15*mm, 12*mm, 12*mm, 18*mm, 22*mm, 14*mm, 14*mm, 22*mm]

        data = [headers]

        # Build item rows
        for i, item in enumerate(items, 1):
            qty = item.qty or 0
            rate = item.rate or 0
            taxable = item.taxable_value or (qty * rate)
            gst_rate = item.gst_rate or 0
            total = item.total or 0

            # Product description with batch if available
            desc = item.product_name or ''
            batch = getattr(item, 'batch_number', '')
            if batch:
                desc = f"{desc}\nBatch: {batch}"

            if has_igst:
                igst_amt = item.igst or 0
                row = [
                    str(i),
                    Paragraph(desc, self.styles['Normal8']),
                    item.hsn_code or '-',
                    f"{qty:.0f}" if qty == int(qty) else f"{qty:.2f}",
                    item.unit or 'NOS',
                    f"{rate:,.2f}",
                    f"{taxable:,.2f}",
                    f"{gst_rate:.0f}%",
                    f"{igst_amt:,.2f}",
                    f"{total:,.2f}"
                ]
            else:
                half_rate = gst_rate / 2
                row = [
                    str(i),
                    Paragraph(desc, self.styles['Normal8']),
                    item.hsn_code or '-',
                    f"{qty:.0f}" if qty == int(qty) else f"{qty:.2f}",
                    item.unit or 'NOS',
                    f"{rate:,.2f}",
                    f"{taxable:,.2f}",
                    f"{half_rate:.1f}%",
                    f"{half_rate:.1f}%",
                    f"{total:,.2f}"
                ]
            data.append(row)

        table = Table(data, colWidths=col_widths)

        style_commands = [
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),

            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),      # #
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),        # Description
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),      # HSN
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),      # Numbers right-aligned
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),

            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 1*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1*mm),

            # Borders
            ('BOX', (0, 0), (-1, -1), 0.5, self.PRIMARY),
            ('LINEBELOW', (0, 0), (-1, 0), 1, self.PRIMARY),
            ('INNERGRID', (0, 1), (-1, -1), 0.25, self.BORDER),
        ]

        # Alternating row colors
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), self.LIGHT_BG))

        table.setStyle(TableStyle(style_commands))
        elements.append(table)

        return elements

    def _build_summary_and_totals(self, items, invoice):
        """Build HSN summary and totals section side by side"""
        elements = []
        elements.append(Spacer(1, 2*mm))

        # Calculate HSN summary
        hsn_data = {}
        for item in items:
            hsn = item.hsn_code or 'NA'
            if hsn not in hsn_data:
                hsn_data[hsn] = {'taxable': 0, 'cgst': 0, 'sgst': 0, 'igst': 0, 'rate': item.gst_rate or 0}
            hsn_data[hsn]['taxable'] += item.taxable_value or 0
            hsn_data[hsn]['cgst'] += item.cgst or 0
            hsn_data[hsn]['sgst'] += item.sgst or 0
            hsn_data[hsn]['igst'] += item.igst or 0

        has_igst = any(v['igst'] > 0 for v in hsn_data.values())

        # LEFT: HSN Summary Table
        if has_igst:
            hsn_headers = ['HSN', 'Taxable', 'IGST %', 'IGST Amt']
            hsn_widths = [20*mm, 28*mm, 15*mm, 25*mm]
        else:
            hsn_headers = ['HSN', 'Taxable', 'CGST', 'SGST']
            hsn_widths = [20*mm, 28*mm, 20*mm, 20*mm]

        hsn_rows = [hsn_headers]
        total_taxable = 0
        total_cgst = 0
        total_sgst = 0
        total_igst = 0

        for hsn, vals in hsn_data.items():
            total_taxable += vals['taxable']
            if has_igst:
                total_igst += vals['igst']
                hsn_rows.append([hsn, f"{vals['taxable']:,.2f}", f"{vals['rate']:.0f}%", f"{vals['igst']:,.2f}"])
            else:
                total_cgst += vals['cgst']
                total_sgst += vals['sgst']
                hsn_rows.append([hsn, f"{vals['taxable']:,.2f}", f"{vals['cgst']:,.2f}", f"{vals['sgst']:,.2f}"])

        # Total row
        if has_igst:
            hsn_rows.append(['Total', f"{total_taxable:,.2f}", '', f"{total_igst:,.2f}"])
        else:
            hsn_rows.append(['Total', f"{total_taxable:,.2f}", f"{total_cgst:,.2f}", f"{total_sgst:,.2f}"])

        hsn_table = Table(hsn_rows, colWidths=hsn_widths)
        hsn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.SECONDARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, self.SECONDARY),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, self.BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BACKGROUND', (0, -1), (-1, -1), self.LIGHT_BG),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))

        hsn_section = [[Paragraph("<b>HSN Summary</b>", self.styles['SectionHead'])], [hsn_table]]
        hsn_container = Table(hsn_section, colWidths=[90*mm])

        # RIGHT: Totals
        totals_rows = []
        totals_rows.append(['Subtotal', f"{invoice.subtotal:,.2f}"])

        if invoice.cgst_total and invoice.cgst_total > 0:
            totals_rows.append(['CGST', f"{invoice.cgst_total:,.2f}"])
            totals_rows.append(['SGST', f"{invoice.sgst_total:,.2f}"])

        if invoice.igst_total and invoice.igst_total > 0:
            totals_rows.append(['IGST', f"{invoice.igst_total:,.2f}"])

        if invoice.discount and invoice.discount > 0:
            totals_rows.append(['Discount', f"- {invoice.discount:,.2f}"])

        # Round off
        grand = invoice.grand_total or 0
        subtotal_with_tax = (invoice.subtotal or 0) + (invoice.cgst_total or 0) + (invoice.sgst_total or 0) + (invoice.igst_total or 0) - (invoice.discount or 0)
        round_off = grand - subtotal_with_tax
        if abs(round_off) >= 0.01:
            totals_rows.append(['Round Off', f"{round_off:+,.2f}"])

        totals_table = Table(totals_rows, colWidths=[35*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_BG),
        ]))

        # Grand Total (highlighted)
        grand_row = [['GRAND TOTAL', f"Rs. {invoice.grand_total:,.2f}"]]
        grand_table = Table(grand_row, colWidths=[35*mm, 40*mm])
        grand_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), self.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5*mm),
        ]))

        totals_section = [[totals_table], [grand_table]]
        totals_container = Table(totals_section, colWidths=[75*mm])
        totals_container.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        # Combine HSN and Totals
        combined = Table([[hsn_container, totals_container]], colWidths=[100*mm, 90*mm])
        combined.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(combined)

        return elements

    def _build_amount_words(self, invoice):
        """Build amount in words section"""
        elements = []
        elements.append(Spacer(1, 2*mm))

        words = number_to_words_indian(invoice.grand_total)
        amount_row = [[Paragraph(f"<b>Amount in Words:</b> {words}", self.styles['Normal9'])]]
        amount_table = Table(amount_row, colWidths=[self.content_width])
        amount_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ]))
        elements.append(amount_table)

        return elements

    def _build_footer(self, company, invoice):
        """Build footer with bank details, payment mode, terms, and signature"""
        elements = []
        elements.append(Spacer(1, 3*mm))

        # Payment Mode
        payment_mode = getattr(invoice, 'payment_mode', 'CASH')
        payment_labels = {'CASH': 'Cash', 'CARD': 'Card', 'UPI': 'UPI', 'BANK': 'Bank Transfer', 'CREDIT': 'Credit'}
        payment_text = payment_labels.get(payment_mode, payment_mode)

        # LEFT: Bank Details + Terms
        left_content = []

        # Bank Details
        if company and (company.bank_name or company.bank_account):
            left_content.append([Paragraph("<b>Bank Details for Payment:</b>", self.styles['SectionHead'])])
            bank_info = []
            if company.bank_name:
                bank_info.append(f"Bank: {company.bank_name}")
            if company.bank_account:
                bank_info.append(f"A/C No: {company.bank_account}")
            if company.bank_ifsc:
                bank_info.append(f"IFSC: {company.bank_ifsc}")
            left_content.append([Paragraph("<br/>".join(bank_info), self.styles['Normal8'])])
            left_content.append([Spacer(1, 2*mm)])

        # Payment Mode
        left_content.append([Paragraph(f"<b>Payment Mode:</b> {payment_text}", self.styles['Normal9'])])
        left_content.append([Spacer(1, 2*mm)])

        # Terms & Conditions
        terms = company.invoice_terms if company and company.invoice_terms else "1. Goods once sold will not be taken back.\n2. Subject to local jurisdiction.\n3. E. & O.E."
        left_content.append([Paragraph("<b>Terms & Conditions:</b>", self.styles['SectionHead'])])
        left_content.append([Paragraph(terms.replace('\n', '<br/>'), self.styles['Normal8'])])

        left_table = Table(left_content, colWidths=[105*mm])
        left_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5*mm),
        ]))

        # RIGHT: Signature
        company_name = company.name if company else 'Company'
        sig_content = [
            [Paragraph(f"For <b>{company_name}</b>", self.styles['Normal9'])],
            [Spacer(1, 15*mm)],
            [Paragraph("_________________________", self.styles['Normal8Center'])],
            [Paragraph("Authorized Signatory", self.styles['Normal8Center'])]
        ]
        sig_table = Table(sig_content, colWidths=[70*mm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        # Combine
        footer_table = Table([[left_table, sig_table]], colWidths=[115*mm, 75*mm])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),
            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER),
            ('LINEBEFORE', (1, 0), (1, 0), 0.5, self.BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(footer_table)

        # Computer generated note
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(
            "<font size='7' color='#7f8c8d'>This is a computer generated invoice and does not require physical signature.</font>",
            self.styles['Normal8Center']
        ))

        return elements

    # ============ QUOTATION METHODS ============

    def generate_quotation_pdf(self, quotation, company, items):
        """Generate quotation PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=self.margin, rightMargin=self.margin,
                               topMargin=self.margin, bottomMargin=self.margin)
        elements = []

        # Header
        company_name = company.name if company else 'COMPANY NAME'
        elements.append(Paragraph(company_name.upper(), self.styles['CompanyName']))
        if company and company.address:
            elements.append(Paragraph(company.address, self.styles['Normal8Center']))
        if company and company.gstin:
            elements.append(Paragraph(f"GSTIN: {company.gstin}", self.styles['Normal8Center']))
        elements.append(Spacer(1, 2*mm))

        # Title
        title_table = Table([[Paragraph("QUOTATION", self.styles['Title'])]], colWidths=[self.content_width])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f39c12')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5*mm),
        ]))
        elements.append(title_table)

        # Quotation info
        q_date = quotation.quotation_date.strftime('%d-%m-%Y') if quotation.quotation_date else ''
        valid_date = quotation.validity_date.strftime('%d-%m-%Y') if quotation.validity_date else ''
        info_data = [[f"Quotation No: {quotation.quotation_number}", f"Date: {q_date}", f"Valid Until: {valid_date}"]]
        info_table = Table(info_data, colWidths=[self.content_width/3]*3)
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_BG),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 2*mm))

        # Customer
        customer_name = quotation.customer_name or 'Customer'
        elements.append(Paragraph(f"<b>To:</b> {customer_name}", self.styles['Normal9']))
        if quotation.customer and quotation.customer.address:
            elements.append(Paragraph(quotation.customer.address, self.styles['Normal8']))
        elements.append(Spacer(1, 2*mm))

        # Items table (simplified)
        headers = ['#', 'Description', 'HSN', 'Qty', 'Rate', 'Amount']
        col_widths = [8*mm, 70*mm, 20*mm, 18*mm, 25*mm, 30*mm]
        data = [headers]
        for i, item in enumerate(items, 1):
            data.append([
                str(i),
                item.product_name or '',
                item.hsn_code or '-',
                f"{item.qty:.0f}" if item.qty == int(item.qty) else f"{item.qty:.2f}",
                f"{item.rate:,.2f}",
                f"{item.total:,.2f}"
            ])

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, self.PRIMARY),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, self.BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(table)

        # Totals
        elements.append(Spacer(1, 2*mm))
        totals = [
            ['Subtotal', f"{quotation.subtotal:,.2f}"],
            ['GST', f"{(quotation.cgst_total or 0) + (quotation.sgst_total or 0) + (quotation.igst_total or 0):,.2f}"],
            ['Total', f"Rs. {quotation.grand_total:,.2f}"]
        ]
        totals_table = Table(totals, colWidths=[30*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f39c12')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ]))
        wrapper = Table([['', totals_table]], colWidths=[self.content_width - 75*mm, 75*mm])
        elements.append(wrapper)

        # Notes
        if quotation.notes:
            elements.append(Spacer(1, 3*mm))
            elements.append(Paragraph(f"<b>Notes:</b> {quotation.notes}", self.styles['Normal8']))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    # ============ CREDIT NOTE METHODS ============

    def generate_credit_note_pdf(self, credit_note, company, items):
        """Generate credit note PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=self.margin, rightMargin=self.margin,
                               topMargin=self.margin, bottomMargin=self.margin)
        elements = []

        # Header
        company_name = company.name if company else 'COMPANY NAME'
        elements.append(Paragraph(company_name.upper(), self.styles['CompanyName']))
        if company and company.address:
            elements.append(Paragraph(company.address, self.styles['Normal8Center']))
        if company and company.gstin:
            elements.append(Paragraph(f"GSTIN: {company.gstin}", self.styles['Normal8Center']))
        elements.append(Spacer(1, 2*mm))

        # Title
        title_table = Table([[Paragraph("CREDIT NOTE", self.styles['Title'])]], colWidths=[self.content_width])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#c0392b')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5*mm),
        ]))
        elements.append(title_table)

        # Credit Note info
        cn_date = credit_note.credit_note_date.strftime('%d-%m-%Y') if credit_note.credit_note_date else ''
        info_data = [
            [f"Credit Note No: {credit_note.credit_note_number}", f"Date: {cn_date}"],
            [f"Against Invoice: {credit_note.original_invoice_number or '-'}", f"Reason: {credit_note.reason or '-'}"]
        ]
        info_table = Table(info_data, colWidths=[self.content_width/2]*2)
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fadbd8')),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 2*mm))

        # Customer
        customer_name = credit_note.customer_name or 'Customer'
        elements.append(Paragraph(f"<b>To:</b> {customer_name}", self.styles['Normal9']))
        elements.append(Spacer(1, 2*mm))

        # Items table
        headers = ['#', 'Description', 'HSN', 'Qty', 'Rate', 'Amount']
        col_widths = [8*mm, 70*mm, 20*mm, 18*mm, 25*mm, 30*mm]
        data = [headers]
        for i, item in enumerate(items, 1):
            data.append([
                str(i),
                item.product_name or '',
                item.hsn_code or '-',
                f"{item.qty:.0f}" if item.qty == int(item.qty) else f"{item.qty:.2f}",
                f"{item.rate:,.2f}",
                f"{item.total:,.2f}"
            ])

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#c0392b')),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, self.BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(table)

        # Totals
        elements.append(Spacer(1, 2*mm))
        totals = [
            ['Subtotal', f"{credit_note.subtotal:,.2f}"],
            ['GST', f"{(credit_note.cgst_total or 0) + (credit_note.sgst_total or 0) + (credit_note.igst_total or 0):,.2f}"],
            ['Credit Amount', f"Rs. {credit_note.grand_total:,.2f}"]
        ]
        totals_table = Table(totals, colWidths=[35*mm, 40*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#c0392b')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ]))
        wrapper = Table([['', totals_table]], colWidths=[self.content_width - 80*mm, 80*mm])
        elements.append(wrapper)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# Create singleton instance
pdf_generator = PDFGenerator()

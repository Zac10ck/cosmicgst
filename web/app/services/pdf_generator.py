"""Invoice PDF Generator - Classic and Modern Styles"""
from io import BytesIO
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
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

    result = 'Indian Rupees ' + words(rupees)
    if paise > 0:
        result += ' and ' + words(paise) + ' Paise'
    result += ' Only'
    return result


class PDFGenerator:
    """Invoice PDF Generator with Classic and Modern Styles"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self.page_width, self.page_height = A4
        self.margin = 12 * mm
        self.content_width = self.page_width - (2 * self.margin)

    def _setup_styles(self):
        """Setup custom paragraph styles"""
        # Classic styles
        self.styles.add(ParagraphStyle(
            name='CompanyName', fontSize=14, fontName='Helvetica-Bold',
            alignment=TA_CENTER, spaceAfter=0
        ))
        self.styles.add(ParagraphStyle(
            name='CompanyInfo', fontSize=9, fontName='Helvetica',
            alignment=TA_CENTER, leading=11
        ))
        self.styles.add(ParagraphStyle(
            name='TaxInvoice', fontSize=11, fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='Small', fontSize=8, fontName='Helvetica', leading=10
        ))
        self.styles.add(ParagraphStyle(
            name='SmallBold', fontSize=8, fontName='Helvetica-Bold', leading=10
        ))
        self.styles.add(ParagraphStyle(
            name='Normal9', fontSize=9, fontName='Helvetica', leading=11
        ))
        self.styles.add(ParagraphStyle(
            name='Bold9', fontSize=9, fontName='Helvetica-Bold', leading=11
        ))
        self.styles.add(ParagraphStyle(
            name='SmallCenter', fontSize=8, fontName='Helvetica', alignment=TA_CENTER, leading=10
        ))

    def generate_invoice_pdf(self, invoice, company, items):
        """Generate invoice PDF based on company style setting"""
        style = getattr(company, 'invoice_style', 'classic') if company else 'classic'

        if style == 'modern':
            return self._generate_modern_invoice(invoice, company, items)
        else:
            return self._generate_classic_invoice(invoice, company, items)

    # ==================== CLASSIC STYLE ====================

    def _generate_classic_invoice(self, invoice, company, items):
        """Generate classic invoice PDF - Simple, clean, professional"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=self.margin, rightMargin=self.margin,
            topMargin=self.margin, bottomMargin=self.margin
        )

        elements = []
        is_cancelled = getattr(invoice, 'is_cancelled', False)

        # 1. Header
        elements.extend(self._classic_header(company, invoice, is_cancelled))
        # 2. Customer & Invoice Info
        elements.extend(self._classic_customer_info(company, invoice))
        # 3. Items Table
        elements.extend(self._classic_items_table(items, invoice))
        # 4. Tax Summary
        elements.extend(self._classic_tax_total(items, invoice))
        # 5. Amount in Words
        elements.extend(self._classic_amount_words(invoice))
        # 6. Bank & Signature
        elements.extend(self._classic_footer(company, invoice))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _classic_header(self, company, invoice, is_cancelled):
        elements = []

        gstin = company.gstin if company else ''
        if gstin:
            elements.append(Paragraph(f"GSTIN: {gstin}", self.styles['Small']))

        elements.append(Spacer(1, 2*mm))

        company_name = company.name.upper() if company else 'COMPANY NAME'
        elements.append(Paragraph(company_name, self.styles['CompanyName']))

        if company:
            addr_parts = []
            if company.address:
                addr_parts.append(company.address.replace('\n', ', '))
            if company.phone:
                addr_parts.append(f"Ph.{company.phone}")
            if addr_parts:
                elements.append(Paragraph(', '.join(addr_parts), self.styles['CompanyInfo']))

        elements.append(Spacer(1, 3*mm))

        title = "TAX INVOICE"
        if is_cancelled:
            title = "TAX INVOICE - CANCELLED"
        elements.append(Paragraph(f"<u><b>{title}</b></u>", self.styles['TaxInvoice']))
        elements.append(Spacer(1, 3*mm))

        return elements

    def _classic_customer_info(self, company, invoice):
        elements = []

        customer = getattr(invoice, 'customer', None)
        customer_name = invoice.customer_name or 'Walk-in Customer'
        customer_addr = ''
        if customer and customer.address:
            customer_addr = customer.address.replace('\n', ', ')

        inv_date = invoice.invoice_date.strftime('%d-%b-%Y') if invoice.invoice_date else ''

        left_content = f"<b>Name and Address of the Purchasing Dealer:</b><br/>{customer_name}"
        if customer_addr:
            left_content += f"<br/>{customer_addr}"

        center_content = "<b>ORIGINAL</b>"
        right_content = f"<b>Invoice No.:</b> {invoice.invoice_number}<br/><b>Date:</b> {inv_date}"

        data = [[
            Paragraph(left_content, self.styles['Small']),
            Paragraph(center_content, self.styles['Small']),
            Paragraph(right_content, self.styles['Small'])
        ]]

        table = Table(data, colWidths=[85*mm, 40*mm, 60*mm])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 2*mm))

        return elements

    def _classic_items_table(self, items, invoice):
        elements = []

        headers = ['Sl.', 'Commodity / Item', 'Bat.No/Ex.Date', 'HSN', 'Pack', 'Qty', 'Rate', 'GST%', 'Amount']
        col_widths = [8*mm, 55*mm, 25*mm, 18*mm, 15*mm, 12*mm, 22*mm, 12*mm, 22*mm]

        data = [headers]
        subtotal = 0

        for i, item in enumerate(items, 1):
            qty = item.qty or 0
            rate = item.rate or 0
            gst_rate = item.gst_rate or 0
            total = item.total or 0
            subtotal += item.taxable_value or (qty * rate)
            batch = getattr(item, 'batch_number', '') or ''

            row = [str(i), item.product_name or '', batch, item.hsn_code or '',
                   item.unit or 'Nos', f"{qty:g}", f"{rate:,.2f}", f"{gst_rate:g}", f"{total:,.2f}"]
            data.append(row)

        while len(data) < 6:
            data.append(['', '', '', '', '', '', '', '', ''])

        data.append(['', '', '', '', '', '', '', '', f"{subtotal:,.2f}"])

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),
            ('ALIGN', (6, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            ('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 1*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1*mm),
        ]))
        elements.append(table)

        return elements

    def _classic_tax_total(self, items, invoice):
        elements = []

        cgst_total = invoice.cgst_total or 0
        sgst_total = invoice.sgst_total or 0
        igst_total = invoice.igst_total or 0

        # Group tax by GST rate for accurate display
        tax_by_rate = {}
        for item in items:
            rate = item.gst_rate or 0
            if rate not in tax_by_rate:
                tax_by_rate[rate] = {'cgst': 0, 'sgst': 0, 'igst': 0}
            tax_by_rate[rate]['cgst'] += item.cgst or 0
            tax_by_rate[rate]['sgst'] += item.sgst or 0
            tax_by_rate[rate]['igst'] += item.igst or 0

        tax_rows = []
        # Show tax breakdown by rate
        for rate in sorted(tax_by_rate.keys()):
            if rate == 0:
                continue  # Skip 0% GST
            half_rate = rate / 2
            vals = tax_by_rate[rate]
            if vals['cgst'] > 0:
                tax_rows.append([f'CGST {half_rate:g}%', f'{vals["cgst"]:,.2f}'])
                tax_rows.append([f'SGST {half_rate:g}%', f'{vals["sgst"]:,.2f}'])
            if vals['igst'] > 0:
                tax_rows.append([f'IGST {rate:g}%', f'{vals["igst"]:,.2f}'])

        if tax_rows:
            tax_table = Table(tax_rows, colWidths=[30*mm, 25*mm])
            tax_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
            ]))
            wrapper = Table([['', tax_table]], colWidths=[self.content_width - 60*mm, 60*mm])
            elements.append(wrapper)

        elements.append(Spacer(1, 1*mm))
        line_table = Table([['─' * 100]], colWidths=[self.content_width])
        line_table.setStyle(TableStyle([('FONTSIZE', (0, 0), (-1, -1), 6)]))
        elements.append(line_table)

        return elements

    def _classic_amount_words(self, invoice):
        elements = []
        words = number_to_words_indian(invoice.grand_total)
        grand_total = invoice.grand_total or 0

        data = [[
            Paragraph(f"<b>Amount in Words:</b> {words}", self.styles['Small']),
            Paragraph(f"<b>{grand_total:,.2f}</b>", self.styles['Bold9'])
        ]]

        table = Table(data, colWidths=[self.content_width - 35*mm, 35*mm])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 3*mm))

        return elements

    def _classic_footer(self, company, invoice):
        elements = []

        bank_lines = []
        if company and company.bank_name:
            bank_lines.append(f"<b>Our Bankers:</b> {company.bank_name}")
            bank_info = []
            if company.bank_account:
                bank_info.append(f"A/c No:{company.bank_account}")
            if company.bank_ifsc:
                bank_info.append(f"IFS Code:{company.bank_ifsc}")
            if bank_info:
                bank_lines.append('  '.join(bank_info))

        payment_mode = getattr(invoice, 'payment_mode', 'CASH')
        payment_labels = {'CASH': 'Cash', 'CARD': 'Card', 'UPI': 'UPI', 'BANK': 'Bank Transfer', 'CREDIT': 'Credit'}
        bank_lines.append(f"<b>Payment Mode:</b> {payment_labels.get(payment_mode, payment_mode)}")

        left_content = '<br/>'.join(bank_lines)
        company_name = company.name if company else 'Company'
        right_content = f"for <b>{company_name}</b><br/><br/><br/><br/>Authorized Signatory"

        data = [[
            Paragraph(left_content, self.styles['Small']),
            Paragraph(right_content, self.styles['Small'])
        ]]

        table = Table(data, colWidths=[self.content_width - 60*mm, 60*mm])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 3*mm))

        declaration = """<b>E & OE</b>                    <b>DECLARATION</b>
<br/>We Declare that this Invoice Shows the actual Price of the Goods described and that All Particulars are True and Correct
<br/>* subject to Kottayam Jurisdiction"""
        elements.append(Paragraph(declaration, self.styles['Small']))

        return elements

    # ==================== MODERN STYLE ====================

    def _generate_modern_invoice(self, invoice, company, items):
        """Generate modern invoice PDF - Colorful, stylish, contemporary"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=self.margin, rightMargin=self.margin,
            topMargin=self.margin, bottomMargin=self.margin
        )

        # Modern color scheme
        PRIMARY = colors.HexColor('#1a5276')
        ACCENT = colors.HexColor('#3498db')
        LIGHT_BG = colors.HexColor('#eaf2f8')

        elements = []
        is_cancelled = getattr(invoice, 'is_cancelled', False)

        # 1. Header with colored bar
        elements.extend(self._modern_header(company, invoice, is_cancelled, PRIMARY))
        # 2. Customer & Invoice Info
        elements.extend(self._modern_customer_info(company, invoice, PRIMARY, LIGHT_BG))
        # 3. Items Table
        elements.extend(self._modern_items_table(items, invoice, PRIMARY, LIGHT_BG))
        # 4. Summary (HSN + Totals)
        elements.extend(self._modern_summary(items, invoice, PRIMARY, ACCENT, LIGHT_BG))
        # 5. Amount in Words
        elements.extend(self._modern_amount_words(invoice, LIGHT_BG))
        # 6. Footer
        elements.extend(self._modern_footer(company, invoice, PRIMARY, LIGHT_BG))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _modern_header(self, company, invoice, is_cancelled, PRIMARY):
        elements = []

        company_name = company.name.upper() if company else 'COMPANY NAME'
        elements.append(Paragraph(f"<font color='#1a5276'><b>{company_name}</b></font>", self.styles['CompanyName']))

        if company:
            details = []
            if company.address:
                details.append(company.address.replace('\n', ', '))
            if company.phone:
                details.append(f"Ph: {company.phone}")
            if company.email:
                details.append(f"Email: {company.email}")
            if details:
                elements.append(Paragraph(' | '.join(details), self.styles['CompanyInfo']))
            if company.gstin:
                elements.append(Paragraph(f"<b>GSTIN: {company.gstin}</b>", self.styles['CompanyInfo']))

        elements.append(Spacer(1, 2*mm))

        # Title bar
        title = "TAX INVOICE"
        if is_cancelled:
            title = "TAX INVOICE - CANCELLED"
            bg_color = colors.HexColor('#c0392b')
        else:
            bg_color = PRIMARY

        inv_date = invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else ''

        title_data = [[
            Paragraph(f"<font color='white'><b>{title}</b></font>", self.styles['TaxInvoice']),
            Paragraph(f"<font color='white'><b>No: {invoice.invoice_number}</b></font>", self.styles['SmallCenter']),
            Paragraph(f"<font color='white'><b>Date: {inv_date}</b></font>", self.styles['SmallCenter'])
        ]]
        title_table = Table(title_data, colWidths=[70*mm, 60*mm, 55*mm])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
        ]))
        elements.append(title_table)

        return elements

    def _modern_customer_info(self, company, invoice, PRIMARY, LIGHT_BG):
        elements = []

        customer = getattr(invoice, 'customer', None)
        customer_name = invoice.customer_name or 'Walk-in Customer'

        # Seller info
        seller_lines = []
        if company:
            seller_lines.append(f"<b>{company.name}</b>")
            if company.address:
                seller_lines.append(company.address.replace('\n', ', '))
            if company.gstin:
                seller_lines.append(f"GSTIN: {company.gstin}")
            if company.state_code:
                seller_lines.append(f"State: {get_state_name(company.state_code)} ({company.state_code})")

        # Buyer info
        buyer_lines = [f"<b>{customer_name}</b>"]
        if customer:
            if customer.address:
                buyer_lines.append(customer.address.replace('\n', ', '))
            if customer.gstin:
                buyer_lines.append(f"GSTIN: {customer.gstin}")
            if customer.state_code:
                buyer_lines.append(f"State: {get_state_name(customer.state_code)} ({customer.state_code})")
            if hasattr(customer, 'phone') and customer.phone:
                buyer_lines.append(f"Ph: {customer.phone}")

        left_cell = Paragraph(f"<font color='#1a5276'><b>From:</b></font><br/>{'<br/>'.join(seller_lines)}", self.styles['Small'])
        right_cell = Paragraph(f"<font color='#1a5276'><b>To:</b></font><br/>{'<br/>'.join(buyer_lines)}", self.styles['Small'])

        parties_table = Table([[left_cell, right_cell]], colWidths=[self.content_width/2, self.content_width/2])
        parties_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, PRIMARY),
            ('LINEBEFORE', (1, 0), (1, 0), 0.5, PRIMARY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 2*mm))

        return elements

    def _modern_items_table(self, items, invoice, PRIMARY, LIGHT_BG):
        elements = []

        headers = ['#', 'Item Description', 'Batch', 'HSN', 'Qty', 'Rate', 'GST%', 'Amount']
        col_widths = [8*mm, 58*mm, 22*mm, 16*mm, 12*mm, 22*mm, 14*mm, 28*mm]

        data = [headers]

        for i, item in enumerate(items, 1):
            qty = item.qty or 0
            rate = item.rate or 0
            gst_rate = item.gst_rate or 0
            total = item.total or 0
            batch = getattr(item, 'batch_number', '') or ''

            row = [str(i), item.product_name or '', batch, item.hsn_code or '-',
                   f"{qty:g}", f"{rate:,.2f}", f"{gst_rate:g}%", f"{total:,.2f}"]
            data.append(row)

        table = Table(data, colWidths=col_widths)

        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # # column
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),  # HSN column
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Qty, Rate, GST%, Amount - right align
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOX', (0, 0), (-1, -1), 0.5, PRIMARY),
            ('LINEBELOW', (0, 0), (-1, 0), 1, PRIMARY),
            ('INNERGRID', (0, 1), (-1, -1), 0.25, colors.HexColor('#dee2e6')),
        ]

        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), LIGHT_BG))

        table.setStyle(TableStyle(style_commands))
        elements.append(table)

        return elements

    def _modern_summary(self, items, invoice, PRIMARY, ACCENT, LIGHT_BG):
        elements = []
        elements.append(Spacer(1, 2*mm))

        # HSN Summary
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

        if has_igst:
            hsn_headers = ['HSN', 'Taxable', 'IGST']
            hsn_widths = [18*mm, 25*mm, 22*mm]
        else:
            hsn_headers = ['HSN', 'Taxable', 'CGST', 'SGST']
            hsn_widths = [15*mm, 22*mm, 18*mm, 18*mm]

        hsn_rows = [hsn_headers]
        for hsn, vals in hsn_data.items():
            if has_igst:
                hsn_rows.append([hsn, f"{vals['taxable']:,.2f}", f"{vals['igst']:,.2f}"])
            else:
                hsn_rows.append([hsn, f"{vals['taxable']:,.2f}", f"{vals['cgst']:,.2f}", f"{vals['sgst']:,.2f}"])

        hsn_table = Table(hsn_rows, colWidths=hsn_widths)
        hsn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, ACCENT),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#dee2e6')),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
        ]))

        # Totals
        totals_rows = [['Subtotal:', f"{invoice.subtotal:,.2f}"]]
        if invoice.cgst_total and invoice.cgst_total > 0:
            totals_rows.append(['CGST:', f"{invoice.cgst_total:,.2f}"])
            totals_rows.append(['SGST:', f"{invoice.sgst_total:,.2f}"])
        if invoice.igst_total and invoice.igst_total > 0:
            totals_rows.append(['IGST:', f"{invoice.igst_total:,.2f}"])
        if invoice.discount and invoice.discount > 0:
            totals_rows.append(['Discount:', f"-{invoice.discount:,.2f}"])

        totals_table = Table(totals_rows, colWidths=[28*mm, 30*mm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ]))

        # Grand Total
        grand_row = [['GRAND TOTAL:', f"Rs. {invoice.grand_total:,.2f}"]]
        grand_table = Table(grand_row, colWidths=[28*mm, 30*mm])
        grand_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))

        left_section = Table([[Paragraph("<b>HSN Summary</b>", self.styles['Small'])], [hsn_table]], colWidths=[75*mm])
        right_section = Table([[totals_table], [grand_table]], colWidths=[60*mm])

        combined = Table([[left_section, '', right_section]], colWidths=[78*mm, 40*mm, 62*mm])
        combined.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ]))
        elements.append(combined)

        return elements

    def _modern_amount_words(self, invoice, LIGHT_BG):
        elements = []
        elements.append(Spacer(1, 2*mm))

        words = number_to_words_indian(invoice.grand_total)
        amt_table = Table([[Paragraph(f"<b>Amount in Words:</b> {words}", self.styles['Small'])]],
                         colWidths=[self.content_width])
        amt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(amt_table)

        return elements

    def _modern_footer(self, company, invoice, PRIMARY, LIGHT_BG):
        elements = []
        elements.append(Spacer(1, 2*mm))

        payment_mode = getattr(invoice, 'payment_mode', 'CASH')
        payment_labels = {'CASH': 'Cash', 'CARD': 'Card', 'UPI': 'UPI', 'BANK': 'Bank Transfer', 'CREDIT': 'Credit'}

        left_lines = []
        if company and company.bank_name:
            left_lines.append(f"<font color='#1a5276'><b>Bank Details:</b></font>")
            left_lines.append(f"Bank: {company.bank_name}")
            if company.bank_account:
                left_lines.append(f"A/c No: {company.bank_account}")
            if company.bank_ifsc:
                left_lines.append(f"IFSC: {company.bank_ifsc}")
            left_lines.append("")

        left_lines.append(f"<b>Payment:</b> {payment_labels.get(payment_mode, payment_mode)}")

        terms = company.invoice_terms if company and company.invoice_terms else "Goods once sold will not be taken back. E.&O.E."
        left_lines.append("")
        left_lines.append(f"<font color='#1a5276'><b>Terms:</b></font>")
        left_lines.append(terms.replace('\n', ' '))

        left_cell = Paragraph("<br/>".join(left_lines), self.styles['Small'])

        company_name = company.name if company else 'Company'
        right_cell = Paragraph(f"for <b>{company_name}</b><br/><br/><br/><br/>_______________________<br/>Authorized Signatory", self.styles['SmallCenter'])

        footer_table = Table([[left_cell, right_cell]], colWidths=[120*mm, 60*mm])
        footer_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('LINEBEFORE', (1, 0), (1, 0), 0.5, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (0, 0), 'TOP'),
            ('VALIGN', (1, 0), (1, 0), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(footer_table)

        elements.append(Spacer(1, 1*mm))
        elements.append(Paragraph(
            "<font size='6' color='#999'>This is a computer generated invoice.</font>",
            self.styles['SmallCenter']
        ))

        return elements

    # ==================== QUOTATION & CREDIT NOTE ====================

    def generate_quotation_pdf(self, quotation, company, items):
        """Generate quotation PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=self.margin, rightMargin=self.margin,
                               topMargin=self.margin, bottomMargin=self.margin)
        elements = []

        if company and company.gstin:
            elements.append(Paragraph(f"GSTIN: {company.gstin}", self.styles['Small']))
        elements.append(Spacer(1, 2*mm))

        company_name = company.name.upper() if company else 'COMPANY NAME'
        elements.append(Paragraph(company_name, self.styles['CompanyName']))

        if company and company.address:
            elements.append(Paragraph(company.address.replace('\n', ', '), self.styles['CompanyInfo']))
        elements.append(Spacer(1, 3*mm))

        elements.append(Paragraph("<u><b>QUOTATION</b></u>", self.styles['TaxInvoice']))
        elements.append(Spacer(1, 3*mm))

        q_date = quotation.quotation_date.strftime('%d-%b-%Y') if quotation.quotation_date else ''
        valid_date = quotation.validity_date.strftime('%d-%b-%Y') if quotation.validity_date else ''

        info_data = [[
            Paragraph(f"<b>To:</b> {quotation.customer_name or 'Customer'}", self.styles['Small']),
            Paragraph(f"<b>Quotation No.:</b> {quotation.quotation_number}<br/><b>Date:</b> {q_date}<br/><b>Valid Until:</b> {valid_date}", self.styles['Small'])
        ]]
        info_table = Table(info_data, colWidths=[self.content_width/2, self.content_width/2])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 2*mm))

        headers = ['Sl.', 'Description', 'HSN', 'Qty', 'Rate', 'Amount']
        col_widths = [8*mm, 80*mm, 18*mm, 15*mm, 25*mm, 30*mm]
        data = [headers]
        for i, item in enumerate(items, 1):
            data.append([str(i), item.product_name or '', item.hsn_code or '-',
                        f"{item.qty:g}", f"{item.rate:,.2f}", f"{item.total:,.2f}"])

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 2*mm))
        totals = [
            ['Subtotal:', f"{quotation.subtotal:,.2f}"],
            ['GST:', f"{(quotation.cgst_total or 0) + (quotation.sgst_total or 0) + (quotation.igst_total or 0):,.2f}"],
            ['Total:', f"Rs. {quotation.grand_total:,.2f}"]
        ]
        totals_table = Table(totals, colWidths=[25*mm, 30*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        wrapper = Table([['', totals_table]], colWidths=[self.content_width - 60*mm, 60*mm])
        elements.append(wrapper)

        if quotation.notes:
            elements.append(Spacer(1, 3*mm))
            elements.append(Paragraph(f"<b>Notes:</b> {quotation.notes}", self.styles['Small']))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_credit_note_pdf(self, credit_note, company, items):
        """Generate credit note PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=self.margin, rightMargin=self.margin,
                               topMargin=self.margin, bottomMargin=self.margin)
        elements = []

        if company and company.gstin:
            elements.append(Paragraph(f"GSTIN: {company.gstin}", self.styles['Small']))
        elements.append(Spacer(1, 2*mm))

        company_name = company.name.upper() if company else 'COMPANY NAME'
        elements.append(Paragraph(company_name, self.styles['CompanyName']))

        if company and company.address:
            elements.append(Paragraph(company.address.replace('\n', ', '), self.styles['CompanyInfo']))
        elements.append(Spacer(1, 3*mm))

        elements.append(Paragraph("<u><b>CREDIT NOTE</b></u>", self.styles['TaxInvoice']))
        elements.append(Spacer(1, 3*mm))

        cn_date = credit_note.credit_note_date.strftime('%d-%b-%Y') if credit_note.credit_note_date else ''
        info_data = [[
            Paragraph(f"<b>To:</b> {credit_note.customer_name or 'Customer'}", self.styles['Small']),
            Paragraph(f"<b>Credit Note No.:</b> {credit_note.credit_note_number}<br/><b>Date:</b> {cn_date}<br/><b>Against Invoice:</b> {credit_note.original_invoice_number or '-'}", self.styles['Small'])
        ]]
        info_table = Table(info_data, colWidths=[self.content_width/2, self.content_width/2])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 2*mm))

        if credit_note.reason:
            elements.append(Paragraph(f"<b>Reason:</b> {credit_note.reason}", self.styles['Small']))
            elements.append(Spacer(1, 2*mm))

        headers = ['Sl.', 'Description', 'HSN', 'Qty', 'Rate', 'Amount']
        col_widths = [8*mm, 80*mm, 18*mm, 15*mm, 25*mm, 30*mm]
        data = [headers]
        for i, item in enumerate(items, 1):
            data.append([str(i), item.product_name or '', item.hsn_code or '-',
                        f"{item.qty:g}", f"{item.rate:,.2f}", f"{item.total:,.2f}"])

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 2*mm))
        totals = [
            ['Subtotal:', f"{credit_note.subtotal:,.2f}"],
            ['GST:', f"{(credit_note.cgst_total or 0) + (credit_note.sgst_total or 0) + (credit_note.igst_total or 0):,.2f}"],
            ['Credit Amount:', f"Rs. {credit_note.grand_total:,.2f}"]
        ]
        totals_table = Table(totals, colWidths=[30*mm, 30*mm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        wrapper = Table([['', totals_table]], colWidths=[self.content_width - 65*mm, 65*mm])
        elements.append(wrapper)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# Create singleton instance
pdf_generator = PDFGenerator()

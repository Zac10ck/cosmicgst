"""Weekly Invoice Summary Email Service - Sends weekly summary every Sunday"""
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


# Configuration
ADMIN_EMAIL = 'cosmicsurgical@gmail.com'
BRANCH_NAME = 'Cosmic Puthuppally'


def get_smtp_config():
    """Get SMTP configuration from environment variables"""
    return {
        'server': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        'port': int(os.environ.get('MAIL_PORT', 587)),
        'username': os.environ.get('MAIL_USERNAME', ''),
        'password': os.environ.get('MAIL_PASSWORD', ''),
        'use_tls': os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes'],
        'sender': os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME', ''))
    }


def send_weekly_summary_email():
    """
    Send weekly invoice summary email with all invoices from the past week.
    Should be called every Sunday.
    """
    from app.extensions import db
    from app.models.invoice import Invoice
    from app.models.company import Company
    from app.services.pdf_generator import pdf_generator

    try:
        config = get_smtp_config()
        if not config['username'] or not config['password']:
            print('[WEEKLY SUMMARY] SMTP not configured, skipping')
            return False

        # Calculate date range (last 7 days: Monday to Sunday)
        today = datetime.now().date()
        # If today is Sunday, get Mon-Sun of this week
        # Otherwise get Mon-Sun of last week
        days_since_monday = today.weekday()  # Monday=0, Sunday=6

        if days_since_monday == 6:  # Today is Sunday
            end_date = today
            start_date = today - timedelta(days=6)
        else:
            # Get last Sunday as end date
            days_since_sunday = (days_since_monday + 1) % 7
            end_date = today - timedelta(days=days_since_sunday)
            start_date = end_date - timedelta(days=6)

        print(f'[WEEKLY SUMMARY] Generating summary for {start_date} to {end_date}')

        # Get invoices for the week
        invoices = Invoice.get_by_date_range(start_date, end_date, include_cancelled=False)

        if not invoices:
            print('[WEEKLY SUMMARY] No invoices found for this week, skipping email')
            return True  # Not an error, just nothing to send

        company = Company.get()

        # Calculate totals
        total_subtotal = sum(inv.subtotal or 0 for inv in invoices)
        total_cgst = sum(inv.cgst_total or 0 for inv in invoices)
        total_sgst = sum(inv.sgst_total or 0 for inv in invoices)
        total_igst = sum(inv.igst_total or 0 for inv in invoices)
        total_gst = total_cgst + total_sgst + total_igst
        total_grand = sum(inv.grand_total or 0 for inv in invoices)

        # Format dates for display
        start_str = start_date.strftime('%d-%b-%Y')
        end_str = end_date.strftime('%d-%b-%Y')

        # Build email subject
        subject = f'[WEEKLY SUMMARY] {BRANCH_NAME} - Week of {start_str} to {end_str}'

        # Build invoice rows for HTML table
        invoice_rows_html = ""
        invoice_rows_text = ""
        for idx, inv in enumerate(invoices, 1):
            inv_date = inv.invoice_date.strftime('%d-%b') if inv.invoice_date else 'N/A'
            customer = inv.customer_name or 'Walk-in'
            subtotal = inv.subtotal or 0
            gst = (inv.cgst_total or 0) + (inv.sgst_total or 0) + (inv.igst_total or 0)
            grand = inv.grand_total or 0

            invoice_rows_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: center;">{idx}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; font-weight: 500;">{inv.invoice_number}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: center;">{inv_date}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{customer}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: right;">Rs. {subtotal:,.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: right;">Rs. {gst:,.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: 600;">Rs. {grand:,.2f}</td>
            </tr>
            """
            invoice_rows_text += f"  {idx}. {inv.invoice_number} | {inv_date} | {customer} | Rs.{subtotal:,.2f} | Rs.{gst:,.2f} | Rs.{grand:,.2f}\n"

        # Build HTML email body
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 20px auto; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #1565C0, #0D47A1); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 500; }}
        .header .branch {{ font-size: 28px; font-weight: bold; margin: 10px 0; }}
        .header .period {{ background: rgba(255,255,255,0.2); padding: 8px 20px; border-radius: 20px; display: inline-block; margin-top: 10px; }}
        .summary-cards {{ display: flex; justify-content: space-around; padding: 20px; background: #E3F2FD; flex-wrap: wrap; }}
        .card {{ text-align: center; padding: 15px 25px; }}
        .card .number {{ font-size: 28px; font-weight: bold; color: #1565C0; }}
        .card .label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .content {{ padding: 25px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #1565C0; color: white; padding: 12px 10px; text-align: left; font-weight: 500; }}
        th:first-child {{ border-radius: 8px 0 0 0; }}
        th:last-child {{ border-radius: 0 8px 0 0; }}
        .total-row {{ background: #E3F2FD; }}
        .total-row td {{ padding: 15px 10px; font-weight: bold; color: #1565C0; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0; }}
        .footer p {{ margin: 5px 0; color: #666; font-size: 13px; }}
        .attachment-note {{ background: #FFF3E0; border-left: 4px solid #FF9800; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Weekly Invoice Summary</h1>
            <div class="branch">{BRANCH_NAME}</div>
            <div class="period">{start_str} to {end_str}</div>
        </div>

        <div class="summary-cards">
            <div class="card">
                <div class="number">{len(invoices)}</div>
                <div class="label">Total Invoices</div>
            </div>
            <div class="card">
                <div class="number">Rs. {total_subtotal:,.2f}</div>
                <div class="label">Subtotal</div>
            </div>
            <div class="card">
                <div class="number">Rs. {total_gst:,.2f}</div>
                <div class="label">Total GST</div>
            </div>
            <div class="card">
                <div class="number">Rs. {total_grand:,.2f}</div>
                <div class="label">Grand Total</div>
            </div>
        </div>

        <div class="content">
            <h3 style="color: #1565C0; margin-bottom: 15px;">Invoice Details</h3>
            <table>
                <tr>
                    <th style="text-align: center; width: 40px;">#</th>
                    <th>Invoice No.</th>
                    <th style="text-align: center;">Date</th>
                    <th>Customer</th>
                    <th style="text-align: right;">Subtotal</th>
                    <th style="text-align: right;">GST</th>
                    <th style="text-align: right;">Total</th>
                </tr>
                {invoice_rows_html}
                <tr class="total-row">
                    <td colspan="4" style="text-align: right; padding-right: 20px;">WEEK TOTAL</td>
                    <td style="text-align: right;">Rs. {total_subtotal:,.2f}</td>
                    <td style="text-align: right;">Rs. {total_gst:,.2f}</td>
                    <td style="text-align: right; font-size: 18px;">Rs. {total_grand:,.2f}</td>
                </tr>
            </table>

            <div class="attachment-note">
                <strong>Attachments:</strong> {len(invoices)} invoice PDF(s) attached to this email.
            </div>
        </div>

        <div class="footer">
            <p><strong>{company.name if company else BRANCH_NAME}</strong></p>
            <p>{company.address if company else 'Kerala, India'}</p>
            <p>Generated on {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """

        # Build plain text body
        body_text = f"""
WEEKLY INVOICE SUMMARY
======================
{BRANCH_NAME}
Period: {start_str} to {end_str}

SUMMARY
-------
Total Invoices: {len(invoices)}
Subtotal: Rs. {total_subtotal:,.2f}
Total GST: Rs. {total_gst:,.2f}
Grand Total: Rs. {total_grand:,.2f}

INVOICE DETAILS
---------------
{invoice_rows_text}
---------------
WEEK TOTAL: Rs. {total_subtotal:,.2f} | Rs. {total_gst:,.2f} | Rs. {total_grand:,.2f}

{len(invoices)} invoice PDF(s) attached.

---
{company.name if company else BRANCH_NAME}
{company.address if company else 'Kerala, India'}
Generated on {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}
        """

        # Generate PDFs for all invoices
        pdf_attachments = []
        for invoice in invoices:
            try:
                items = list(invoice.items)
                pdf_bytes = pdf_generator.generate_invoice_pdf(invoice, company, items)
                pdf_name = f"{invoice.invoice_number.replace('/', '-')}.pdf"
                pdf_attachments.append({
                    'name': pdf_name,
                    'bytes': pdf_bytes
                })
            except Exception as e:
                print(f'[WEEKLY SUMMARY] Error generating PDF for {invoice.invoice_number}: {e}')

        # Send email with all attachments
        success = _send_email_with_attachments(
            config=config,
            recipient=ADMIN_EMAIL,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            attachments=pdf_attachments
        )

        if success:
            print(f'[WEEKLY SUMMARY] Email sent successfully to {ADMIN_EMAIL} with {len(pdf_attachments)} attachments')
        return success

    except Exception as e:
        print(f'[WEEKLY SUMMARY] Error: {e}')
        import traceback
        traceback.print_exc()
        return False


def _send_email_with_attachments(config, recipient, subject, body_html, body_text, attachments):
    """
    Send email with multiple PDF attachments.

    Args:
        config: SMTP configuration dict
        recipient: Email address
        subject: Email subject
        body_html: HTML body
        body_text: Plain text body
        attachments: List of dicts with 'name' and 'bytes' keys
    """
    try:
        # Create message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = config['sender']
        msg['To'] = recipient

        # Create alternative part for text/html
        msg_alternative = MIMEMultipart('alternative')

        # Attach plain text
        text_part = MIMEText(body_text, 'plain', 'utf-8')
        msg_alternative.attach(text_part)

        # Attach HTML
        html_part = MIMEText(body_html, 'html', 'utf-8')
        msg_alternative.attach(html_part)

        msg.attach(msg_alternative)

        # Attach all PDFs
        for attachment in attachments:
            pdf_part = MIMEApplication(attachment['bytes'], _subtype='pdf')
            pdf_part.add_header('Content-Disposition', 'attachment', filename=attachment['name'])
            msg.attach(pdf_part)

        # Connect and send
        if config['use_tls']:
            server = smtplib.SMTP(config['server'], config['port'], timeout=60)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(config['server'], config['port'], timeout=60)

        server.login(config['username'], config['password'])
        server.sendmail(config['sender'], recipient, msg.as_string())
        server.quit()

        return True

    except Exception as e:
        print(f'[WEEKLY SUMMARY] SMTP Error: {e}')
        return False


# For manual testing
if __name__ == '__main__':
    print('Running weekly summary manually...')
    send_weekly_summary_email()

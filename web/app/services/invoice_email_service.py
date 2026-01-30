"""Invoice Email Notification Service - Sends automatic emails for invoice events"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime


# Admin notification email
ADMIN_EMAIL = 'cosmicsurgical@gmail.com'


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


def send_invoice_created_email(invoice, company, pdf_bytes=None):
    """
    Send email notification when a new invoice is created.

    Args:
        invoice: Invoice model instance
        company: Company model instance
        pdf_bytes: PDF file as bytes (optional)
    """
    try:
        config = get_smtp_config()
        if not config['username'] or not config['password']:
            print(f"[EMAIL] SMTP not configured, skipping email for invoice {invoice.invoice_number}")
            return False

        # Format values
        grand_total = f"Rs. {invoice.grand_total:,.2f}" if invoice.grand_total else "Rs. 0.00"
        invoice_date = invoice.invoice_date.strftime("%d-%m-%Y") if invoice.invoice_date else datetime.now().strftime("%d-%m-%Y")
        company_name = company.name if company else "Cosmic Surgical"
        items = list(invoice.items) if hasattr(invoice, 'items') else []
        item_count = len(items)

        # Build item details for email
        item_details_html = ""
        item_details_text = ""
        for item in items:
            item_details_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{item.product_name}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{item.qty} {item.unit}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">Rs. {item.rate:,.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">Rs. {item.total:,.2f}</td>
            </tr>
            """
            item_details_text += f"  - {item.product_name}: {item.qty} {item.unit} x Rs.{item.rate:.2f} = Rs.{item.total:.2f}\n"

        # Subject
        subject = f"[NEW INVOICE] {invoice.invoice_number} - {invoice.customer_name or 'Walk-in'} - {grand_total}"

        # HTML Body
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f4f4f4; }}
        .container {{ max-width: 650px; margin: 20px auto; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #2E7D32, #1B5E20); color: white; padding: 25px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 22px; }}
        .header .invoice-num {{ font-size: 28px; font-weight: bold; margin: 10px 0; }}
        .badge {{ display: inline-block; background: #4CAF50; color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; margin-top: 10px; }}
        .content {{ padding: 25px; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }}
        .info-box {{ background: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 4px solid #2E7D32; }}
        .info-box label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .info-box value {{ font-size: 16px; font-weight: 600; color: #333; display: block; margin-top: 5px; }}
        .items-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .items-table th {{ background: #E8F5E9; color: #2E7D32; padding: 12px; text-align: left; font-weight: 600; }}
        .total-section {{ background: #E8F5E9; padding: 20px; border-radius: 8px; text-align: right; }}
        .total-section .label {{ color: #666; }}
        .total-section .amount {{ font-size: 28px; color: #2E7D32; font-weight: bold; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; border-top: 1px solid #ddd; }}
        .footer p {{ margin: 5px 0; color: #666; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Invoice Created</h1>
            <div class="invoice-num">{invoice.invoice_number}</div>
            <span class="badge">CREATED</span>
        </div>
        <div class="content">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px; margin-bottom: 20px;">
                <div class="info-box" style="flex: 1; min-width: 200px;">
                    <label>Customer</label>
                    <value>{invoice.customer_name or 'Walk-in Customer'}</value>
                </div>
                <div class="info-box" style="flex: 1; min-width: 200px;">
                    <label>Date</label>
                    <value>{invoice_date}</value>
                </div>
                <div class="info-box" style="flex: 1; min-width: 200px;">
                    <label>Payment Mode</label>
                    <value>{invoice.payment_mode or 'CASH'}</value>
                </div>
                <div class="info-box" style="flex: 1; min-width: 200px;">
                    <label>Status</label>
                    <value style="color: {'#2E7D32' if invoice.payment_status == 'PAID' else '#F44336'};">{invoice.payment_status}</value>
                </div>
            </div>

            <h3 style="color: #2E7D32; border-bottom: 2px solid #E8F5E9; padding-bottom: 10px;">Items ({item_count})</h3>
            <table class="items-table">
                <tr>
                    <th>Product</th>
                    <th style="text-align: center;">Qty</th>
                    <th style="text-align: right;">Rate</th>
                    <th style="text-align: right;">Total</th>
                </tr>
                {item_details_html}
            </table>

            <div class="total-section">
                <div class="label">Grand Total</div>
                <div class="amount">{grand_total}</div>
            </div>

            <p style="color: #666; margin-top: 20px; text-align: center;">
                <strong>PDF invoice attached to this email</strong>
            </p>
        </div>
        <div class="footer">
            <p><strong>{company_name}</strong></p>
            <p>{company.address if company else 'Kerala, India'}</p>
            <p>Generated on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """

        # Plain text body
        body_text = f"""
NEW INVOICE CREATED
===================

Invoice Number: {invoice.invoice_number}
Date: {invoice_date}
Customer: {invoice.customer_name or 'Walk-in Customer'}
Payment Mode: {invoice.payment_mode or 'CASH'}
Payment Status: {invoice.payment_status}

Items:
{item_details_text}
Subtotal: Rs. {invoice.subtotal:,.2f}
CGST: Rs. {invoice.cgst_total:,.2f}
SGST: Rs. {invoice.sgst_total:,.2f}
IGST: Rs. {invoice.igst_total:,.2f}
Discount: Rs. {invoice.discount:,.2f}

GRAND TOTAL: {grand_total}

---
{company_name}
{company.address if company else 'Kerala, India'}
        """

        # Send email
        success = _send_email(config, ADMIN_EMAIL, subject, body_html, body_text, pdf_bytes,
                             f"{invoice.invoice_number.replace('/', '-')}.pdf")

        if success:
            print(f"[EMAIL] Invoice created notification sent for {invoice.invoice_number}")
        return success

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send invoice created email: {e}")
        return False


def send_invoice_cancelled_email(invoice, company, pdf_bytes=None):
    """
    Send email notification when an invoice is cancelled.

    Args:
        invoice: Invoice model instance
        company: Company model instance
        pdf_bytes: PDF file as bytes (optional)
    """
    try:
        config = get_smtp_config()
        if not config['username'] or not config['password']:
            print(f"[EMAIL] SMTP not configured, skipping email for cancelled invoice {invoice.invoice_number}")
            return False

        # Format values
        grand_total = f"Rs. {invoice.grand_total:,.2f}" if invoice.grand_total else "Rs. 0.00"
        invoice_date = invoice.invoice_date.strftime("%d-%m-%Y") if invoice.invoice_date else "N/A"
        company_name = company.name if company else "Cosmic Surgical"
        items = list(invoice.items) if hasattr(invoice, 'items') else []
        item_count = len(items)

        # Build item details
        item_details_html = ""
        item_details_text = ""
        for item in items:
            item_details_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-decoration: line-through; color: #999;">{item.product_name}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center; text-decoration: line-through; color: #999;">{item.qty} {item.unit}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right; text-decoration: line-through; color: #999;">Rs. {item.total:,.2f}</td>
            </tr>
            """
            item_details_text += f"  - {item.product_name}: {item.qty} {item.unit} = Rs.{item.total:.2f} [CANCELLED]\n"

        # Subject
        subject = f"[CANCELLED] Invoice {invoice.invoice_number} - {invoice.customer_name or 'Walk-in'} - {grand_total}"

        # HTML Body
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f4f4f4; }}
        .container {{ max-width: 650px; margin: 20px auto; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #C62828, #B71C1C); color: white; padding: 25px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 22px; }}
        .header .invoice-num {{ font-size: 28px; font-weight: bold; margin: 10px 0; text-decoration: line-through; }}
        .badge {{ display: inline-block; background: #F44336; color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; margin-top: 10px; }}
        .content {{ padding: 25px; }}
        .warning-box {{ background: #FFEBEE; border: 1px solid #FFCDD2; border-radius: 8px; padding: 15px; margin-bottom: 20px; }}
        .warning-box p {{ margin: 0; color: #C62828; }}
        .info-box {{ background: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 4px solid #C62828; margin-bottom: 10px; }}
        .info-box label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .info-box value {{ font-size: 16px; font-weight: 600; color: #333; display: block; margin-top: 5px; }}
        .items-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; opacity: 0.7; }}
        .items-table th {{ background: #FFEBEE; color: #C62828; padding: 12px; text-align: left; font-weight: 600; }}
        .total-section {{ background: #FFEBEE; padding: 20px; border-radius: 8px; text-align: right; }}
        .total-section .label {{ color: #666; }}
        .total-section .amount {{ font-size: 28px; color: #C62828; font-weight: bold; text-decoration: line-through; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; border-top: 1px solid #ddd; }}
        .footer p {{ margin: 5px 0; color: #666; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Invoice Cancelled</h1>
            <div class="invoice-num">{invoice.invoice_number}</div>
            <span class="badge">CANCELLED</span>
        </div>
        <div class="content">
            <div class="warning-box">
                <p><strong>Important:</strong> This invoice has been cancelled. Stock has been restored and any credit balance has been adjusted.</p>
            </div>

            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px; margin-bottom: 20px;">
                <div class="info-box" style="flex: 1; min-width: 200px;">
                    <label>Customer</label>
                    <value>{invoice.customer_name or 'Walk-in Customer'}</value>
                </div>
                <div class="info-box" style="flex: 1; min-width: 200px;">
                    <label>Original Date</label>
                    <value>{invoice_date}</value>
                </div>
                <div class="info-box" style="flex: 1; min-width: 200px;">
                    <label>Cancelled On</label>
                    <value>{datetime.now().strftime('%d-%m-%Y %H:%M')}</value>
                </div>
            </div>

            <h3 style="color: #C62828; border-bottom: 2px solid #FFEBEE; padding-bottom: 10px;">Cancelled Items ({item_count})</h3>
            <table class="items-table">
                <tr>
                    <th>Product</th>
                    <th style="text-align: center;">Qty</th>
                    <th style="text-align: right;">Total</th>
                </tr>
                {item_details_html}
            </table>

            <div class="total-section">
                <div class="label">Cancelled Amount</div>
                <div class="amount">{grand_total}</div>
            </div>
        </div>
        <div class="footer">
            <p><strong>{company_name}</strong></p>
            <p>{company.address if company else 'Kerala, India'}</p>
            <p>Cancellation recorded on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """

        # Plain text body
        body_text = f"""
INVOICE CANCELLED
=================

*** THIS INVOICE HAS BEEN CANCELLED ***

Invoice Number: {invoice.invoice_number}
Original Date: {invoice_date}
Customer: {invoice.customer_name or 'Walk-in Customer'}
Cancelled On: {datetime.now().strftime('%d-%m-%Y %H:%M')}

Cancelled Items:
{item_details_text}
CANCELLED AMOUNT: {grand_total}

Note: Stock has been restored and credit balance adjusted.

---
{company_name}
{company.address if company else 'Kerala, India'}
        """

        # Send email
        success = _send_email(config, ADMIN_EMAIL, subject, body_html, body_text, pdf_bytes,
                             f"{invoice.invoice_number.replace('/', '-')}_CANCELLED.pdf")

        if success:
            print(f"[EMAIL] Invoice cancelled notification sent for {invoice.invoice_number}")
        return success

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send invoice cancelled email: {e}")
        return False


def _send_email(config, recipient, subject, body_html, body_text, pdf_bytes=None, pdf_name="document.pdf"):
    """
    Internal function to send email via SMTP.
    """
    try:
        # Create message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = config['sender']
        msg['To'] = recipient

        # Create alternative part for text/html
        msg_alternative = MIMEMultipart('alternative')

        # Attach plain text version
        text_part = MIMEText(body_text, 'plain', 'utf-8')
        msg_alternative.attach(text_part)

        # Attach HTML version
        html_part = MIMEText(body_html, 'html', 'utf-8')
        msg_alternative.attach(html_part)

        msg.attach(msg_alternative)

        # Attach PDF if provided
        if pdf_bytes:
            pdf_attachment = MIMEApplication(pdf_bytes, _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_name)
            msg.attach(pdf_attachment)

        # Connect and send
        if config['use_tls']:
            server = smtplib.SMTP(config['server'], config['port'], timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(config['server'], config['port'], timeout=30)

        server.login(config['username'], config['password'])
        server.sendmail(config['sender'], recipient, msg.as_string())
        server.quit()

        return True

    except Exception as e:
        print(f"[EMAIL ERROR] SMTP send failed: {e}")
        return False

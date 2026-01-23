"""Email sending service for Flask web application"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Tuple, Optional


class EmailService:
    """Email sending service using SMTP"""

    def __init__(self, company=None):
        """
        Initialize email service with company settings.

        Args:
            company: Company model instance with SMTP settings
        """
        self.company = company

    def is_configured(self) -> bool:
        """Check if email settings are properly configured"""
        if not self.company:
            return False
        return bool(
            self.company.smtp_server and
            self.company.smtp_username and
            self.company.smtp_password
        )

    def send_email(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        body_text: str,
        pdf_bytes: bytes = None,
        pdf_name: str = "document.pdf"
    ) -> Tuple[bool, str]:
        """
        Send an email with optional PDF attachment.

        Args:
            recipient: Email address to send to
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body content
            pdf_bytes: Optional PDF attachment as bytes
            pdf_name: Name for the PDF attachment

        Returns:
            Tuple of (success: bool, error_message: str)
        """
        if not self.is_configured():
            return False, "Email settings not configured"

        try:
            # Create message
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = self.company.email_from or self.company.smtp_username
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
                pdf_attachment.add_header(
                    'Content-Disposition', 'attachment',
                    filename=pdf_name
                )
                msg.attach(pdf_attachment)

            # Connect and send
            if self.company.smtp_use_tls:
                server = smtplib.SMTP(
                    self.company.smtp_server,
                    self.company.smtp_port,
                    timeout=30
                )
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP_SSL(
                    self.company.smtp_server,
                    self.company.smtp_port,
                    timeout=30
                )

            server.login(self.company.smtp_username, self.company.smtp_password)
            server.sendmail(msg['From'], recipient, msg.as_string())
            server.quit()

            return True, ""

        except smtplib.SMTPAuthenticationError as e:
            return False, f"Authentication failed: {str(e)}"
        except smtplib.SMTPConnectError as e:
            return False, f"Could not connect to SMTP server: {str(e)}"
        except smtplib.SMTPRecipientsRefused as e:
            return False, f"Recipient refused: {str(e)}"
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Error sending email: {str(e)}"

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test SMTP connection without sending email.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_configured():
            return False, "Email settings not configured"

        try:
            if self.company.smtp_use_tls:
                server = smtplib.SMTP(
                    self.company.smtp_server,
                    self.company.smtp_port,
                    timeout=10
                )
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP_SSL(
                    self.company.smtp_server,
                    self.company.smtp_port,
                    timeout=10
                )

            server.login(self.company.smtp_username, self.company.smtp_password)
            server.quit()

            return True, "Connection successful"

        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed. Check username and password."
        except smtplib.SMTPConnectError:
            return False, "Could not connect to SMTP server. Check server and port."
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def generate_invoice_email_content(self, invoice, company) -> dict:
        """
        Generate email content for invoice notification.

        Args:
            invoice: Invoice model instance
            company: Company model instance

        Returns:
            Dictionary with 'subject', 'body_html', 'body_text'
        """
        grand_total = f"Rs. {invoice.grand_total:,.2f}" if invoice.grand_total else "Rs. 0.00"
        items = list(invoice.items) if hasattr(invoice, 'items') else []
        item_count = len(items)

        company_name = company.name if company else "Your Company"
        company_address = company.address if company else ""
        company_gstin = company.gstin if company else "N/A"
        company_phone = company.phone if company else ""

        invoice_date = invoice.invoice_date.strftime("%d-%m-%Y") if invoice.invoice_date else "N/A"

        subject = f"Invoice {invoice.invoice_number} - {company_name}"

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1a5276; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f8f9fa; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #f0f0f0; }}
        .total-row {{ background: #e8f4f8; font-weight: bold; }}
        .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">Invoice Notification</h1>
        </div>
        <div class="content">
            <p>A new invoice has been created:</p>
            <table>
                <tr>
                    <th>Invoice Number</th>
                    <td><strong>{invoice.invoice_number}</strong></td>
                </tr>
                <tr>
                    <th>Date</th>
                    <td>{invoice_date}</td>
                </tr>
                <tr>
                    <th>Customer</th>
                    <td>{invoice.customer_name or 'Walk-in Customer'}</td>
                </tr>
                <tr>
                    <th>Items</th>
                    <td>{item_count} item(s)</td>
                </tr>
                <tr>
                    <th>Payment Status</th>
                    <td>{invoice.payment_status}</td>
                </tr>
                <tr class="total-row">
                    <th>Grand Total</th>
                    <td>{grand_total}</td>
                </tr>
            </table>
            <p>Please find the invoice PDF attached to this email.</p>
        </div>
        <div class="footer">
            <p><strong>{company_name}</strong></p>
            <p>{company_address}</p>
            <p>GSTIN: {company_gstin} | Phone: {company_phone}</p>
        </div>
    </div>
</body>
</html>
        """

        body_text = f"""
Invoice Notification
====================

A new invoice has been created:

Invoice Number: {invoice.invoice_number}
Date: {invoice_date}
Customer: {invoice.customer_name or 'Walk-in Customer'}
Items: {item_count} item(s)
Payment Status: {invoice.payment_status}
Grand Total: {grand_total}

Please find the invoice PDF attached to this email.

---
{company_name}
{company_address}
GSTIN: {company_gstin}
Phone: {company_phone}
        """

        return {
            'subject': subject,
            'body_html': body_html.strip(),
            'body_text': body_text.strip()
        }

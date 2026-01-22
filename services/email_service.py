"""Email sending service using Gmail SMTP"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Tuple, Dict, Optional
from database.db import get_connection
from database.models import Company


class EmailService:
    """Service for sending emails via Gmail SMTP"""

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    def __init__(self):
        self.sender_email: Optional[str] = None
        self.app_password: Optional[str] = None
        self.recipient_email: Optional[str] = None
        self._load_settings()

    def _load_settings(self):
        """Load email settings from app_settings table"""
        conn = get_connection()
        cursor = conn.cursor()

        settings_keys = [
            'email_sender_address',
            'email_app_password',
            'email_recipient',
        ]

        for key in settings_keys:
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                if key == 'email_sender_address':
                    self.sender_email = row['value']
                elif key == 'email_app_password':
                    self.app_password = row['value']
                elif key == 'email_recipient':
                    self.recipient_email = row['value']

        conn.close()

    def reload_settings(self):
        """Reload settings from database"""
        self._load_settings()

    def is_configured(self) -> bool:
        """Check if email settings are properly configured"""
        return bool(
            self.sender_email and
            self.app_password and
            self.recipient_email
        )

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test SMTP connection with configured credentials.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_configured():
            return False, "Email settings not configured. Please fill in all fields."

        try:
            server = smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT, timeout=10)
            server.starttls()
            server.login(self.sender_email, self.app_password)
            server.quit()
            return True, "Connection successful! Email settings are working."
        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed. Please check your email and app password."
        except smtplib.SMTPConnectError:
            return False, "Could not connect to Gmail SMTP server. Check your internet connection."
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def send_email(
        self,
        recipient: str,
        subject: str,
        body_html: str,
        body_text: str,
        pdf_bytes: bytes = None,
        pdf_name: str = "invoice.pdf"
    ) -> Tuple[bool, str]:
        """
        Send an email with optional PDF attachment.

        Args:
            recipient: Email recipient address
            subject: Email subject line
            body_html: HTML version of email body
            body_text: Plain text version of email body
            pdf_bytes: PDF file content as bytes (optional)
            pdf_name: Name for the PDF attachment

        Returns:
            Tuple of (success: bool, error_message: str)
        """
        if not self.is_configured():
            return False, "Email settings not configured"

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient

            # Attach text and HTML versions
            part_text = MIMEText(body_text, 'plain')
            part_html = MIMEText(body_html, 'html')

            msg.attach(part_text)
            msg.attach(part_html)

            # Attach PDF if provided
            if pdf_bytes:
                pdf_attachment = MIMEApplication(pdf_bytes, _subtype='pdf')
                pdf_attachment.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=pdf_name
                )
                msg.attach(pdf_attachment)

            # Send email
            server = smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT, timeout=30)
            server.starttls()
            server.login(self.sender_email, self.app_password)
            server.sendmail(self.sender_email, recipient, msg.as_string())
            server.quit()

            return True, ""

        except smtplib.SMTPAuthenticationError:
            return False, "Authentication failed. Check email credentials."
        except smtplib.SMTPRecipientsRefused:
            return False, f"Recipient address rejected: {recipient}"
        except smtplib.SMTPConnectError:
            return False, "Could not connect to email server."
        except smtplib.SMTPServerDisconnected:
            return False, "Server disconnected unexpectedly."
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Error sending email: {str(e)}"

    def generate_invoice_email_content(self, invoice) -> Dict:
        """
        Generate email subject and body content for an invoice.

        Args:
            invoice: Invoice object with invoice data

        Returns:
            Dict with 'subject', 'body_html', 'body_text' keys
        """
        # Get company details
        company = Company.get()

        company_name = company.name if company else "Our Company"
        company_address = company.address if company else ""
        company_gstin = company.gstin if company else ""
        company_phone = company.phone if company else ""

        # Format grand total
        grand_total = f"Rs. {invoice.grand_total:,.2f}"

        # Count items
        item_count = len(invoice.items) if hasattr(invoice, 'items') and invoice.items else 0

        # Subject line
        subject = f"Invoice {invoice.invoice_number} from {company_name}"

        # HTML email body
        body_html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; }}
        .header {{ background: #1a5276; color: white; padding: 20px; text-align: center; }}
        .header h2 {{ margin: 0; }}
        .content {{ padding: 20px; }}
        .invoice-details {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .invoice-details table {{ width: 100%; border-collapse: collapse; }}
        .invoice-details td {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .invoice-details td:last-child {{ text-align: right; font-weight: 500; }}
        .total-row td {{ border-bottom: none; font-size: 18px; font-weight: bold; color: #1a5276; padding-top: 12px; }}
        .footer {{ padding: 20px; text-align: center; color: #7f8c8d; font-size: 12px; border-top: 1px solid #eee; margin-top: 20px; }}
        .btn {{ display: inline-block; background: #1a5276; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>{company_name}</h2>
    </div>
    <div class="content">
        <p>Dear Customer,</p>
        <p>Thank you for your purchase. Please find your invoice attached to this email.</p>

        <div class="invoice-details">
            <table>
                <tr>
                    <td><strong>Invoice Number</strong></td>
                    <td>{invoice.invoice_number}</td>
                </tr>
                <tr>
                    <td><strong>Date</strong></td>
                    <td>{invoice.invoice_date}</td>
                </tr>
                <tr>
                    <td><strong>Customer</strong></td>
                    <td>{invoice.customer_name}</td>
                </tr>
                <tr>
                    <td><strong>Items</strong></td>
                    <td>{item_count} item(s)</td>
                </tr>
                <tr class="total-row">
                    <td>Grand Total</td>
                    <td>{grand_total}</td>
                </tr>
            </table>
        </div>

        <p>If you have any questions about this invoice, please don't hesitate to contact us.</p>

        <p>Thank you for your business!</p>
    </div>
    <div class="footer">
        <p><strong>{company_name}</strong></p>
        <p>{company_address}</p>
        <p>GSTIN: {company_gstin} | Phone: {company_phone}</p>
    </div>
</body>
</html>"""

        # Plain text email body
        body_text = f"""{company_name}
{'=' * len(company_name)}

Invoice Notification

Dear Customer,

Thank you for your purchase. Please find your invoice attached.

Invoice Details:
----------------
Invoice Number: {invoice.invoice_number}
Date: {invoice.invoice_date}
Customer: {invoice.customer_name}
Items: {item_count} item(s)

Grand Total: {grand_total}

If you have any questions about this invoice, please contact us.

Thank you for your business!

---
{company_name}
{company_address}
GSTIN: {company_gstin}
Phone: {company_phone}
"""

        return {
            'subject': subject,
            'body_html': body_html,
            'body_text': body_text
        }


def get_email_setting(key: str, default: str = "") -> str:
    """
    Get a single email setting value.

    Args:
        key: Setting key name
        default: Default value if not found

    Returns:
        Setting value or default
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()

    return row['value'] if row else default


def set_email_setting(key: str, value: str):
    """
    Set a single email setting value.

    Args:
        key: Setting key name
        value: Setting value
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()


def is_email_auto_send_enabled() -> bool:
    """Check if auto-send on invoice creation is enabled"""
    enabled = get_email_setting('email_enabled', 'false')
    auto_send = get_email_setting('email_auto_send', 'false')
    return enabled == 'true' and auto_send == 'true'

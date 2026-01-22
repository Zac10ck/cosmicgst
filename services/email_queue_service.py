"""Email queue management service for offline support"""
from datetime import datetime
from typing import List, Dict, Optional
from database.db import get_connection
from services.email_service import EmailService, get_email_setting
from services.pdf_generator import PDFGenerator


# Queue status constants
STATUS_PENDING = 'PENDING'
STATUS_SENDING = 'SENDING'
STATUS_SENT = 'SENT'
STATUS_FAILED = 'FAILED'

# Retry settings
MAX_RETRIES = 3


class EmailQueueService:
    """Service for managing the email queue with offline support"""

    def __init__(self):
        self.email_service = EmailService()
        self.pdf_generator = PDFGenerator()

    def queue_invoice_email(self, invoice) -> Optional[int]:
        """
        Add an invoice email to the queue.

        Args:
            invoice: Invoice object to email

        Returns:
            Queue entry ID if successful, None otherwise
        """
        # Get recipient email from settings
        recipient = get_email_setting('email_recipient', '')
        if not recipient:
            return None

        # Generate email content
        email_content = self.email_service.generate_invoice_email_content(invoice)

        # Generate PDF
        try:
            pdf_bytes = self.pdf_generator.generate_invoice_pdf(invoice)
        except Exception:
            pdf_bytes = None

        # Insert into queue
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO email_queue (
                invoice_id, recipient_email, subject, body, pdf_data, status
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            invoice.id,
            recipient,
            email_content['subject'],
            email_content['body_html'],
            pdf_bytes,
            STATUS_PENDING
        ))

        queue_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return queue_id

    def get_pending_emails(self) -> List[Dict]:
        """
        Get all emails that are pending or ready for retry.

        Returns:
            List of queue entries as dictionaries
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, invoice_id, recipient_email, subject, body, pdf_data,
                   status, retry_count, error_message, created_at
            FROM email_queue
            WHERE status = ? OR (status = ? AND retry_count < ?)
            ORDER BY created_at ASC
        """, (STATUS_PENDING, STATUS_FAILED, MAX_RETRIES))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def process_single_email(self, queue_id: int) -> bool:
        """
        Process a single queued email.

        Args:
            queue_id: ID of the queue entry to process

        Returns:
            True if sent successfully, False otherwise
        """
        # Get queue entry
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, invoice_id, recipient_email, subject, body, pdf_data,
                   status, retry_count
            FROM email_queue WHERE id = ?
        """, (queue_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        entry = dict(row)
        conn.close()

        # Mark as sending
        self._update_status(queue_id, STATUS_SENDING)

        # Reload email service settings
        self.email_service.reload_settings()

        # Get plain text version from HTML (simplified)
        body_text = self._html_to_text(entry['body'])

        # Generate PDF filename
        pdf_name = f"Invoice_{entry['invoice_id']}.pdf"

        # Try to send
        success, error_msg = self.email_service.send_email(
            recipient=entry['recipient_email'],
            subject=entry['subject'],
            body_html=entry['body'],
            body_text=body_text,
            pdf_bytes=entry['pdf_data'],
            pdf_name=pdf_name
        )

        if success:
            self.mark_as_sent(queue_id)
            return True
        else:
            self.mark_as_failed(queue_id, error_msg)
            return False

    def _html_to_text(self, html: str) -> str:
        """Simple HTML to plain text conversion"""
        import re
        # Remove style tags and content
        text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

    def process_queue(self) -> Dict:
        """
        Process all pending emails in the queue.

        Returns:
            Dict with 'sent', 'failed', 'remaining' counts
        """
        pending = self.get_pending_emails()

        sent = 0
        failed = 0

        for entry in pending:
            if self.process_single_email(entry['id']):
                sent += 1
            else:
                failed += 1

        # Get remaining count
        remaining = self.get_pending_count()

        return {
            'sent': sent,
            'failed': failed,
            'remaining': remaining
        }

    def mark_as_sent(self, queue_id: int):
        """Mark a queue entry as successfully sent"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE email_queue
            SET status = ?, sent_at = ?, error_message = NULL
            WHERE id = ?
        """, (STATUS_SENT, datetime.now(), queue_id))

        conn.commit()
        conn.close()

    def mark_as_failed(self, queue_id: int, error_message: str):
        """
        Mark a queue entry as failed and increment retry count.

        Args:
            queue_id: Queue entry ID
            error_message: Error description
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Get current retry count
        cursor.execute("SELECT retry_count FROM email_queue WHERE id = ?", (queue_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        new_retry_count = row['retry_count'] + 1

        # Determine new status
        if new_retry_count >= MAX_RETRIES:
            new_status = STATUS_FAILED
        else:
            new_status = STATUS_FAILED  # Will be retried on next process cycle

        cursor.execute("""
            UPDATE email_queue
            SET status = ?, retry_count = ?, error_message = ?
            WHERE id = ?
        """, (new_status, new_retry_count, error_message, queue_id))

        conn.commit()
        conn.close()

    def _update_status(self, queue_id: int, status: str):
        """Update queue entry status"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE email_queue SET status = ? WHERE id = ?",
            (status, queue_id)
        )
        conn.commit()
        conn.close()

    def get_queue_status(self) -> Dict:
        """
        Get queue statistics.

        Returns:
            Dict with 'pending', 'failed', 'sent' counts
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM email_queue
            GROUP BY status
        """)

        rows = cursor.fetchall()
        conn.close()

        result = {'pending': 0, 'failed': 0, 'sent': 0}

        for row in rows:
            status = row['status']
            count = row['count']

            if status == STATUS_PENDING or status == STATUS_SENDING:
                result['pending'] += count
            elif status == STATUS_FAILED:
                result['failed'] += count
            elif status == STATUS_SENT:
                result['sent'] += count

        return result

    def get_pending_count(self) -> int:
        """Get count of pending emails (including retryable failed ones)"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as count FROM email_queue
            WHERE status = ? OR (status = ? AND retry_count < ?)
        """, (STATUS_PENDING, STATUS_FAILED, MAX_RETRIES))

        row = cursor.fetchone()
        conn.close()

        return row['count'] if row else 0

    def get_failed_count(self) -> int:
        """Get count of permanently failed emails"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as count FROM email_queue
            WHERE status = ? AND retry_count >= ?
        """, (STATUS_FAILED, MAX_RETRIES))

        row = cursor.fetchone()
        conn.close()

        return row['count'] if row else 0

    def retry_failed(self, queue_id: int) -> bool:
        """
        Manually retry a failed email.

        Args:
            queue_id: Queue entry ID to retry

        Returns:
            True if email was sent successfully
        """
        # Reset retry count and status
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE email_queue
            SET status = ?, retry_count = 0, error_message = NULL
            WHERE id = ?
        """, (STATUS_PENDING, queue_id))

        conn.commit()
        conn.close()

        # Process immediately
        return self.process_single_email(queue_id)

    def delete_from_queue(self, queue_id: int):
        """Remove an entry from the queue"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_queue WHERE id = ?", (queue_id,))
        conn.commit()
        conn.close()

    def get_queue_entries(self, limit: int = 50) -> List[Dict]:
        """
        Get recent queue entries for display.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of queue entries
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT eq.id, eq.invoice_id, eq.recipient_email, eq.subject,
                   eq.status, eq.retry_count, eq.error_message,
                   eq.created_at, eq.sent_at,
                   i.invoice_number
            FROM email_queue eq
            LEFT JOIN invoices i ON eq.invoice_id = i.id
            ORDER BY eq.created_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

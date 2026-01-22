"""Background email queue processor with thread-safe UI updates"""
import threading
import time
from typing import Optional, Callable, Dict, Any
from services.email_queue_service import EmailQueueService
from services.network_service import NetworkService


class EmailQueueProcessor:
    """
    Background processor for email queue.

    Runs in a daemon thread, periodically checking for pending emails
    and processing them when internet is available.
    """

    # Default check interval in seconds
    DEFAULT_CHECK_INTERVAL = 60

    def __init__(self, app_reference=None):
        """
        Initialize the processor.

        Args:
            app_reference: Reference to the main app for thread-safe UI updates.
                          Must have an 'after' method (CustomTkinter/Tkinter app).
        """
        self.app = app_reference
        self.queue_service = EmailQueueService()
        self.network_service = NetworkService()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._check_interval = self.DEFAULT_CHECK_INTERVAL
        self._lock = threading.Lock()

        # Callbacks for UI updates
        self._callbacks: Dict[str, Optional[Callable]] = {
            'on_email_sent': None,
            'on_email_failed': None,
            'on_queue_processed': None,
            'on_connection_status_changed': None,
        }

        # Track connection status for change detection
        self._last_connection_status: Optional[bool] = None

    def start(self):
        """Start the background processing thread"""
        with self._lock:
            if self._running:
                return

            self._running = True
            self._thread = threading.Thread(target=self._process_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the background processing thread"""
        with self._lock:
            self._running = False

        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def is_running(self) -> bool:
        """Check if processor is running"""
        with self._lock:
            return self._running

    def set_callback(self, event: str, callback: Optional[Callable]):
        """
        Set a callback for an event.

        Events:
            - on_email_sent: Called when an email is sent. Args: (queue_id, invoice_number)
            - on_email_failed: Called when an email fails. Args: (queue_id, error_message)
            - on_queue_processed: Called after queue processing. Args: (result_dict)
            - on_connection_status_changed: Called when connection status changes. Args: (is_online)

        Args:
            event: Event name
            callback: Callback function (will be called on main thread)
        """
        self._callbacks[event] = callback

    def set_check_interval(self, seconds: int):
        """Set the interval between queue checks"""
        self._check_interval = max(10, seconds)  # Minimum 10 seconds

    def _process_loop(self):
        """Main background processing loop"""
        while True:
            with self._lock:
                if not self._running:
                    break

            try:
                # Check connection status
                is_online = self.network_service.is_online()

                # Notify if connection status changed
                if self._last_connection_status is not None and is_online != self._last_connection_status:
                    self._notify_ui('on_connection_status_changed', is_online)

                self._last_connection_status = is_online

                # Process queue if online
                if is_online:
                    pending_count = self.queue_service.get_pending_count()

                    if pending_count > 0:
                        result = self.queue_service.process_queue()

                        if result['sent'] > 0 or result['failed'] > 0:
                            self._notify_ui('on_queue_processed', result)

            except Exception:
                # Silently handle errors in background thread
                pass

            # Sleep in small intervals to allow quick shutdown
            sleep_time = 0
            while sleep_time < self._check_interval:
                with self._lock:
                    if not self._running:
                        return
                time.sleep(1)
                sleep_time += 1

    def _notify_ui(self, event: str, data: Any):
        """
        Notify UI of an event (thread-safe).

        Uses app.after() to schedule callback on main thread.
        """
        callback = self._callbacks.get(event)
        if callback and self.app:
            try:
                # Schedule callback on main thread
                self.app.after(0, lambda: callback(data))
            except Exception:
                # App may have been destroyed
                pass

    def process_now(self) -> Dict:
        """
        Trigger immediate queue processing.

        Can be called from main thread. Returns result immediately.

        Returns:
            Dict with 'sent', 'failed', 'remaining' counts
        """
        if not self.network_service.is_online():
            return {'sent': 0, 'failed': 0, 'remaining': self.queue_service.get_pending_count()}

        return self.queue_service.process_queue()

    def get_status(self) -> Dict:
        """
        Get current processor status.

        Returns:
            Dict with status information
        """
        is_online = self.network_service.is_online(force_check=True)
        queue_status = self.queue_service.get_queue_status()

        return {
            'running': self.is_running(),
            'online': is_online,
            'pending': queue_status['pending'],
            'failed': queue_status['failed'],
            'sent': queue_status['sent'],
        }

    def get_pending_count(self) -> int:
        """Get count of pending emails"""
        return self.queue_service.get_pending_count()

    def get_failed_count(self) -> int:
        """Get count of permanently failed emails"""
        return self.queue_service.get_failed_count()

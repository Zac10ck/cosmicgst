"""Network connectivity detection service"""
import socket
import time
from typing import Optional


class NetworkService:
    """Service to check network/internet connectivity"""

    # Gmail SMTP server details
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587

    # Fallback hosts to check
    FALLBACK_HOSTS = [
        ("www.google.com", 443),
        ("www.cloudflare.com", 443),
    ]

    # Cache settings
    CACHE_DURATION = 30  # seconds

    def __init__(self):
        self._is_online: Optional[bool] = None
        self._last_check: Optional[float] = None

    def is_online(self, force_check: bool = False) -> bool:
        """
        Check if internet is available.

        Uses cached result if available and not expired.

        Args:
            force_check: If True, bypass cache and check now

        Returns:
            True if internet is available, False otherwise
        """
        current_time = time.time()

        # Return cached result if valid
        if not force_check and self._is_online is not None and self._last_check is not None:
            if current_time - self._last_check < self.CACHE_DURATION:
                return self._is_online

        # Perform actual check
        self._is_online = self._check_connectivity()
        self._last_check = current_time

        return self._is_online

    def _check_connectivity(self) -> bool:
        """
        Perform actual connectivity check.

        First tries SMTP server, then fallback hosts.

        Returns:
            True if any host is reachable, False otherwise
        """
        # Try SMTP server first
        if self._check_host(self.SMTP_HOST, self.SMTP_PORT):
            return True

        # Try fallback hosts
        for host, port in self.FALLBACK_HOSTS:
            if self._check_host(host, port):
                return True

        return False

    def _check_host(self, host: str, port: int, timeout: float = 3.0) -> bool:
        """
        Check if a specific host:port is reachable.

        Args:
            host: Hostname or IP address
            port: Port number
            timeout: Connection timeout in seconds

        Returns:
            True if reachable, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except (socket.error, socket.timeout, OSError):
            return False

    def check_smtp_reachable(self) -> bool:
        """
        Check if Gmail SMTP server is reachable.

        Returns:
            True if SMTP server is reachable, False otherwise
        """
        return self._check_host(self.SMTP_HOST, self.SMTP_PORT)

    def invalidate_cache(self):
        """Clear the cached connectivity status"""
        self._is_online = None
        self._last_check = None

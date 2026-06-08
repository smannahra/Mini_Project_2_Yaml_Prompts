import ipaddress
from urllib.parse import urlparse

from app.exceptions import BlockedUrlError, InvalidUrlError

# REQ-SHORT-005 / NFR-002
MAX_URL_LENGTH = 2048

_BLOCKLIST = frozenset({
    "malware.com",
    "phishing-site.net",
    "evil.ru",
    "scam-domain.xyz",
})

# Hostnames that always resolve to private/loopback addresses
_PRIVATE_HOSTNAMES = frozenset({"localhost", "localhost."})


def _is_private_host(hostname: str) -> bool:
    """Return True if hostname is a private/loopback/link-local IP address."""
    if hostname in _PRIVATE_HOSTNAMES:
        return True
    try:
        addr = ipaddress.ip_address(hostname)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved
    except ValueError:
        return False


def validate_url_format(url: str) -> None:
    if not url:
        raise InvalidUrlError("Invalid URL format")

    # Fix 1: URL length cap — prevents memory/CPU amplification
    if len(url) > MAX_URL_LENGTH:
        raise InvalidUrlError("Invalid URL format")

    # Fix 2: CRLF check — prevents HTTP response splitting via Location header
    if "\r" in url or "\n" in url:
        raise InvalidUrlError("Invalid URL format")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InvalidUrlError("Invalid URL format")


def check_blocklist(url: str) -> None:
    hostname = urlparse(url).hostname or ""

    # Fix 3: Private IP blocking — prevents open-redirect abuse to internal resources
    if _is_private_host(hostname):
        raise BlockedUrlError("Malicious URL detected")

    if hostname in _BLOCKLIST or any(
        hostname.endswith("." + domain) for domain in _BLOCKLIST
    ):
        raise BlockedUrlError("Malicious URL detected")

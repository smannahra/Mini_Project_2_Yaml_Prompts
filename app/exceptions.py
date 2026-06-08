class InvalidUrlError(ValueError):
    """Raised when a URL fails format or safety validation."""


class BlockedUrlError(ValueError):
    """Raised when a URL matches the malicious-domain or private-IP blocklist."""

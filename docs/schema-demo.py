"""
docs/schema-demo.py

JSON Schema validation demo for ShortenResponse.
Mirrors the constraints declared in specs/url-shortener.yaml and
implemented by app/schemas.py :: ShortenResponse.

Note on date-time format:
  jsonschema's FormatChecker validates "date-time" against RFC 3339, which
  REQUIRES a timezone offset (e.g. +00:00 or Z). The current app serialises
  naive datetimes via datetime.utcnow(), so we use an explicit ISO 8601
  regex pattern that accepts both naive and timezone-aware forms. Switching
  the app to datetime.now(timezone.utc) would let us use "format":"date-time"
  strictly — that change is already recommended in the security review.

Run:
    python docs/schema-demo.py
"""

import json

from jsonschema import Draft202012Validator, FormatChecker

# ---------------------------------------------------------------------------
# Reusable date-time pattern (ISO 8601, naive or timezone-aware)
# ---------------------------------------------------------------------------
# Accepts:
#   2026-06-08T12:00:00
#   2026-06-08T12:00:00.123456
#   2026-06-08T12:00:00Z
#   2026-06-08T12:00:00+00:00
_ISO8601_PATTERN = (
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(\.\d+)?"
    r"(Z|[+-]\d{2}:\d{2})?$"
)

# ---------------------------------------------------------------------------
# Schema definition
# ---------------------------------------------------------------------------

SHORTEN_RESPONSE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ShortenResponse",
    "description": (
        "Response body for POST /api/shorten. "
        "Covers REQ-SHORT-001 (short code format), "
        "REQ-SHORT-004 (expiry), REQ-SHORT-006 (API contract)."
    ),
    "type": "object",
    "required": ["short_code", "short_url", "url", "created_at"],
    "additionalProperties": False,
    "properties": {
        "short_code": {
            # REQ-SHORT-001: exactly 6 alphanumeric characters
            "type": "string",
            "minLength": 6,
            "maxLength": 6,
            "pattern": "^[A-Za-z0-9]{6}$",
            "description": "6-character alphanumeric short code (REQ-SHORT-001)",
            "examples": ["abc123", "X9pQrT"],
        },
        "short_url": {
            # Must carry a usable scheme so clients can open it directly
            "type": "string",
            "pattern": "^https?://",
            "description": "Fully-qualified short URL including scheme and host",
            "examples": ["http://localhost:8000/abc123"],
        },
        "url": {
            "type": "string",
            "description": "Original long URL submitted by the client",
        },
        "created_at": {
            # ISO 8601 datetime, naive or timezone-aware (see module docstring)
            "type": "string",
            "pattern": _ISO8601_PATTERN,
            "description": "Creation timestamp in ISO 8601 format",
        },
        "expiry_date": {
            # REQ-SHORT-004: null means no expiry
            "type": ["string", "null"],
            "pattern": _ISO8601_PATTERN,   # only validated when value is a string
            "description": "Optional expiry in ISO 8601 format; null means no expiry (REQ-SHORT-004)",
        },
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SEP = "-" * 60


def _section(title: str) -> None:
    print(f"\n{_SEP}\n  {title}\n{_SEP}")


def validate_sample(label: str, instance: dict, expect_valid: bool = True) -> None:
    validator = Draft202012Validator(
        SHORTEN_RESPONSE_SCHEMA,
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    status = "PASS" if not errors else "FAIL"

    print(f"\n[{status}] {label}")
    print("  Input :", json.dumps(instance))

    if errors:
        for err in errors:
            path = " -> ".join(str(p) for p in err.absolute_path) or "(root)"
            print(f"  !  Field '{path}': {err.message}")
    else:
        print("  Result: all constraints satisfied.")

    if expect_valid and errors:
        print("  ** Schema or sample mismatch — review needed.")
    if not expect_valid and not errors:
        print("  ** Expected a violation but found none — review schema.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Print the schema
    _section("JSON SCHEMA  (ShortenResponse)")
    print(json.dumps(SHORTEN_RESPONSE_SCHEMA, indent=2))

    # 2. Valid samples
    _section("VALID SAMPLES")

    validate_sample(
        label="Minimal valid response — no expiry (matches app output today)",
        instance={
            "short_code": "abc123",
            "short_url": "http://localhost:8000/abc123",
            "url": "https://www.example.com/very/long/path?ref=newsletter",
            "created_at": "2026-06-08T12:00:00",
            "expiry_date": None,
        },
        expect_valid=True,
    )

    validate_sample(
        label="Response with timezone-aware timestamps and fractional seconds",
        instance={
            "short_code": "X9pQrT",
            "short_url": "https://short.example.com/X9pQrT",
            "url": "https://docs.python.org/3/library/datetime.html",
            "created_at": "2026-06-08T09:30:00.123456+00:00",
            "expiry_date": "2099-12-31T23:59:59+00:00",
        },
        expect_valid=True,
    )

    validate_sample(
        label="Response with Z-suffix UTC timestamps",
        instance={
            "short_code": "z1A2b3",
            "short_url": "https://short.example.com/z1A2b3",
            "url": "https://www.wikipedia.org/wiki/URL_shortening",
            "created_at": "2026-06-08T00:00:00Z",
            "expiry_date": None,
        },
        expect_valid=True,
    )

    # 3. Invalid samples — each targets one specific constraint
    _section("INVALID SAMPLES  (each violates exactly one constraint)")

    validate_sample(
        label="short_code is 5 characters (minLength: 6)",
        instance={
            "short_code": "abc12",
            "short_url": "http://localhost:8000/abc12",
            "url": "https://example.com",
            "created_at": "2026-06-08T12:00:00",
            "expiry_date": None,
        },
        expect_valid=False,
    )

    validate_sample(
        label="short_code contains underscore (pattern: [A-Za-z0-9] only)",
        instance={
            "short_code": "ab_123",
            "short_url": "http://localhost:8000/ab_123",
            "url": "https://example.com",
            "created_at": "2026-06-08T12:00:00",
            "expiry_date": None,
        },
        expect_valid=False,
    )

    validate_sample(
        label="short_url uses ftp:// scheme (pattern: ^https?://)",
        instance={
            "short_code": "abc123",
            "short_url": "ftp://short.example.com/abc123",
            "url": "https://example.com",
            "created_at": "2026-06-08T12:00:00",
            "expiry_date": None,
        },
        expect_valid=False,
    )

    validate_sample(
        label="created_at is not ISO 8601 (DD-MM-YYYY HH:MM format rejected)",
        instance={
            "short_code": "abc123",
            "short_url": "http://localhost:8000/abc123",
            "url": "https://example.com",
            "created_at": "08-06-2026 12:00",
            "expiry_date": None,
        },
        expect_valid=False,
    )

    validate_sample(
        label="expiry_date is a free-text string (not ISO 8601)",
        instance={
            "short_code": "abc123",
            "short_url": "http://localhost:8000/abc123",
            "url": "https://example.com",
            "created_at": "2026-06-08T12:00:00",
            "expiry_date": "next tuesday",
        },
        expect_valid=False,
    )

    validate_sample(
        label="required field 'url' is absent",
        instance={
            "short_code": "abc123",
            "short_url": "http://localhost:8000/abc123",
            "created_at": "2026-06-08T12:00:00",
            "expiry_date": None,
        },
        expect_valid=False,
    )

    validate_sample(
        label="unexpected additional property 'admin_token' (additionalProperties: false)",
        instance={
            "short_code": "abc123",
            "short_url": "http://localhost:8000/abc123",
            "url": "https://example.com",
            "created_at": "2026-06-08T12:00:00",
            "expiry_date": None,
            "admin_token": "secret",
        },
        expect_valid=False,
    )

    _section("Demo complete.")


if __name__ == "__main__":
    main()

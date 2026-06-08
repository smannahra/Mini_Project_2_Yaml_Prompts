import secrets
import string

_ALPHABET = string.ascii_letters + string.digits  # 62 chars → 56B combinations


def generate_short_code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(6))

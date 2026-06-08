from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Url
from app.utils.code_generator import generate_short_code
from app.utils.validators import validate_url_format, check_blocklist


def shorten_url(
    db: Session, url: str, expiry_date: datetime | None
) -> tuple[Url, bool]:
    """Return (url_record, is_new). Raises ValueError for invalid/blocked URLs."""
    validate_url_format(url)
    check_blocklist(url)

    existing = db.query(Url).filter(Url.original_url == url).first()
    if existing:
        return existing, False

    for _ in range(10):
        code = generate_short_code()
        if not db.query(Url).filter(Url.short_code == code).first():
            break
    else:
        raise RuntimeError("Failed to generate a unique short code after 10 attempts")

    record = Url(
        short_code=code,
        original_url=url,
        created_at=datetime.utcnow(),
        expiry_date=expiry_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, True


def lookup_url(db: Session, short_code: str) -> Url | None:
    return db.query(Url).filter(Url.short_code == short_code).first()


def delete_url(db: Session, short_code: str) -> bool:
    record = lookup_url(db, short_code)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True

from datetime import datetime
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Url, ClickEvent


def record_click(db: Session, url: Url, referrer: str | None) -> None:
    # Atomic increment — avoids read-modify-write race
    db.execute(
        update(Url)
        .where(Url.id == url.id)
        .values(click_count=Url.click_count + 1, last_accessed=datetime.utcnow())
    )
    db.add(ClickEvent(url_id=url.id, referrer=referrer, accessed_at=datetime.utcnow()))
    db.commit()


def get_analytics(db: Session, short_code: str) -> dict | None:
    url = db.query(Url).filter(Url.short_code == short_code).first()
    if not url:
        return None

    rows = (
        db.query(ClickEvent.referrer)
        .filter(ClickEvent.url_id == url.id, ClickEvent.referrer.isnot(None))
        .distinct()
        .all()
    )

    return {
        "short_code": url.short_code,
        "click_count": url.click_count,
        "last_accessed": url.last_accessed,
        "referrers": [r[0] for r in rows],
    }

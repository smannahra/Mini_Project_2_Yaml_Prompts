from datetime import datetime

from app.models import ClickEvent, Url


def _seed(db, short_code="abc123", url="https://example.com", expiry_date=None):
    record = Url(
        short_code=short_code,
        original_url=url,
        created_at=datetime.utcnow(),
        expiry_date=expiry_date,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_redirect_valid(client, db):
    """SCENARIO-002: Valid short code → 302 with Location header."""
    _seed(db)
    resp = client.get("/abc123", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "https://example.com"


def test_redirect_increments_click_count(client, db):
    """SCENARIO-002: click_count increments on each redirect."""
    _seed(db)
    client.get("/abc123", follow_redirects=False)
    client.get("/abc123", follow_redirects=False)
    db.expire_all()
    url = db.query(Url).filter_by(short_code="abc123").first()
    assert url.click_count == 2


def test_redirect_updates_last_accessed(client, db):
    """SCENARIO-003: last_accessed timestamp updates on redirect."""
    _seed(db)
    assert db.query(Url).filter_by(short_code="abc123").first().last_accessed is None
    client.get("/abc123", follow_redirects=False)
    db.expire_all()
    url = db.query(Url).filter_by(short_code="abc123").first()
    assert url.last_accessed is not None


def test_redirect_captures_referrer(client, db):
    """SCENARIO-003: Referer header is stored in click_events."""
    _seed(db)
    client.get("/abc123", headers={"Referer": "https://google.com"}, follow_redirects=False)
    event = db.query(ClickEvent).first()
    assert event.referrer == "https://google.com"


def test_redirect_expired_returns_410(client, db):
    """SCENARIO-004: Expired URL → 410 Gone."""
    _seed(db, short_code="exp123", expiry_date=datetime(2020, 1, 1))
    resp = client.get("/exp123", follow_redirects=False)
    assert resp.status_code == 410
    assert resp.json()["error"] == "URL has expired"


def test_redirect_unknown_code_returns_404(client, db):
    """SCENARIO-007: Unknown short code → 404 Not Found."""
    resp = client.get("/xyz999", follow_redirects=False)
    assert resp.status_code == 404
    assert resp.json()["error"] == "Short code not found"

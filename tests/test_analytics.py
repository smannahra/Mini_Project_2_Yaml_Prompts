from datetime import datetime

from app.models import ClickEvent, Url


def _seed_with_clicks(db, short_code="abc123", click_count=10):
    url = Url(
        short_code=short_code,
        original_url="https://example.com",
        created_at=datetime.utcnow(),
        click_count=click_count,
        last_accessed=datetime.utcnow(),
    )
    db.add(url)
    db.commit()
    db.refresh(url)
    # Two clicks from google (should be deduplicated), one with no referrer
    db.add(ClickEvent(url_id=url.id, referrer="https://google.com", accessed_at=datetime.utcnow()))
    db.add(ClickEvent(url_id=url.id, referrer="https://google.com", accessed_at=datetime.utcnow()))
    db.add(ClickEvent(url_id=url.id, referrer=None, accessed_at=datetime.utcnow()))
    db.commit()
    return url


def test_get_analytics(client, db):
    """SCENARIO-008: Analytics endpoint returns click_count, last_accessed, deduplicated referrers."""
    _seed_with_clicks(db)
    resp = client.get("/api/urls/abc123/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["short_code"] == "abc123"
    assert data["click_count"] == 10
    assert data["last_accessed"] is not None
    assert data["referrers"] == ["https://google.com"]  # deduplicated, None excluded


def test_get_analytics_not_found(client, db):
    """REQ-SHORT-003: Unknown short code → 404."""
    resp = client.get("/api/urls/zzz999/analytics")
    assert resp.status_code == 404
    assert resp.json()["error"] == "Short code not found"


def test_get_url_detail(client, db):
    """REQ-SHORT-006: GET /api/urls/{short_code} returns URL details."""
    _seed_with_clicks(db, click_count=5)
    resp = client.get("/api/urls/abc123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["short_code"] == "abc123"
    assert data["url"] == "https://example.com"
    assert data["click_count"] == 5


def test_delete_url(client, db):
    """REQ-SHORT-006: DELETE /api/urls/{short_code} → 204 then 404."""
    _seed_with_clicks(db)
    resp = client.delete("/api/urls/abc123")
    assert resp.status_code == 204
    resp = client.delete("/api/urls/abc123")
    assert resp.status_code == 404

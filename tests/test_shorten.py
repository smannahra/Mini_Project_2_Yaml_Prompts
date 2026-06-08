def test_shorten_valid_url(client):
    """SCENARIO-001: POST a new valid URL → 201 with 6-char alphanumeric short_code."""
    resp = client.post("/api/shorten", json={"url": "https://www.example.com/very/long/path"})
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["short_code"]) == 6
    assert data["short_code"].isalnum()
    assert data["url"] == "https://www.example.com/very/long/path"
    assert "short_url" in data
    assert data["short_code"] in data["short_url"]


def test_shorten_duplicate_url_returns_200(client):
    """SCENARIO-006: Same URL shortened twice → 200 with same short_code, no new record."""
    first = client.post("/api/shorten", json={"url": "https://www.example.com"})
    assert first.status_code == 201
    code = first.json()["short_code"]

    second = client.post("/api/shorten", json={"url": "https://www.example.com"})
    assert second.status_code == 200
    assert second.json()["short_code"] == code


def test_shorten_invalid_url_returns_422(client):
    """SCENARIO-005: Malformed URL → 422."""
    resp = client.post("/api/shorten", json={"url": "not-a-valid-url"})
    assert resp.status_code == 422
    assert resp.json()["error"] == "Invalid URL format"
    assert resp.json()["code"] == "INVALID_URL"


def test_shorten_blocklisted_url_returns_400(client):
    """REQ-SHORT-005 / NFR-002: Known malicious domain → 400."""
    resp = client.post("/api/shorten", json={"url": "https://malware.com/payload"})
    assert resp.status_code == 400
    assert "Malicious" in resp.json()["error"]
    assert resp.json()["code"] == "MALICIOUS_URL"


def test_shorten_with_expiry(client):
    """REQ-SHORT-004: expiry_date is accepted and returned."""
    resp = client.post(
        "/api/shorten",
        json={"url": "https://timed.example.com", "expiry_date": "2099-01-01T00:00:00"},
    )
    assert resp.status_code == 201
    assert resp.json()["expiry_date"] is not None

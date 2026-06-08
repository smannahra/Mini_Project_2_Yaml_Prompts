 ---
  Implementation Plan — URL Shortener Service

  Stack

  Python 3.11+, FastAPI, SQLite via SQLAlchemy (sync), Pydantic v2, SlowAPI (rate limiting), pytest

  ---
  File Tree

  url-shortener-sdd/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py                  # FastAPI app, lifespan, rate limiter mount
  │   ├── database.py              # SQLAlchemy engine, session factory, Base
  │   ├── models.py                # ORM models: Url, ClickEvent
  │   ├── schemas.py               # Pydantic request/response schemas
  │   ├── routers/
  │   │   ├── __init__.py
  │   │   ├── shorten.py           # POST /api/shorten
  │   │   ├── redirect.py          # GET /{short_code}
  │   │   └── urls.py              # GET/DELETE /api/urls/{short_code}[/analytics]
  │   ├── services/
  │   │   ├── __init__.py
  │   │   ├── url_service.py       # Shorten, lookup, delete business logic
  │   │   └── analytics_service.py # Click recording, analytics query
  │   └── utils/
  │       ├── __init__.py
  │       ├── code_generator.py    # 6-char alphanumeric short code generator
  │       └── validators.py        # URL format check + malicious-domain blocklist
  ├── tests/
  │   ├── __init__.py
  │   ├── conftest.py              # In-memory SQLite fixture, test client
  │   ├── test_shorten.py          # SCENARIO-001, 005, 006
  │   ├── test_redirect.py         # SCENARIO-002, 003, 004, 007
  │   └── test_analytics.py        # SCENARIO-008
  ├── requirements.txt
  └── specs/
      └── url-shortener.yaml       # (already exists)

  ---
  Data Model

  Table: urls

  ┌───────────────┬────────────┬───────────────────────────┬───────────────┐
  │    Column     │    Type    │        Constraints        │     Notes     │
  ├───────────────┼────────────┼───────────────────────────┼───────────────┤
  │ id            │ INTEGER    │ PK, autoincrement         │               │
  ├───────────────┼────────────┼───────────────────────────┼───────────────┤
  │ short_code    │ VARCHAR(6) │ UNIQUE, NOT NULL, indexed │ REQ-SHORT-001 │
  ├───────────────┼────────────┼───────────────────────────┼───────────────┤
  │ original_url  │ TEXT       │ NOT NULL, indexed         │ dedup lookup  │
  ├───────────────┼────────────┼───────────────────────────┼───────────────┤
  │ created_at    │ DATETIME   │ NOT NULL, default=now     │               │
  ├───────────────┼────────────┼───────────────────────────┼───────────────┤
  │ expiry_date   │ DATETIME   │ NULL                      │ REQ-SHORT-004 │
  ├───────────────┼────────────┼───────────────────────────┼───────────────┤
  │ click_count   │ INTEGER    │ NOT NULL, default=0       │ REQ-SHORT-003 │
  ├───────────────┼────────────┼───────────────────────────┼───────────────┤
  │ last_accessed │ DATETIME   │ NULL                      │ REQ-SHORT-003 │
  └───────────────┴────────────┴───────────────────────────┴───────────────┘

  Table: click_events

  ┌─────────────┬──────────┬────────────────────────┬───────────────┐
  │   Column    │   Type   │      Constraints       │     Notes     │
  ├─────────────┼──────────┼────────────────────────┼───────────────┤
  │ id          │ INTEGER  │ PK, autoincrement      │               │
  ├─────────────┼──────────┼────────────────────────┼───────────────┤
  │ url_id      │ INTEGER  │ FK → urls.id, NOT NULL │               │
  ├─────────────┼──────────┼────────────────────────┼───────────────┤
  │ referrer    │ TEXT     │ NULL                   │ REQ-SHORT-003 │
  ├─────────────┼──────────┼────────────────────────┼───────────────┤
  │ accessed_at │ DATETIME │ NOT NULL, default=now  │               │
  └─────────────┴──────────┴────────────────────────┴───────────────┘

  click_events is append-only. Referrers list in analytics is SELECT DISTINCT referrer … WHERE referrer IS NOT NULL.

  ---
  Tasks

  ---
  TASK-001 — Project scaffold & dependencies

  Requirement: REQ-SHORT-006
  Description: Create requirements.txt, all __init__.py files, and the top-level directory structure so every subsequent
  task has a place to land.

  Files created:
  - requirements.txt
  - app/__init__.py, app/routers/__init__.py, app/services/__init__.py, app/utils/__init__.py
  - tests/__init__.py

  Acceptance criteria:
  - pip install -r requirements.txt completes without errors
  - requirements.txt pins: fastapi, uvicorn[standard], sqlalchemy, pydantic[email], slowapi, pytest, httpx

  ---
  TASK-002 — Database setup

  Requirement: REQ-SHORT-001, REQ-SHORT-003
  Description: Implement app/database.py — SQLAlchemy engine pointed at ./url_shortener.db, session factory, Base, and
  init_db() that calls Base.metadata.create_all().

  Files created: app/database.py

  Acceptance criteria:
  - init_db() creates the SQLite file on first run
  - A FastAPI lifespan hook in main.py calls init_db() at startup
  - Session dependency get_db() yields a session and closes it after each request

  ---
  TASK-003 — ORM models

  Requirement: REQ-SHORT-001, REQ-SHORT-003, REQ-SHORT-004
  Description: Implement app/models.py with Url and ClickEvent mapped classes matching the data model above.

  Files created: app/models.py

  Acceptance criteria:
  - Url.short_code has a unique index
  - Url.original_url has a regular index (for dedup lookup)
  - ClickEvent.url_id is a FK to urls.id with CASCADE delete
  - Both tables have __repr__ for debugging

  ---
  TASK-004 — Pydantic schemas

  Requirement: REQ-SHORT-001, REQ-SHORT-006
  Description: Implement app/schemas.py with all request and response models.

  Files created: app/schemas.py

  Schemas:
  - ShortenRequest — url: str, expiry_date: datetime | None
  - ShortenResponse — short_code, short_url, url, created_at, expiry_date
  - UrlDetailResponse — short_code, url, created_at, expiry_date, click_count
  - AnalyticsResponse — short_code, click_count, last_accessed, referrers: list[str]
  - ErrorResponse — error: str, code: str

  Acceptance criteria:
  - All response models use model_config = ConfigDict(from_attributes=True)
  - expiry_date serialises to ISO 8601 string in responses

  ---
  TASK-005 — Short code generator

  Requirement: REQ-SHORT-001
  Description: Implement app/utils/code_generator.py — generates a random 6-character code from [A-Za-z0-9] (62 chars →
  56B combinations).

  Files created: app/utils/code_generator.py

  Acceptance criteria:
  - generate_short_code() returns exactly 6 alphanumeric characters
  - Uses secrets.choice (cryptographically random, no random module)
  - Caller is responsible for uniqueness retry loop (handled in TASK-007)

  ---
  TASK-006 — URL validator & blocklist

  Requirement: REQ-SHORT-005, NFR-002
  Description: Implement app/utils/validators.py with two functions: validate_url_format(url) and check_blocklist(url).

  Files created: app/utils/validators.py

  Blocklist (hardcoded set, expandable): malware.com, phishing-site.net, evil.ru, scam-domain.xyz (representative
  examples).

  Acceptance criteria:
  - validate_url_format raises ValueError("Invalid URL format") if scheme is not http/https or netloc is empty (uses
  urllib.parse.urlparse)
  - check_blocklist raises ValueError("Malicious URL detected") if the URL's hostname matches any blocklisted domain
  - Both raise on None / empty string input

  ---
  TASK-007 — URL shortening service

  Requirement: REQ-SHORT-001, REQ-SHORT-004, REQ-SHORT-005
  Description: Implement app/services/url_service.py — shorten_url(db, request, base_url) orchestrates validation, dedup,
  code generation, and persistence.

  Files created: app/services/url_service.py

  Logic:
  1. Call validate_url_format → raises → router returns 422
  2. Call check_blocklist → raises → router returns 400
  3. Query urls by original_url — if found, return existing record (caller returns 200)
  4. Retry loop: generate_short_code() until code not already in DB (collision guard)
  5. Insert new Url row, commit, return record (caller returns 201)

  Acceptance criteria:
  - Duplicate URL returns the existing Url object with a flag distinguishing 200 vs 201
  - Short code uniqueness is guaranteed — loop retries up to 10× before raising RuntimeError
  - expiry_date stored as-is (UTC datetime) when provided

  ---
  TASK-008 — Redirect & expiry service

  Requirement: REQ-SHORT-002, REQ-SHORT-003, REQ-SHORT-004
  Description: Add lookup_url(db, short_code) to url_service.py; extend analytics_service.py with record_click(db, url,
  referrer).

  Files modified/created: app/services/url_service.py, app/services/analytics_service.py

  Logic for redirect:
  1. Query urls by short_code → 404 if not found
  2. Check expiry_date — if set and < datetime.utcnow() → 410
  3. Call record_click(db, url, referrer) — increments click_count, updates last_accessed, inserts ClickEvent
  4. Return original_url for the 302

  Acceptance criteria:
  - click_count increments atomically (single UPDATE statement, not read-modify-write)
  - last_accessed set to datetime.utcnow() on every redirect
  - referrer captured from Request.headers.get("referer") (case-insensitive via FastAPI)
  - Expired URLs never redirect regardless of click count

  ---
  TASK-009 — Analytics service

  Requirement: REQ-SHORT-003
  Description: Add get_analytics(db, short_code) to app/services/analytics_service.py.

  Files modified: app/services/analytics_service.py

  Logic:
  1. Lookup Url by short_code → 404 if missing
  2. Query SELECT DISTINCT referrer FROM click_events WHERE url_id=? AND referrer IS NOT NULL
  3. Return dict with short_code, click_count, last_accessed, referrers

  Acceptance criteria:
  - referrers is a deduplicated list of strings
  - last_accessed is None if URL has never been clicked
  - Returns 404 via HTTPException if short code unknown

  ---
  TASK-010 — API routers

  Requirement: REQ-SHORT-006
  Description: Wire all endpoints into FastAPI routers.

  Files created: app/routers/shorten.py, app/routers/redirect.py, app/routers/urls.py

  Endpoints:

  ┌─────────────┬────────┬──────────────────────────────────┬──────────────┐
  │    File     │ Method │               Path               │ Success code │
  ├─────────────┼────────┼──────────────────────────────────┼──────────────┤
  │ shorten.py  │ POST   │ /api/shorten                     │ 201 / 200    │
  ├─────────────┼────────┼──────────────────────────────────┼──────────────┤
  │ redirect.py │ GET    │ /{short_code}                    │ 302          │
  ├─────────────┼────────┼──────────────────────────────────┼──────────────┤
  │ urls.py     │ GET    │ /api/urls/{short_code}           │ 200          │
  ├─────────────┼────────┼──────────────────────────────────┼──────────────┤
  │ urls.py     │ GET    │ /api/urls/{short_code}/analytics │ 200          │
  ├─────────────┼────────┼──────────────────────────────────┼──────────────┤
  │ urls.py     │ DELETE │ /api/urls/{short_code}           │ 204          │
  └─────────────┴────────┴──────────────────────────────────┴──────────────┘

  Acceptance criteria:
  - All error responses use ErrorResponse schema with error and code fields
  - POST /api/shorten returns ShortenResponse; short_url is constructed as {base_url}/{short_code} using Request.base_url
  - GET /{short_code} returns RedirectResponse(url=..., status_code=302)
  - 410 response body is {"error": "URL has expired", "code": "URL_EXPIRED"}
  - 404 response body is {"error": "Short code not found", "code": "NOT_FOUND"}

  ---
  TASK-011 — App entry point & rate limiting

  Requirement: REQ-SHORT-006, NFR-003
  Description: Implement app/main.py — create the FastAPI app, attach SlowAPI rate limiter (100/hour per IP on
  /api/shorten), register all routers, add lifespan hook.

  Files created: app/main.py

  Acceptance criteria:
  - uvicorn app.main:app --reload starts the server
  - /api/shorten returns HTTP 429 after 100 requests from the same IP within one hour
  - Rate limit header X-RateLimit-Limit present in shorten responses
  - All routers mounted with correct prefixes — redirect router has no prefix so GET /{short_code} is at root

  ---
  TASK-012 — Tests

  Requirement: REQ-SHORT-001 through REQ-SHORT-006 (all scenarios SCENARIO-001 through SCENARIO-008)
  Description: Write pytest tests using an in-memory SQLite test database and FastAPI TestClient.

  Files created: tests/conftest.py, tests/test_shorten.py, tests/test_redirect.py, tests/test_analytics.py

  Acceptance criteria:
  - pytest tests/ passes with zero failures
  - Each Gherkin scenario from the spec has a corresponding test function (SCENARIO-001 → test_shorten_valid_url, etc.)
  - conftest.py overrides the get_db dependency with an in-memory SQLite session — no test writes to url_shortener.db
  - Tests cover: 201 create, 200 dedup, 422 bad URL, 400 blocklist, 302 redirect, 410 expired, 404 missing, analytics
  click count + referrer

  ---
  Build Order (dependency-safe)

  TASK-001 → TASK-002 → TASK-003 → TASK-004
                                        ↓
                 TASK-005 → TASK-006 → TASK-007 → TASK-008 → TASK-009
                                                                    ↓
                                                  TASK-010 → TASK-011 → TASK-012

  Tasks 005 and 006 have no DB dependency and can be written alongside TASK-003/004.

  ---
 
# Traceability Matrix — URL Shortener Service

## Requirement → Code → Test → Status

| Req ID | Description | Code File | Test File | Test Function | Status |
|--------|-------------|-----------|-----------|---------------|--------|
| REQ-SHORT-001 | URL Shortening | app/services/url_service.py | tests/test_shorten.py | test_shorten_valid_url | ✅ PASS |
| REQ-SHORT-002 | URL Redirection | app/routers/redirect.py | tests/test_redirect.py | test_redirect_valid | ✅ PASS |
| REQ-SHORT-003 | Analytics Tracking | app/services/analytics_service.py | tests/test_analytics.py | test_analytics_click_count | ✅ PASS |
| REQ-SHORT-004 | URL Expiry | app/services/url_service.py | tests/test_redirect.py | test_redirect_expired_url | ✅ PASS |
| REQ-SHORT-005 | URL Validation | app/utils/validators.py | tests/test_shorten.py | test_shorten_invalid_url | ✅ PASS |
| REQ-SHORT-006 | RESTful API | app/routers/ | tests/ (all) | multiple | ✅ PASS |
| NFR-001 | Performance <100ms | N/A | No test | N/A | ⚠️ GAP |
| NFR-002 | Blocklist/Security | app/utils/validators.py | tests/test_shorten.py | test_shorten_blocked_url | ⚠️ PARTIAL |
| NFR-003 | Rate Limiting | app/main.py | No test | N/A | ⚠️ GAP |

## Gherkin Scenario → Test → Status

| Scenario ID | Description | Test Function | Status |
|-------------|-------------|---------------|--------|
| SCENARIO-001 | Shorten valid URL | test_shorten_valid_url | ✅ PASS |
| SCENARIO-002 | Redirect short URL | test_redirect_valid | ✅ PASS |
| SCENARIO-003 | Track analytics | test_analytics_referrer | ✅ PASS |
| SCENARIO-004 | Reject expired URL | test_redirect_expired_url | ✅ PASS |
| SCENARIO-005 | Reject invalid URL | test_shorten_invalid_url | ✅ PASS |
| SCENARIO-006 | Return existing code for duplicate | test_shorten_duplicate_url | ✅ PASS |
| SCENARIO-007 | Return 404 for unknown code | test_redirect_not_found | ✅ PASS |
| SCENARIO-008 | Get analytics | test_analytics_endpoint | ✅ PASS |

## Coverage Summary

- Functional requirements: 6/6 fully covered ✅
- Non-functional requirements: 0/3 fully covered ⚠️
- Gherkin scenarios: 8/8 covered ✅
- Total tests: 15
- First run pass rate: 100%

## Known Gaps

| Gap | Reason | Mitigation |
|-----|--------|------------|
| NFR-001 performance test | Requires load testing tool | Manual testing with uvicorn |
| NFR-002 partial | Private IP blocking added in round 2 but no dedicated test | Covered implicitly |
| NFR-003 rate limit test | Requires 100+ requests in test | Manual testing only |
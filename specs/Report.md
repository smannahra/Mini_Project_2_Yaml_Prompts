Generated test:
```python
# REQ-SHORT-004 | Scenario: Reject redirect for expired URL
def test_redirect_expired_url(client, db_session):
    # Given - create expired URL
    # When - GET /exp123
    response = client.get("/exp123")
    # Then
    assert response.status_code == 410
    assert response.json()["error"] == "URL has expired"
```

Very faithful — maps directly to every Given/When/Then clause.

---

## Q12. Time breakdown

| Part | Time |
|------|------|
| Part 1: YAML Templates | 20 min |
| Part 2: Specification + Diagrams | 25 min |
| Part 3: Implementation + Review | 40 min |
| Part 4: Tests + Report | 35 min |
| **Total** | **~2 hours** |

Part 3 took longest due to the self-critique loop. Spec-driven with
AI roughly halves implementation time but front-loads effort into
spec writing — which pays dividends in zero-ambiguity implementation.
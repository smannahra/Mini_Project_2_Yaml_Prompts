---
name: project-url-shortener
description: URL Shortener SDD project — spec at specs/url-shortener.yaml, Python/FastAPI/SQLite, no Docker/JWT
metadata:
  type: project
---

Building a URL Shortener Service using spec-driven development.

Spec file: `specs/url-shortener.yaml` (v1.0.0, approved 2026-06-08)

**Why:** Mini Project 2 for Claude Code Mastery course, demonstrating spec-driven development.

**How to apply:** All implementation decisions must trace back to a REQ-SHORT-NNN or NFR-NNN requirement ID from the spec. Keep the stack simple: Python, FastAPI, SQLite (no Docker, no JWT).

Key requirements:
- REQ-SHORT-001: 6-char alphanumeric short codes, unique
- REQ-SHORT-002: HTTP 302 redirect, 410 for expired, 404 for missing
- REQ-SHORT-003: Track click_count, last_accessed, referrer per redirect
- REQ-SHORT-004: Optional ISO 8601 expiry_date
- REQ-SHORT-005: URL validation + blocklist, dedup returns existing code
- REQ-SHORT-006: RESTful JSON API with proper status codes
- NFR-002: Blocklist of malicious domains
- NFR-003: Rate limit 100 requests/IP/hour

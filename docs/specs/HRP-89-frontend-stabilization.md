# HRP-89 — Stabilize the bounded Streamlit demonstration interface

**Status:** Implemented on the review branch; pending human PR review
**Jira:** HRP-89
**Branch / PR:** `fix/frontend-stabilization` / PR #82
**Dependencies:** FastAPI query endpoints HRP-83–HRP-86; PostgreSQL runtime for live data
**Related ADR:** ADR-0007

## Objective

Provide a reproducible, tested Streamlit demonstration interface that queries the
curated data through FastAPI and is safe to run locally.

## Context and scope

- Includes: Streamlit startup, API client error handling, combined search filters,
  pagination, session-state cleanup, masking, native rendering, CI dependencies,
  and focused tests/documentation.
- Excludes: a product-final frontend, authentication, new data pipelines, and any
  direct database or broker integration.
- Scope decision: Streamlit is included as a bounded demonstration interface for
  this task. Its promotion to the final/product frontend remains subject to explicit
  scope approval; ADR-0007 keeps React + TypeScript + Vite as the preferred future
  direction and Streamlit as fallback-only for a constrained demo.
- Historical relationship: HRP-93 records the earlier project closeout with the
  frontend excluded. This spec documents a later, bounded demo change and does not
  rewrite that historical acceptance record.

## Architecture and security

The runtime boundary is:

```text
Streamlit → FastAPI → curated PostgreSQL data
```

Streamlit does not consume Kafka, MongoDB RAW, PostgreSQL, or Redis directly. The
interface excludes IBAN and salary, masks passport, email, phone and IP values, and
does not retain unused sensitive fields in session state. Dynamic API values are
rendered with native Streamlit components rather than unescaped HTML.

## Acceptance criteria

- [x] Streamlit starts from the repository root after installing `.[dev,frontend]`.
- [x] Search uses FastAPI combined filters and `limit` / `offset` pagination, and
  clears stale results/details on a new request or error.
- [x] Expected API failures and invalid JSON produce controlled user-facing errors.
- [x] Sensitive fields are masked and no bank or salary data is exposed.
- [x] CI installs frontend dependencies and focused AppTest coverage exists.
- [x] Execution instructions identify API `127.0.0.1:8123` and frontend
  `127.0.0.1:8501`.

## Accessibility and sustainability applicability

- Accessibility: applicable. Visible labels, headings, native Streamlit inputs,
  buttons, tabs, tables, structured detail output and readable errors are implemented
  and covered by AppTest. This is not a formal WCAG 2.2 AA audit or conformance claim;
  keyboard-only and rendered-interface review remain human PR evidence.
- Sustainability: applicable. The UI uses bounded API responses, explicit pagination,
  one combined search request, no polling, and no direct duplicate database access.
- Deferred claims: no formal WCAG conformance, carbon/energy result, production
  frontend status, or deployment claim is made.

## Test strategy and evidence

| Level | Case | Expected evidence |
|---|---|---|
| Unit | API client errors, masking and combined request | Focused pytest tests |
| AppTest | Startup, statistics, unavailable API, search and masking | `tests/test_frontend_app.py` with zero exceptions |
| API | Search, statistics, health and CORS | Existing unit tests plus local HTTP checks when PostgreSQL is available |
| Full suite | Regression and coverage threshold | `pytest --basetemp <isolated-dir>` |

## Limitations and follow-up

PostgreSQL may be empty in local demonstrations, legitimately producing empty
searches and zero statistics. MongoDB-dependent integrations may be skipped when
the service is unavailable. Browser review and GitHub Actions status are external
evidence and are not replaced by local tests.

## Completion evidence

- Commit: to be recorded after the corrective documentation commit.
- Jira closing comment: pending human review and merge; no Jira mutation is made by
  this change.

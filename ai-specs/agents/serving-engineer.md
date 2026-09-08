---
name: serving-engineer
description: Plan, implement or review PostgreSQL, FastAPI and future frontend work.
---

# Serving engineer

Use for Johans's PostgreSQL and API work. Frontend is excluded from the HRP-93
closeout; any later UI work follows ADR-0007, not an assumed Streamlit implementation. Start from the approved data model
and API contract. Design migrations, unique constraints, indexes and idempotent upserts
before handlers. API and dashboard may query curated PostgreSQL data only. Test schema
constraints, repository behaviour and HTTP success/error paths without exposing
sensitive fields.

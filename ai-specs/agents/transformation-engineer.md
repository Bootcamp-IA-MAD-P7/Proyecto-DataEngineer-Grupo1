---
name: transformation-engineer
description: Plan, implement or review ETL correlation, Redis state and metrics.
---

# Transformation engineer

Use for Gaby's ETL, Redis and observability work. Read the approved event contract,
data model and task spec before changing code. Keep field mapping evidence-based,
idempotent and tolerant of incomplete or out-of-order fragments. Redis must have a TTL
and never be the sole source of truth. Require tests for duplicates, invalid messages,
ordering and expiry; do not claim a correlation key until reviewed evidence and its
own transformation specification approve it.

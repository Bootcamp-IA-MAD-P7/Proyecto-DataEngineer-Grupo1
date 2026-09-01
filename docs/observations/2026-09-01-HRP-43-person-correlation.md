# HRP-43 — Authorised empirical person-correlation observation — 2026-09-01

**Observed by:** Gabriela
**Reviewer:** Pending human review
**Authorised environment:** Kafka through the HR Pro consumer and MongoDB RAW
**Database / collection:** `hr_pro` / `raw_events_hrp43_20260901`
**Method:** `scripts/hrp43_observe.py`, exact raw equality, aggregate-only output
**Restriction confirmed:** No educational generator source or logs were inspected.

## Session summary

| Item | Observation |
|---|---|
| Kafka endpoint | `localhost:29092` |
| Topic | `probando` |
| Consumer group | `hrp43-correlation-20260901` |
| Sample size | 2,000 RAW events |
| Invalid events | 0 |
| Comparison | Exact raw equality; no normalization or hashing |

No payload values, candidate values, hashes, or complete messages are recorded here.

## Observed payload shapes

| Count | Fields |
|---:|---|
| 399 | `IBAN`, `passport`, `salary` |
| 401 | `IPv4`, `address` |
| 400 | `address`, `city`, `fullname` |
| 401 | `company`, `company address`, `company_email`, `company_telfnumber`, `fullname`, `job` |
| 399 | `email`, `last_name`, `name`, `passport`, `sex`, `telfnumber` |

## Candidate metrics

| Candidate | Present | Missing | Distinct values | Repeated values | Repeated occurrences | Cross-shape values | Cross-shape event pairs |
|---|---:|---:|---:|---:|---:|---:|---:|
| `passport` | 798 | 1,202 | 401 | 397 | 794 | 397 | 397 |
| `fullname` | 801 | 1,199 | 402 | 399 | 798 | 399 | 399 |
| `address` | 801 | 1,199 | 401 | 400 | 800 | 400 | 400 |

Null and empty candidate values were not present in this sample. Counts for true
collisions and identity-based counterexamples remain unknown because person identity
is not observable in the authorised RAW evidence.

## Evidence-supported interpretation

- `passport` is supported as a partial candidate connecting the Personal and Bank
  structural shapes.
- `fullname` is supported as a partial candidate connecting the Location and
  Professional structural shapes.
- `address` is supported as a partial candidate connecting the Location and Net
  structural shapes.
- Location therefore provides an observed bridge between Professional and Net.
- Personal/Bank remain disconnected from Location/Professional/Net in this evidence.
- No universal person key is supported.

These are partial correlation observations, not proof of uniqueness or person identity.
Absence of observed collisions is not evidence of uniqueness. The global HRP-43 result
is **Insufficient evidence**.

## Evidence limitations and next action

The observation does not establish true-person labels, collision ground truth,
completeness, conflict resolution, normalization, or business uniqueness. No hidden
relationship is inferred from generator behavior. A further authorised observation
with identity-grounded evidence would be required before recommending a universal key.

## Execution evidence

- Command: `.\\.venv\\Scripts\\python.exe scripts/hrp43_observe.py`
- Output: aggregate metrics only; no candidate values or payloads emitted.
- ADR-0006: remains Proposed and blocked.
- Human review: pending.

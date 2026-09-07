---
# HRP-89 — Read-only React frontend for curated profiles

## Objective
Visualize curated employee records via the existing FastAPI API (HRP-83..86).
The frontend adds no new endpoints and performs no writes.

## Stack and location
React + TypeScript + Vite, managed with Bun (never npm). Lives at repo-root
`frontend/`. It is NOT a Python package and is excluded from ruff/mypy/pytest.

## API consumed (existing, unchanged)
- GET /health -> {"status":"ok"}
- GET /people/search?id&passport&first_name&last_name&limit(1-100)&offset
  -> list[PersonSearchResult]; 400 if all four filters empty
- GET /people/search/by-location-profession?city&address&job&company&limit&offset
  -> list[PersonSearchResult]; 400 if all four filters empty
- GET /statistics -> StatisticsResult
No person-by-id endpoint exists. Detail view calls /people/search?id=X and
takes the first row; empty list means "not found" (the API never returns 404
for a missing person).

## Views
1. Dashboard: live /health status badge (poll every 30s, never hardcoded
   online), /statistics metrics, pipeline diagram
   (Kafka -> MongoDB -> ETL -> PostgreSQL -> API -> Frontend), About cards.
2. Search: one form with two groups (Identity: id/first_name/last_name/passport;
   Location & Role: city/address/job/company), limit/offset pagination.
   Identity-only -> /people/search. Location-only ->
   /people/search/by-location-profession. Both -> parallel calls, intersect
   results by id (documented limitation: page-limited intersection).
   Empty form -> client-side warning, no API call.
3. Detail (route /person/:id): profile in blocks — Identity, Contact,
   Locations, Professional. Uses /people/search?id=X.

## Privacy (hard rules)
Mask at render, never stored or logged unmasked: passport, email,
telephone_number, ip_v4, company_email, company_telephone_number.
Formats: passport "*****123", email "a***@domain.com", phone "******789",
IP "84.12.x.x". bank_accounts (IBAN/salary) are never returned by the API and
never requested. No console.log/console.debug of API responses ever.

## Completeness indicator
"X/4 domains" per person, derived client-side from real API fields:
identity (first_name AND last_name), contact (email OR telephone_number),
location (locations list non-empty), professional (professional_profiles
list non-empty). This is derived from real data, not a backend measurement.

## UI states (all explicit, user must distinguish them)
loading / results / no results (echo the search criteria) /
API unavailable (network error or HTTP 503) / request error (4xx with detail).

## Accessibility
WCAG 2.2 AA applicability assessed: semantic HTML, labeled inputs,
sufficient color contrast on status badges.

## Out of scope
Kafka/MongoDB/Redis/Prometheus surfaces, authentication, writes, raw payloads.
---

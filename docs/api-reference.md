# Query API

Entry point: `python -m uvicorn hr_pro_platform.api.main:app --host 127.0.0.1 --port 8000`.
PostgreSQL must be configured and its schema created. OpenAPI: /docs and /openapi.json.

| Method / route | Input | Result |
|---|---|---|
| GET /health | None | SELECT 1; {"status":"ok"} when connected |
| GET /people/search | At least one: id, passport, first_name, last_name | Employee records with locations and professional_profiles |
| GET /people/search/by-location-profession | At least one: city, address, job, company | Same result shape; exact matches |
| GET /statistics | None | rows_per_table and employees_missing_domain |

Search uses exact equality. Multiple filters combine with AND; location and
professional filters together require both. No case folding, substring or fuzzy search.
Pagination defaults to limit=20, offset=0; limit must be 1–100 and offset non-negative.
Results order by employee id. No match returns [].

## Error contract

- Missing search filters or invalid pagination range: HTTP 400.
- Invalid parsed parameter type: FastAPI validation, normally HTTP 422.
- psycopg database error: HTTP 503 with {"status":"unavailable"}.
- Database dependency resolution may fail before filter validation when SQL is unavailable.

## Safe demonstration

```bash
curl http://localhost:8000/health
curl http://localhost:8000/statistics
curl "http://localhost:8000/people/search?id=1&limit=20&offset=0"
curl "http://localhost:8000/people/search/by-location-profession?city=Synthetic%20City"
```

Use an isolated database containing only synthetic data for search demonstrations.
id=1 is illustrative, not a claim that a row exists.

## Response boundaries

PersonSearchResult includes id, first_name, last_name, sex, telephone_number, email,
passport, locations and professional_profiles. Bank accounts, IBAN and salary are
excluded. Network records are not separately nested in the response.
Statistics exposes six row counts and four missing-domain counts, computed in SQL.

No authentication, authorization or production deployment is implemented here.
Excluding financial fields does not anonymize employee names, contacts or passports.
Do not expose the local API publicly without a separately designed access policy.

Sources: [routes](../src/hr_pro_platform/api/main.py),
[response models](../src/hr_pro_platform/api/people.py),
[statistics](../src/hr_pro_platform/api/statistics.py).

# HRP-70 — Run SQL persistence tests in CI

**Status:** Draft; not yet implemented
**Owner:** Johans Salas
**Human reviewer:** Miguel or Gaby
**Jira:** HRP-70 — Crear tests de persistencia SQL
**Dependencies:** HRP-72 (CI test automation, merged via [PR #22](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/22));
HRP-54/56/57/58/59/60 (PostgreSQL schema and persistence tests, merged)
**Related ADR:** None
**Planned branch:** `feature/HRP-70-sql-persistence-tests-ci`

## Objective

Make the SQL persistence tests that already exist run against a real PostgreSQL
database inside the repository's CI pipeline, so evidence currently reported as
"author-provided local evidence" in every review becomes CI-verified — without
rewriting or expanding those tests' own logic, and without touching MongoDB, Kafka
or Redis in CI.

## Context and scope

### Verified preconditions (checked against `develop` before drafting this spec)

- HRP-72's merge commit (PR #22) is on `develop`; `.github/workflows/ci.yml`'s
  single job is still named `quality` and runs
  `python scripts/validate_specs.py`, `pre-commit run --all-files`,
  `ruff check .`, `ruff format --check .`, `mypy src`, `pytest`, and a Compose
  syntax check, in that order.
- `ci.yml` declares no `services:` block; no PostgreSQL (or any database)
  service exists in CI today. Confirmed by direct inspection.
- No `docs/specs/HRP-70-*.md`, branch or PR existed before this task.

### The gap this task closes

`tests/unit/test_postgres_schema.py`, `tests/integration/test_person_repository.py`,
`tests/integration/test_grouped_data_persistence.py` and
`tests/integration/test_validation_queries.py` (HRP-54/56/57/58/59/60) already
exist and already pass locally against the `infra/compose.dev.yml` PostgreSQL
container. None of them run in CI: their `live_connection`/equivalent fixtures
attempt `psycopg.connect(...)` and call `pytest.skip(...)` on
`psycopg.OperationalError`, which is exactly what happens today in GitHub
Actions since no database is reachable there. `docs/specs/HRP-72-ci-test-automation.md`
explicitly excludes "persistence" from its own scope, leaving this gap for a
later task. Across every review round on HRP-56 through HRP-59, Miguel and
Gabriela repeatedly noted that PostgreSQL integration tests are skipped in CI
and that the reported live-database results are author-provided, not
CI-verified. This task closes exactly that gap — it is CI wiring, not new test
logic.

### Includes

- A `postgres` service added to the existing `quality` job in `ci.yml` (image
  `postgres:16`, matching `infra/compose.dev.yml`), with a health check
  (`pg_isready`) gating the job's steps.
- Job-level `POSTGRES_HOST`/`POSTGRES_PORT`/`POSTGRES_DB`/`POSTGRES_USER`/
  `POSTGRES_PASSWORD` environment variables pointing at that service, set
  before the `pytest` step runs. `tests/conftest.py`'s
  `os.environ.setdefault(...)` synthetic defaults do not override them, so
  the existing `live_connection`-style fixtures connect for real instead of
  skipping.
- Confirmation (documented, not silently assumed) that all four existing
  persistence test files pass when actually executed inside GitHub Actions
  against this service.

### Excludes (out of scope, do not touch)

- Rewriting, extending or otherwise changing the business logic of any
  existing persistence test, or of `person_repository.py`,
  `validation_queries.py`, `person_mapper.py` or the schema in `postgres.py`.
  This task wires existing, already-reviewed tests into CI; it does not
  re-review their content.
- Any MongoDB, Kafka or Redis service in CI — HRP-70 is specifically about SQL
  (PostgreSQL) persistence tests. `tests/integration/test_hrp34_mongo.py`
  continues to skip in CI exactly as it does today.
- Renaming the `quality` workflow, adding a second workflow, or removing/
  reordering its existing gates (spec validation, pre-commit, ruff, mypy). The
  Compose-syntax-check step for `infra/compose.dev.yml` is untouched — it
  stays a config-only check, not a claim of a running integration environment.
- Changing `infra/compose.dev.yml`, `.env.example`, or any local development
  workflow.
- Any credential used here is a throwaway, ephemeral value scoped to the CI
  job's own service container — never a real secret, never written to a file,
  never the same value as `.env.example`'s development password.

## Design

GitHub Actions' `services:` block on the existing `checks` job starts a
`postgres:16` container alongside the job's steps, with `pg_isready` as its
health check (mirroring `infra/compose.dev.yml`'s own health check verbatim).
The job's existing steps (spec validation, pre-commit, ruff, mypy) are
untouched and run exactly as before; only the environment gains the four
`POSTGRES_*` variables (plus `POSTGRES_HOST=localhost`, since GitHub Actions
service containers publish their ports back to the runner's own network
namespace) so that the `pytest` step's persistence-test fixtures can connect.

No application or test code changes: the four existing persistence test files
are used exactly as merged. If one of them turns out to fail or be flaky when
actually executed in the CI environment for the first time (as opposed to a
local Windows/dev-container run), that is treated as a genuine finding to
document explicitly in this spec's Risks section and in the PR — not something
to silently patch by changing test or production logic without recording why.

## What stays provisional / unknown / pending

- Whether any existing persistence test is sensitive to a CI-specific
  environment detail (timing, connection latency, `ubuntu-latest`'s network
  behavior) is unknown until this task actually runs them in GitHub Actions;
  any such finding is documented, not silently worked around.
- No new persistence guarantee is claimed beyond what HRP-54/56/57/58/59/60
  already established; this task changes where tests run, not what they
  assert.

## Acceptance criteria

- [ ] `ci.yml`'s `quality` job declares a `postgres:16` service with a health
      check, and exports `POSTGRES_*` environment variables before the
      `pytest` step.
- [ ] All four existing persistence test files
      (`test_postgres_schema.py`, `test_person_repository.py`,
      `test_grouped_data_persistence.py`, `test_validation_queries.py`) are
      confirmed to actually run (not skip) and pass inside a real GitHub
      Actions job, not only locally.
- [ ] No change to any test's or any production module's business logic.
- [ ] `test_hrp34_mongo.py` and any Kafka/Redis-dependent test continue to
      skip in CI exactly as before; no MongoDB/Kafka/Redis service is added.
- [ ] The `quality` workflow's name and existing gates (spec validation,
      pre-commit, ruff, mypy) are unchanged; no second workflow is introduced.
- [ ] `docs/specs/HRP-70-sql-persistence-tests-ci.md` is complete per
      `docs/specs/template.md`.

## Accessibility and sustainability applicability

- Accessibility: not applicable — CI configuration change with no user-facing
  flow.
- Sustainability: applicable — adding a database service to every CI run has a
  real, small resource cost (an additional container per job run). Accepted as
  the minimum needed to convert previously-skipped, already-existing tests
  into genuine CI evidence; no additional service, schedule or polling is
  introduced beyond the existing per-PR/per-push triggers.
- Deferred claims: none.

## Test strategy

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Workflow review | `ci.yml` declares the `postgres` service, health check and env vars correctly | Inspection of the committed YAML |
| CI (real) | The four existing persistence test files run (not skip) and pass in an actual GitHub Actions job | A real Actions run on this PR's branch, linked in the PR description — not local-only evidence |
| CI (real) | Non-persistence tests (`test_hrp34_mongo.py`) continue to skip in CI | Same Actions run's output |
| CI (real) | Every other existing `quality` gate (spec validation, pre-commit, ruff, mypy) still passes with the added service present | Same Actions run |

## Evidencia de cierre

- Rama / PR: pending
- Commit: pending
- Comandos ejecutados y resultado: pending
- Comentario Jira con el resultado: pending

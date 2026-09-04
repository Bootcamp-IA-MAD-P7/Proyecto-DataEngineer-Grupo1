# HRP-63 - Compose application, MongoDB and PostgreSQL

**Status:** Draft; implemented locally, pending PR review
**Owner:** Miguel
**Jira:** HRP-63
**Dependencies:** HRP-62 application Dockerfile, HRP-53 PostgreSQL service, HRP-64 environment configuration
**Related ADR:** `docs/adr/0002-raw-and-curated-storage.md`, `docs/adr/0004-configuration-and-secrets.md`
**Planned branch:** `feature/HRP-63-docker-compose-app-mongo-postgres`

## Objective

Provide one reproducible development Compose entry point that can run the existing
Python application image together with the local MongoDB and PostgreSQL services.
This completes the project-level Compose integration required by the intermediate
briefing level without embedding the external educational Kafka runtime.

## Context and scope

- Includes:
  - Add an `app` service to `infra/compose.dev.yml`.
  - Build the app from the existing root `Dockerfile`.
  - Keep MongoDB and PostgreSQL as the local database services already defined by
    HRP-33 and HRP-53.
  - Use `.env.example` as the safe default Compose environment file and `.env` as
    an optional local override, without committing local values.
  - Override `MONGODB_URI` inside the app container so it points to the Compose
    service name `mongo`, not to `localhost`.
  - Document how to start database-only mode and app profile mode.
- Excludes:
  - Kafka broker or educational generator services.
  - Redis, Prometheus, API, frontend or AWS deployment.
  - Changes to Kafka ingestion logic, MongoDB persistence, PostgreSQL schema,
    transformation, tests or data contracts.
  - Any real `.env` value, payload, secret, PII or generator-derived knowledge.
- Verifiable assumptions:
  - The app image from HRP-62 runs `python -m hr_pro_platform.ingestion.main`.
  - The app cannot run successfully until authorised Kafka configuration is supplied
    through local environment variables or the local `.env` override.
  - PostgreSQL is part of this integrated local stack even though the current
    ingestion entry point does not write to PostgreSQL yet.
- Risks:
  - Starting the `app` service without `KAFKA_BOOTSTRAP_SERVERS` and
    `KAFKA_TOPICS` configured will fail during startup. This is expected and must
    be documented rather than hidden by hard-coded defaults.
  - From inside a container, `localhost` refers to that container. Local Kafka
    running on the host must be exposed through an authorised host-reachable
    address such as `host.docker.internal:29092` when using Docker Desktop.

## Design

`infra/compose.dev.yml` remains the single local Compose file. The new `app`
service builds from the existing `Dockerfile`, reads `.env.example` first and the
untracked `.env` override second, and depends on healthy MongoDB and PostgreSQL
containers. PostgreSQL follows the same environment-file order so the database can
start with safe local defaults while still allowing developer-specific overrides.

The service is assigned to the explicit Compose profile `app`. This keeps the
database-only workflow from HRP-33 and HRP-53 stable:

```powershell
docker compose -f infra/compose.dev.yml up -d mongo postgres
```

The application worker is started only when the profile is requested:

```powershell
docker compose -f infra/compose.dev.yml --profile app up -d --build app
```

Kafka remains external. The Compose file does not include, copy, read or infer the
educational generator. The app receives Kafka configuration only through `.env` or
process environment values.

## Acceptance criteria

- [x] `infra/compose.dev.yml` defines an `app` service that builds from the existing
      `Dockerfile`.
- [x] The existing `mongo` and `postgres` services remain available and are not
      rewritten.
- [x] The `app` service depends on healthy MongoDB and PostgreSQL services.
- [x] The database-only workflow remains valid without starting the app.
- [ ] The app can be started explicitly through the `app` profile when authorised
      Kafka variables are configured.
- [x] PostgreSQL can start from `.env.example` defaults when no local `.env` exists.
- [x] No Kafka broker, generator, Redis, Prometheus, API or frontend service is
      added by this task.
- [x] Documentation explains that Kafka is external and `.env` stays local.
- [x] `docker compose -f infra/compose.dev.yml config --quiet` passes.

## Accessibility and sustainability applicability

- Accessibility: not applicable. This task introduces no user-facing flow,
  rendered interface or API response.
- Sustainability: applicable. The Compose stack avoids duplicating services,
  keeps Kafka external instead of copying the educational runtime, and uses an
  explicit `app` profile so developers can run only the services needed for the
  current task. No carbon, energy-saving or deployment claim is made.
- Deferred claims: no AWS readiness, production deployment, end-to-end Kafka
  throughput or full-pipeline performance claim is made by this task.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Static | Compose syntax and interpolation are valid | `docker compose -f infra/compose.dev.yml config --quiet` exits 0 |
| Runtime | MongoDB and PostgreSQL start without the app profile | `docker compose -f infra/compose.dev.yml up -d mongo postgres` and `ps` show healthy services |
| Runtime | MongoDB responds to a ping | `mongosh --eval "db.adminCommand('ping').ok"` returns `1` |
| Runtime | PostgreSQL responds to readiness check | `pg_isready -U hr_pro -d hr_pro` returns accepting connections |
| Build | App image builds through Compose | `docker compose -f infra/compose.dev.yml --profile app build app` succeeds |
| Quality | Specs and Python checks remain clean | Spec validation, Ruff, mypy and pytest where executable |

## Closing evidence

- Branch / PR: `feature/HRP-63-docker-compose-app-mongo-postgres` / pending.
- Commit: pending.
- Commands executed and result:
  - `python scripts/validate_specs.py` -> passed for 39 spec files.
  - `docker compose -f infra/compose.dev.yml config --quiet` -> passed.
  - `docker compose -f infra/compose.dev.yml up -d mongo postgres` -> passed;
    MongoDB and PostgreSQL containers started.
  - `docker compose -f infra/compose.dev.yml ps` -> MongoDB and PostgreSQL healthy.
  - `docker compose -f infra/compose.dev.yml exec -T mongo mongosh --quiet --eval "db.adminCommand('ping').ok"` -> returned `1`.
  - `docker compose -f infra/compose.dev.yml exec -T postgres pg_isready -U hr_pro -d hr_pro` -> returned `accepting connections`.
  - `docker compose -f infra/compose.dev.yml --profile app build app` -> image built successfully.
  - `ruff check .` -> passed.
  - `ruff format --check .` -> passed.
  - `mypy src` -> passed.
  - `pytest` -> local Windows run blocked by `confluent_kafka` DLL Application
    Control during ingestion test imports; this is an environment limitation, not
    caused by the Compose diff. GitHub Actions remains the authoritative evidence.
  - `pre-commit run --all-files` -> local Windows Application Control blocked
    `pre-commit.exe`; individual available checks above were run separately.
- Jira comment: pending; the task remains In Progress until human review and merge.

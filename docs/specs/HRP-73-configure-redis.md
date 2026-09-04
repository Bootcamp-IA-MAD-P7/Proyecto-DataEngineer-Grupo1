# HRP-73 — Configure Redis in Docker Compose

**Status:** Draft
**Owner:** Gabriela (GG)
**Jira:** HRP-73
**Dependencies:** Existing development Compose and Redis temporary-state architecture
**Related ADR:** [ADR-0004](../adr/0004-configuration-and-secrets.md)

## Objective

Provide a reproducible, healthy Redis service in the existing development Docker
Compose file so future processing tasks can use Redis for temporary correlation state.

## Context and scope

- Includes: one official Redis service in `infra/compose.dev.yml`, internal Compose
  networking, healthcheck, restart policy and operational documentation.
- Excludes: Redis repositories, ETL integration, serialization, business TTL policy,
  metrics and application dependencies.
- Verifiable assumptions: Compose's default network provides the stable service
  hostname `redis`; the existing `REDIS_URL` already documents `redis:6379/0`.
- Risks: Redis data is intentionally lost when the container and its ephemeral
  filesystem are removed; MongoDB remains the recoverable raw source.

## Design

Use the official `redis:7.2` image, matching the repository's existing major/minor
image pinning convention. The service is named `redis`, uses the default Compose
network, and listens on its standard internal port 6379 without host publication.
It uses a `tmpfs` mount for `/data` rather than persistent storage and has no
authentication configuration. The healthcheck runs `redis-cli ping` with the same
timing as MongoDB and PostgreSQL.

Redis is temporary correlation state, not a source of truth, so persistence is
deferred until an approved task establishes a need beyond the existing raw and
curated stores.

## Acceptance criteria

- [ ] `infra/compose.dev.yml` defines an official, versioned `redis` service.
- [ ] Redis is reachable by the Compose hostname `redis` on internal port 6379.
- [ ] Redis does not publish port 6379 to the host.
- [ ] The healthcheck verifies Redis with `redis-cli ping` and expects `PONG`.
- [ ] Redis has no persistent volume or authentication secret.
- [ ] Existing MongoDB and PostgreSQL service definitions remain valid.
- [ ] Operational documentation explains startup, connectivity and ephemeral state.
- [ ] Future Redis storage, TTL, ETL and metrics tasks remain out of scope.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this infrastructure task introduces no user-facing
  flow or interface.
- Sustainability: applicable — the service avoids an unnecessary host port and
  persistent volume; evidence is the Compose definition and runtime service scope.
- Deferred claims: no carbon, energy or deployment-efficiency claim is made without
  measured evidence.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Static | Compose configuration | `docker compose -f infra/compose.dev.yml config --quiet` exits 0 |
| Runtime | Redis startup and health | `docker compose ... ps` reports Redis healthy |
| Runtime | Redis protocol | `docker compose ... exec -T redis redis-cli ping` returns `PONG` |
| Regression | Existing services | Compose config remains valid for MongoDB and PostgreSQL |

## Closing evidence

- Branch / PR: pending human workflow
- Commit: pending human workflow
- Commands and results: recorded in the task report
- Jira closing comment: pending human approval and merge

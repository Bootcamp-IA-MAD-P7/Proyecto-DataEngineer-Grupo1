# HRP-62 — Create the Python application Dockerfile

**Status:** Draft; implementation authorised
**Owner:** Miguel
**Jira:** HRP-62
**Dependencies:** Existing Kafka consumer entry point and `pyproject.toml`
**Related ADR:** `docs/adr/0004-configuration-and-secrets.md`
**Planned branch:** `feature/HRP-62-application-dockerfile`

## Objective

Provide a reproducible, minimal Docker image for the existing Kafka ingestion command.
The image must be runnable with configuration supplied at runtime and must not embed
environment files, secrets, services, or educational-runtime code.

## Scope and boundaries

### Includes

- A root-level Dockerfile based on a supported Python 3.11 image.
- Installation of the application from `pyproject.toml` and execution of
  `hr_pro_platform.ingestion.main`.
- A non-root runtime user.
- A `.dockerignore` that prevents local environment files, caches, runtime data, and
  repository metadata from entering the build context.
- README and runbook instructions for a reproducible image build.

### Excludes

- Docker Compose, MongoDB, PostgreSQL, Redis, Prometheus, or any other service.
- Runtime secrets, `.env` files, hard-coded Kafka endpoints, topics, or payload data.
- Changes to consumer, transformation, persistence, or logging behaviour.
- Execution or inspection of the educational Kafka generator.

### Assumptions and risks

- The existing application command is `python -m hr_pro_platform.ingestion.main`.
- Kafka runtime configuration is supplied through environment variables at container
  start; this task only builds the image.
- A successful image build does not demonstrate a live Kafka connection or a
  complete Docker stack. Those are future tasks.

## Design

The image copies only the packaging metadata, README, and `src/` tree required to
install and run the application. It runs as an unprivileged `app` user and defines
the ingestion command as its default command. `.dockerignore` excludes `.env` and
other local/runtime artifacts even though the Dockerfile does not use a broad
`COPY . .` instruction.

## Acceptance criteria

- [ ] `docker build` creates the image successfully from the repository root.
- [ ] The image runs as a non-root user.
- [ ] The default command is the existing Kafka ingestion module.
- [ ] `.env`, `.env.*`, caches, runtime data, and Git metadata are excluded from the
      Docker build context.
- [ ] The Dockerfile contains no endpoint, credential, topic, payload, or generator
      value.
- [ ] README and runbook explain that this image is not the final Compose stack.

## Validation strategy

| Level | Case | Expected evidence |
|---|---|---|
| Build | Build the image from the repository root | `docker build` succeeds |
| Security | Inspect the Dockerfile and build context rules | No `.env` or secret copied |
| Runtime metadata | Inspect image user and command | Non-root user and expected command |
| Quality | Repository quality gates | Pre-commit, Ruff, mypy, pytest where executable |

## Closing evidence

- Branch / PR: pending.
- Commit: pending.
- Commands and results: pending.
- Jira comment: pending; the task remains In Progress until a human reviews the PR.

# HRP-72 — Configure automated test execution in GitHub

**Status:** Ready for review
**Owner:** Miguel
**Jira:** HRP-72
**Dependencies:** Existing quality workflow and repository test harness
**Related ADR:** None

## Objective

Make the repository's existing quality harness reproducible on every pull request
to `develop` and every push to `develop`, without duplicating workflows or weakening
current controls.

## Context and scope

- Includes: auditing the existing GitHub Actions workflow, adding the missing
  `pre-commit` execution step to the existing `quality` workflow, and recording
  traceable evidence of the CI contract.
- Excludes: application code, Docker services, Kafka, persistence, ETL, data-contract
  changes, external secrets, educational Kafka runtime, E2E testing and load testing.
- Verified assumptions: `pyproject.toml` defines the development dependency group and
  pytest coverage threshold; `.pre-commit-config.yaml` defines repository hooks.
- Risks: local Windows Application Control can prevent Python executables or native
  extensions from running. GitHub Actions on `ubuntu-latest` is the authoritative
  execution environment for this task.

## Design

The existing `.github/workflows/ci.yml` workflow, named `quality`, is the single CI
pipeline for pull requests and pushes targeting `develop`. It installs the project
with `.[dev]`, validates task specifications, and runs repository quality controls.

HRP-72 adds `pre-commit run --all-files` to that existing workflow. The workflow
continues to run explicit Ruff checks, mypy and pytest afterwards because these are
separately required, visible CI controls. Pytest reads its configured coverage
threshold from `pyproject.toml`; the workflow does not override it.

No secret, environment file, Kafka broker, Docker runtime service or educational
generator is required by the test job. The existing Compose syntax validation remains
an isolated configuration check and is not presented as a running integration test.

## Acceptance criteria

- [x] The existing `quality` workflow installs the package and development
  dependencies from `pyproject.toml`.
- [x] The workflow validates task specifications and runs `pre-commit run --all-files`.
- [x] The workflow runs `ruff check .`, `ruff format --check .`, `mypy src` and
  `pytest` using the configured coverage threshold.
- [x] A failure in any executed command fails the GitHub Actions job.
- [x] The workflow uses no secrets and does not start or inspect the educational Kafka
  runtime.
- [x] The existing workflow name remains `quality`, preserving compatibility with
  branch-protection checks.

## Test strategy

| Level | Case | Expected evidence |
|---|---|---|
| Workflow review | Inspect `ci.yml`, `pyproject.toml` and `.pre-commit-config.yaml` | Commands and dependency source are traceable |
| Local quality | Run the repository harness where Windows permits | Command results or explicit Application Control limitation |
| CI | Open a pull request to `develop` | `quality / checks` runs the complete harness on Ubuntu |

## Completion evidence

- Branch / PR: `feature/HRP-72-ci-test-automation` / pending human review
- Commit: pending
- Commands and result: pending local and GitHub Actions execution
- Jira closing comment: pending merge and human verification

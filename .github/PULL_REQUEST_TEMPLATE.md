<!-- Required title: HRP-XX type: short summary. Example: HRP-30 feat: add Kafka consumer -->

## Context and traceability

- **Jira:** HRP-XX
- **Spec:** `docs/specs/HRP-XX-*.md`
- **Owner:**
- **Suggested reviewer:**
- **AI assistance:** none / tool name and role used

## What changes and why

<!-- Describe the outcome and its boundary, not only the modified files. -->

## Acceptance criteria

- [ ] Acceptance criterion 1 is met.
- [ ] An error path or boundary case is covered.
- [ ] Scope has not expanded without updating the spec.

## Validation performed

- [ ] `pre-commit run --all-files`
- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `mypy src`
- [ ] `pytest`
- [ ] Integration / E2E (if applicable; link result):

## Data, security and operations

- [ ] No secrets, `.env` files, Docker volumes or complete message captures are included.
- [ ] The educational data generator has not been read, cloned or analyzed.
- [ ] Logs, metrics, migrations or runbook have been updated when applicable.

## Risks, decisions and rollback

- Related ADR / decision made:
- Known risk:
- How to roll back this change:

## Review checklist

- [ ] Someone other than the author has reviewed the change.
- [ ] The spec, documentation and Jira evidence are up to date.
- [ ] The Jira task will move to Done only after merge and verifiable evidence.
- [ ] If AI was used, its output has been checked against the spec, diff and tests.

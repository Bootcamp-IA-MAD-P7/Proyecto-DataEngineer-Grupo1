---
name: spec-driven-task
description: Execute one HR Pro Jira task through the shared SDD harness.
---

# Specification-driven task workflow

1. Load `AGENTS.md`, the applicable standards, the Jira task and its spec.
2. State objective, dependencies, assumptions, acceptance criteria, tests and files
   likely to change. Wait for plan approval when the task is ambiguous.
3. Branch from updated `develop` using `feature/HRP-XX-short-name`.
4. Implement the smallest vertical slice and update tests and documentation together.
5. Run `pre-commit run --all-files` and relevant `pytest` suites.
6. Use `code-auditing` for a self-review, then prepare an English PR description.
7. After human merge, prepare—not fabricate—the Jira closing comment with evidence.

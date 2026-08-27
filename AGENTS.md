# HR Pro Data Platform — Agent Instructions

Read this file before proposing or changing any artifact in this repository.

## Non-negotiable rule

Do not read, clone, search, analyse, infer or reconstruct the educational data generator. Treat it as a black box. Use only the public README, the project briefing and sanitised observations obtained from the authorised Kafka broker.

## Required workflow

1. Read `README.md`, `CONTRIBUTING.md`, `docs/04-sdd-workflow.md` and the Jira task spec before editing.
2. Identify the Jira key, owner, dependencies, acceptance criteria and verification.
3. If AI assistance is used, create or update `docs/ai/task-packets/HRP-XX-*.md`.
4. Work from a branch created from `develop`; never push directly to `develop`.
5. Change code, tests and documentation together in the smallest reviewable step.
6. Run `pre-commit run --all-files` and relevant tests.
7. Open a pull request using the English template, request a human reviewer and record evidence in Jira after merge.

## Data safety

Never commit secrets, `.env` files, tokens, private Kafka endpoints, full event payloads, personal data, banking data or raw customer-like data. Use sanitised and minimal fixtures only after authorised observation.

## Quality and authority

An AI may draft, analyse or suggest. Humans approve specs, architecture decisions, Jira changes, pull requests, merges, releases and external actions. State facts, assumptions and open questions separately.

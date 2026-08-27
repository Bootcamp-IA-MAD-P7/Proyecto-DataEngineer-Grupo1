# HR Pro Data Platform — AI Agent Entry Point

This file is the entry point for every coding assistant, regardless of the tool used.

## Read in this order before changing anything

1. `docs/base-standards.md` — single source of truth for global rules.
2. The applicable standard: `docs/backend-standards.md` or
   `docs/documentation-standards.md`.
3. `docs/04-sdd-workflow.md`, the Jira task and its `docs/specs/HRP-XX-*.md` file.
4. The relevant role under `ai-specs/agents/` and workflow under `ai-specs/skills/`.

## Mandatory project boundary

Never read, clone, search, analyse, infer or reconstruct the educational data
generator. Treat it as a black box. Use only the public README, project briefing and
sanitised observations obtained from the authorised Kafka broker.

## Authority boundary

AI may draft, analyse, plan and implement inside an approved branch. A human approves
specifications, architecture decisions, Jira mutations, pull requests, merges,
releases and external actions. Separate facts, assumptions and open questions.

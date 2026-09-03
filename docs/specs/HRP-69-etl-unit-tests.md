# HRP-69 — Create ETL unit tests

**Status:** Implemented; pending human review
**Owner:** Gabriela Granja
**Human reviewer:** Miguel
**Jira:** HRP-69
**Dependencies:** HRP-44 classification; HRP-45 validation; HRP-46, HRP-47, HRP-48, HRP-49 and HRP-61 domain groupers; HRP-50/HRP-96 consolidation contracts; HRP-51 reconciliation behavior; HRP-55 pure PostgreSQL mapping layer
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-69-etl-unit-tests`
**Implementation branch:** `feature/HRP-69-etl-unit-tests`

## Objective

Create focused unit-test evidence for the current ETL transformation path without
changing production behavior, contracts, persistence, ingestion or identity
semantics. The tests must make the approved classification, validation, grouping,
consolidation and pure mapping behavior executable and reviewable.

## Context and scope

The current implementation already exposes a pure transformation path under
`src/hr_pro_platform/transformation/` and a pure `ConsolidatedPersonRecord` mapper
under `src/hr_pro_platform/storage/person_mapper.py`. Existing unit tests cover most
of this behavior, but the repository has no HRP-69 specification defining the
remaining evidence, its boundaries or its relationship to the downstream PostgreSQL
tasks.

### Includes

- Unit tests for public transformation functions and result contracts:
  - `classify_payload(...)`;
  - `validate_fragment(...)`;
  - `group_personal_fragments(...)`;
  - `group_location_fragments(...)`;
  - `group_professional_fragments(...)`;
  - `group_bank_fragments(...)`;
  - `group_net_fragments(...)`; and
  - `consolidate_person_records(...)`.
- Unit-level regression evidence for `map_person_record(...)`, where a test is needed
  to protect the approved HRP-55 field mapping or the HRP-96 multi-group boundary.
- Synthetic, minimized JSON-compatible fixtures only.
- Explicit assertions for normal flow, malformed or unsupported input, duplicate and
  replay evidence, order independence, incomplete components, ambiguity, unresolved
  material, provenance and input immutability where the existing contract defines
  those behaviors.
- Mocks only for external boundaries if a test reaches an adapter; the core ETL
  tests must remain in memory and must not require Kafka, MongoDB, Redis or
  PostgreSQL.

### Excludes

- Production-code changes, new ETL behavior or a new reconciliation layer.
- A global person identity key, business uniqueness, normalization, fallback
  correlation, recency or conflict-precedence semantics.
- Kafka consumer behavior and raw MongoDB persistence tests owned by HRP-30/31/34.
- Live database tests or PostgreSQL repository write behavior owned by HRP-56,
  HRP-57 and HRP-58.
- Redis state, expiry, API, frontend, Docker or end-to-end testing.
- Repeating tests that already prove the same behavior without identifying a concrete
  uncovered branch or regression risk.
- Reading, cloning or analyzing the educational data generator.

## Current implementation and test evidence

The ETL transformation boundary currently consists of:

| Area | Public implementation | Existing unit evidence |
|---|---|---|
| Classification | `transformation.classifier.classify_payload` | `tests/unit/test_classifier.py` |
| Structural validation | `transformation.validator.validate_fragment` | `tests/unit/test_validation_cleaning.py` |
| Personal grouping | `personal_grouper.group_personal_fragments` | `tests/unit/test_personal_grouper.py` |
| Location grouping | `location_grouper.group_location_fragments` | `tests/unit/test_location_grouper.py` |
| Professional grouping | `professional_grouper.group_professional_fragments` | `tests/unit/test_professional_grouper.py` |
| Bank grouping | `bank_grouper.group_bank_fragments` | `tests/unit/test_bank_grouper.py` |
| Net grouping | `net_grouper.group_net_fragments` | `tests/unit/test_net_grouper.py` |
| Consolidation | `person_consolidator.consolidate_person_records` | `tests/unit/test_person_consolidator.py`, `tests/unit/test_hrp51_reconciliation.py` |
| Pure PostgreSQL mapping | `storage.person_mapper.map_person_record` | `tests/unit/test_person_mapper.py` |

On the isolated baseline run from `develop` commit `2675dfa`, the repository had
177 collected tests, 168 passed and 9 integration tests skipped because MongoDB or
PostgreSQL was unavailable. Coverage was 88.62% overall and the required 75% threshold
passed. The ETL transformation plus pure mapper subset reached 95% combined coverage:
`classifier`, `fragment_contract`, `person_consolidator`, `validator` and
`person_mapper` were at 100%; Personal was 90%, Location 95%, Professional 91%, Bank
91% and Net 91%.

The remaining uncovered transformation lines are defensive branches in the groupers
after upstream validation, primarily repeated payload-shape/type handling. They must
be tested only if the behavior is observable and contract-supported; coverage alone
does not authorize new semantics. `PersonRepository.connect()`/`close()` also have
uncovered lines, but that adapter is outside the ETL unit-test scope proposed here.

## Design and test boundaries

Tests must call the public functions through their typed contracts and assert the
returned dataclasses or tuples. They must not test private helpers directly unless a
public behavior cannot otherwise be observed.

The approved boundaries remain unchanged:

- classification uses exact key sets and ignores values;
- validation is structural and performs no business cleaning;
- each grouper uses its approved exact domain-local key;
- exact duplicate `(payload, SourceReference)` evidence is retained once;
- equal payloads with different `SourceReference` values remain separate evidence;
- ambiguous evidence is preserved rather than resolved by recency or precedence;
- `UnresolvedFragment` retains original payload, classification, source reference and
  technical reason;
- `ConsolidatedPersonRecord` retains the five `DomainGroupContribution` boundaries;
- `consolidate_person_records(...)` remains deterministic and pure; and
- `map_person_record(...)` translates fields without assigning database identity or
  performing database I/O.

The source reference remains opaque. These tests must not infer that it is a business
identity, event time, version, correction marker or universal replay key.

## Acceptance criteria

- [ ] **AC-01:** Focused unit tests exercise every public ETL transformation function
      and its declared result contract using synthetic in-memory inputs.
- [ ] **AC-02:** Tests cover valid exact structures and explicit malformed,
      unsupported, wrong-domain or unusable-key outcomes without inventing value
      semantics.
- [ ] **AC-03:** Tests prove exact domain-local grouping, exact duplicate evidence
      deduplication, separate differing evidence and explicit ambiguity where the
      existing contracts define those outcomes.
- [ ] **AC-04:** Tests prove incomplete components, valid completion, conflicting
      evidence, unresolved material and preservation of `UnresolvedFragment` context.
- [ ] **AC-05:** Tests prove order-independent deterministic results, stable
      provenance and non-mutation of caller-owned payloads and result inputs.
- [ ] **AC-06:** Tests cover the HRP-96 `DomainGroupContribution` boundaries and
      preserve all retained fragments when a domain has multiple groups.
- [ ] **AC-07:** Tests cover the approved HRP-55 field mapping only where a concrete
      regression or missing branch is identified; mapping tests must not perform SQL
      or assign `id`/`employee_id`.
- [ ] **AC-08:** No test introduces global identity, normalization, fallback
      correlation, temporal precedence, business uniqueness or persistence semantics.
- [ ] **AC-09:** No test reads the educational generator or uses complete raw
      payloads, personal data, secrets or live external services.
- [ ] **AC-10:** The focused tests pass, the full quality harness passes or records
      environment-only skips/failures, and the final evidence links the spec, branch,
      commit, PR and validation output.

## Test strategy

| Level | Case | Evidence |
|---|---|---|
| Unit | Exact classification and structural validation | Public result, explicit reason and preserved input |
| Unit | Each domain grouper normal, duplicate, order, invalid and ambiguity paths | Group keys/statuses/fragments/unresolved output |
| Unit | Consolidation complete, incomplete, ambiguous and unresolved components | `ConsolidationResult`, five domain boundaries, rules and provenance |
| Unit | Pure mapper regression, if required after gap review | Candidate rows preserve approved field mapping and source references |
| Quality | `python scripts/validate_specs.py`, `pre-commit run --all-files`, `ruff check .`, `ruff format --check .`, `mypy src`, `pytest` | Commands pass; unavailable integration services are explicitly reported |

Tests must use behavior names and reference the relevant AC identifier, following
`docs/05-test-harness.md`. Existing tests should be extended only when the gap review
identifies missing evidence; otherwise they are the evidence for the corresponding
criterion and should not be duplicated.

## Dependencies and risks

- HRP-44 and HRP-45 define the upstream classification and validation boundaries.
- HRP-46/47/48/49/61 define the domain-local grouping precedents.
- HRP-50 and HRP-96 define consolidated status, unresolved output and
  `DomainGroupContribution` boundaries.
- HRP-51 defines incomplete, duplicate and out-of-order transformation behavior.
- HRP-55 defines the pure candidate-row mapping; HRP-56 and HRP-58 are downstream
  persistence precedents, not reasons to test live PostgreSQL here.
- HRP-57 exists as a remote branch but is not merged into `develop` and has no local
  spec in this baseline. HRP-69 must not encode its unreviewed update behavior.
- The baseline standard pytest command is affected by Windows permissions while
  scanning the shared `pytest-of-ggran` temporary directory. An isolated `--basetemp`
  run avoids that environmental error. MongoDB/PostgreSQL integration tests remain
  skipped when services are unavailable.
- Ruff format can encounter known inaccessible local cache directories during a
  repository-wide baseline. This is an environment/scope issue and must not be fixed
  by modifying unrelated untracked paths.

## Accessibility and sustainability applicability

- Accessibility: not applicable — HRP-69 adds backend unit-test evidence and no
  user-facing flow.
- Sustainability: applicable to test execution efficiency. Tests remain pure and
  bounded, avoid live services and full payloads, and reuse existing fixtures and
  parametrization where it improves evidence without duplicating cases.
- Deferred claims: no claim about production throughput, carbon, energy savings or
  end-to-end reliability is made by unit-test coverage alone.

## Definition of Ready

- The Jira task has an approved objective, owner, dependencies and observable
  acceptance criteria.
- This spec is reviewed and aligned with the current `develop` implementation.
- The reviewer agrees which uncovered branches are contract-relevant and which are
  intentionally left to upstream validation.

## Definition of Done

- Focused unit tests provide evidence for every approved runtime criterion without
  changing production behavior.
- Tests are synthetic, deterministic, isolated from external services and named by
  behavior.
- Relevant quality gates pass, with environment-dependent skips or failures recorded
  explicitly.
- No generator, raw payload, secret, ADR or unrelated module is changed.
- The PR links this spec, the test evidence and the Jira task, and a human reviewer
  approves the change before merge.

## Evidence of closure

- Branch / PR: `feature/HRP-69-etl-unit-tests` / pending commit and PR review.
- Tests added: one valid cross-domain rejection test in each of the Personal,
  Professional, Bank and Net grouper modules. These tests exercise the observable
  `not_*_fragment` outcome required by AC-02.
- Focused tests: 41 passed with coverage disabled.
- Full isolated suite: 172 passed, 9 integration tests skipped because MongoDB and
  PostgreSQL were unavailable; coverage 89.59%, above the 75% threshold.
- ETL transformation plus pure mapper coverage: 95% before HRP-69 and 97% after.
- Specification validation and pre-commit passed. Ruff check, mypy, Compose
  configuration and `git diff --check` passed. Repository-wide Ruff format remains
  affected by known inaccessible local cache paths and is not an HRP-69 failure.
- No production code, integration tests, ADRs, configuration or downstream task
  documentation were changed.
- Jira closure: HRP-69 must remain open until the implementation PR is merged and
  verifiable test evidence is added.

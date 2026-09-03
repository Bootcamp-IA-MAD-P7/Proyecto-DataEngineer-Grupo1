# HRP-60 — Grouped data persistence verification

**Status:** Draft; not yet implemented
**Owner:** Johans Salas
**Human reviewer:** Miguel or Gaby
**Jira:** HRP-60 — Comprobar que los datos agrupados están correctamente persistidos
**Dependencies:** HRP-46, HRP-47, HRP-48, HRP-49, HRP-61 (domain groupers, merged);
HRP-50 (`consolidate_person_records`, merged via PR #43); HRP-51 (reconciliation
behavior, merged); HRP-55 (`person_mapper.map_person_record`, merged); HRP-56/57/58
(`PersonRepository`, merged via [PR #50](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/50),
[PR #52](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/52),
[PR #51](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/51));
ADR-0006 (`Accepted in principle`)
**Related ADR:** [`docs/adr/0006-person-correlation-key.md`](../adr/0006-person-correlation-key.md)
**Planned branch:** `feature/HRP-60-grouped-data-persistence-verification`
**Blocks:** HRP-59 (Create SQL queries to validate final data) — HRP-59 must not
start until this task is approved.

## Objective

Produce a documented, reviewable verification — with evidence against a real
PostgreSQL database — that data grouped by the transformation layer (HRP-46 to
HRP-49, HRP-61) and consolidated by HRP-50 ends up correctly correlated and
persisted in the curated PostgreSQL tables after flowing through
`person_mapper.map_person_record` and `PersonRepository` (HRP-55/56/57/58).

## Context and scope

### Verified preconditions (checked against `develop` before drafting this spec)

- `src/hr_pro_platform/storage/person_repository.py` and `person_mapper.py` exist,
  and `docs/specs/HRP-55-*.md` to `HRP-58-*.md` describe the code as it exists on
  `develop` (confirmed by re-reading `InsertOutcome`, `_DEPENDENT_TABLE_COLUMNS`
  and the `FOR UPDATE` lock, which match their specs).
- `docs/adr/0006-person-correlation-key.md` status is exactly
  `Accepted in principle`; its "Responsibility boundaries" section still excludes
  real-world identity, database uniqueness and PostgreSQL persistence semantics.
- HRP-60 has no open Jira blocker of its own (checked directly on the Jira issue:
  no "is blocked by" link). Its own "blocks" links to HRP-57/HRP-58 are historical
  and already satisfied (both merged); its "blocks" link to HRP-59 is the one this
  task must resolve.
- No `docs/specs/HRP-60-*.md`, branch or PR existed for HRP-60 before this task.

### The gap this task actually addresses

Every existing integration test in `tests/integration/test_person_repository.py`
(HRP-56/57/58 evidence) constructs `PersonRecordMapping`/`CandidateRow` by hand and
calls `PersonRepository.insert_mapping()` directly. None of them exercise the
grouping stage (`group_personal_fragments`, `group_location_fragments`,
`group_professional_fragments`, `group_bank_fragments`, `group_net_fragments`) or
`consolidate_person_records` (HRP-50) at all. So while single-component inserts,
replays and enrichments are already verified against real PostgreSQL, nothing today
proves that the *actual output* of the grouping/consolidation layer — running on
realistic multi-fragment, multi-domain, multi-person input — persists correctly
once it reaches `person_mapper`/`person_repository`. That gap is exactly what
HRP-60 closes: an end-to-end path from classified fragments through grouping,
consolidation and mapping, to real PostgreSQL rows.

### Includes

- An end-to-end verification, exercised as repeatable test code (not a disposable
  manual script), that runs synthetic `ClassifiedFragment` input through
  `group_*_fragments` → `consolidate_person_records` → `map_person_record` →
  `PersonRepository.insert_mapping`, and checks the resulting PostgreSQL rows.
- Coverage of: one complete five-domain component; at least two distinct
  operationally-correlated people processed together without cross-contamination;
  an incomplete component (a known HRP-50 status) persisting only its present
  domains; and a later-arriving grouped fragment for an already-processed
  `source_reference` correctly enriching through the full pipeline (not just
  through a hand-built `CandidateRow`, per HRP-57).
- Explicit documentation of any gap found between what the grouping/consolidation
  layer produces and what actually lands in PostgreSQL.

### Excludes (out of scope, do not touch)

- Building the reusable SQL validation query library — that is HRP-59, which stays
  blocked until this task is approved.
- Any change to the PostgreSQL schema (HRP-54), Docker (HRP-53), or the
  insert/update/deduplication logic already implemented in `person_repository.py`
  (HRP-55/56/57/58). If a real defect is found in that logic, it is documented
  here as a finding/follow-up, not silently fixed inside this task.
- Resolving or advancing the person correlation key (ADR-0006 stays
  `Accepted in principle`, not final).
- Any change to `ingestion/`, `api/`, Kafka or MongoDB.
- Any change to the domain groupers' (HRP-46-49/61) or `consolidate_person_records`'s
  (HRP-50) own logic.

## Design

Pipeline exercised by this task's tests (all pure/production code, unmodified):

```text
ClassifiedFragment (synthetic, minimized, non-PII)
  -> group_personal_fragments / group_location_fragments /
     group_professional_fragments / group_bank_fragments / group_net_fragments
  -> consolidate_person_records()            (HRP-50)
  -> map_person_record()                     (HRP-55)
  -> PersonRepository.insert_mapping()        (HRP-56/57/58)
  -> real PostgreSQL curated tables
```

Fixtures use payloads whose key set exactly matches `classifier.DOMAIN_FIELDS` for
their domain (per `classify_payload`), and use only the four ADR-0006 exact edges
(`personal_bank_passport`, `personal_location_fullname`,
`location_professional_fullname`, `location_net_address`) to correlate fragments —
no fuzzy or heuristic matching, consistent with HRP-50's own constraints. Every
correlation claim made by a test assertion is scoped to "these fragments were
grouped through an approved ADR-0006 edge", never to real-world identity.

Verification queries the live PostgreSQL container (`infra/compose.dev.yml`), the
same pattern already used by `tests/integration/test_person_repository.py`.

## What stays provisional / unknown / pending

- No assertion in this task's tests may claim a persisted row proves real-world
  identity; every correlation-based assertion is scoped to the ADR-0006 exact edge
  that produced it.
- Domain/table combinations not yet covered by HRP-46-49/61 (if any surface during
  implementation) are documented as pending, not fabricated.
- Any production defect this verification surfaces is recorded as an explicit
  finding with a follow-up Jira reference, not fixed inside this task's branch.

## Acceptance criteria

- [ ] A complete five-domain grouped-and-consolidated component, run through the
      full pipeline, persists exactly the expected rows across all five curated
      tables under one `employee_id`, verified against real PostgreSQL.
- [ ] At least two distinct operationally-correlated people, grouped and
      consolidated together in the same run, persist under two distinct
      `employee_id`s with zero cross-contamination.
- [ ] An incomplete component (a domain absent per HRP-50's `incomplete` status)
      persists only its present domains; no row is fabricated for the missing one.
- [ ] A later-arriving grouped fragment for an already-processed `source_reference`,
      run through the full pipeline (grouping → consolidation → mapping →
      `insert_mapping`), correctly enriches the existing employee rather than
      duplicating or skipping silently.
- [ ] Any gap found between grouped/consolidated output and actual persistence is
      documented explicitly in this spec's Risks section, with a follow-up
      reference if it cannot be fixed inside this task's stated scope.
- [ ] No change to schema, Docker, or insert/update/deduplication production logic.
- [ ] This specification is complete per `docs/specs/template.md`.

## Accessibility and sustainability applicability

- Accessibility: not applicable — this is a backend data-persistence verification
  with no user-facing flow.
- Sustainability: applicable through reuse of the existing PostgreSQL dev container
  and repository code; no new service, dependency or persistent store is
  introduced. No carbon, energy or deployment claim is made.
- Deferred claims: none beyond the above.

## Test strategy

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Integración | Cadena completa de cinco dominios agrupada y consolidada, persistida en un solo `employee_id` | Contenedor HRP-53 real; filas exactas verificadas en las cinco tablas curadas |
| Integración | Dos personas distintas correlacionadas exactamente (ADR-0006), procesadas en la misma corrida, sin cruzarse | Contenedor real; `employee_id`s distintos, filas exactas por persona |
| Integración | Componente incompleto (dominio ausente) persiste solo lo presente | Contenedor real; tabla del dominio ausente sin fila para ese `employee_id` |
| Integración | Fragmento agrupado tardío para un `source_reference` ya procesado enriquece a través del pipeline completo | Contenedor real; `InsertOutcome.enriched_tables` no vacío, fila nueva presente, sin duplicados |
| Integración | Valores casi iguales pero no exactos (case/espacio) no se correlacionan | Contenedor real; dos `employee_id`s distintos, ninguna fila cruzada |

## Evidencia de cierre

- Rama: `feature/HRP-60-grouped-data-persistence-verification`; PR: pending
- Commit: pending (se añade tras el commit final de implementación)
- Comandos ejecutados y resultado:
  - `pre-commit run --all-files` → passed
  - `ruff check .` / `ruff format --check .` → passed
  - `mypy src` → `Success: no issues found in 26 source files`
  - `pytest` (suite completa contra PostgreSQL real,
    `docker compose -f infra/compose.dev.yml up -d postgres`) →
    `195 passed, 2 skipped in 18.91s` (skips son solo MongoDB, no relacionados)
  - Sanity check adicional: se confirmó por separado que si el fullname de
    "near miss" coincidiera exactamente en vez de diferir en mayúscula/espacio,
    `consolidate_person_records` produce 2 componentes en vez de 3 — prueba de
    que la aserción de no-cruce del test es sensible al comportamiento real,
    no vacía.
- Comentario Jira con el resultado: pending (se redacta tras aprobación de PR)

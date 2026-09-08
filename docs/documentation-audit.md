# Auditoría documental — HRP-93

**Corte:** 2026-09-08. **Responsable:** Miguel.
**Universo:**167 Markdown versionados al inicio; 8 documentos nuevos;
175 Markdown al final, incluyendo este inventario.
El alcance se limita al repositorio HR Pro, no a dependencias, entornos virtuales,
otras carpetas del workspace ni al generador educativo.

## Método y alcance de la revisión

1. Inventariar todos los Markdown, incluidos GitHub, contexto IA y plantillas.
2. Contrastar guías vigentes con entrypoints, Compose, configuración, clasificación,
   validación, consolidación, Redis, SQL, API, métricas y workflows.
3. Reconstruir integración de 59 specs desde el historial first-parent de develop,
   conservando requisitos/resultados originales como evidencia histórica.
4. Reconciliar nueve jornadas con commits, sin inventar reuniones, horas o bloqueos.
5. Preparar fuentes autocontenidas para NotebookLM y consultar nueve referencias oficiales.
6. Comprobar enlaces/anchors locales, estructura de specs, whitespace y alcance del diff.

La revisión de una spec histórica es de estado, trazabilidad y coherencia de sus
límites con las guías; **no es una recertificación funcional de cada checkbox**.
Las plantillas sin uso y políticas coherentes no se editan solo para aumentar el diff.
No se ejecutaron servicios, broker, suite funcional, benchmarks ni cambios de seguridad.

## Correcciones de fondo

| Hallazgo anterior | Corrección |
|---|---|
| Varias matrices y un Mermaid antiguo 3/6, 1/3, 0/3, 0/2 | Una matriz de aceptación 18/19 con límites técnicos separados |
| Diagrama presentaba process-worker completo antes de existir | Runtime continuo `app` + `etl` + `api`, separado de la prueba sintética HRP-71 |
| storage.main descrito como ETL | Inicialización de esquema y terminación |
| HRP-71 etiquetado como Kafka E2E real | Sintético Kafka-equivalente, sin broker ni Redis |
| Contrato mezclaba tipos observados y clasificador | Observación por claves/tipos frente a clasificación runtime por claves |
| ADR-0006 aún esperaba PR #42 | Integración0512612 del 2026-09-02, sin inventar identidad universal |
| Specs aún «Draft/pending merge» | Cabecera de integración con commit/PR; estado original explícitamente histórico |
| Fuentes incompletas y notas de agosto usadas como estado actual | Paquete NotebookLM, bibliografía y nueve jornadas trazables |
| Métricas SQL/errores/percentiles implícitos | Solo tres métricas de ingesta y límites reales de histogramas |
| Configuración reservada o inventada | Variables consumidas, LOG_LEVEL sin efecto y host/container diferenciados |
| Afirmaciones absolutas de seguridad/durabilidad | Riesgos de logs genéricos y huecos de offsets entre lotes explícitos |
| Fixtures descritas como solo observadas | Sintéticas identificadas o derivadas autorizadas, nunca hechos inventados |
| Daily 31 de agosto decía SQL pendiente | Registro intradía conservado; PR #31/#32 incorporadas al resumen final |

## Evidencia, aceptación y autorización

Miguel autoriza esta edición sin otra confirmación. Se conserva su aceptación
18/19 con frontend excluido; no se usa para afirmar mediciones inexistentes.
Miguel realiza el merge sin revisores adicionales. Jira no se modificó. La
extensión incorpora el worker ETL, servicios Compose y su prueba de runtime.

La extensión supera 270 pruebas unitarias, Ruff, formato y mypy. El intento completo
reportado anteriormente fue 246 pasan, 21 fallan, 40 omitidos,
82,91 % cobertura; no se reejecutó ni se reinterpretó como verde. Esta auditoría
no adjunta el log completo original ni certifica cada fallo como solo ambiental.

## Controles documentales

| Control | Resultado 2026-09-08 | Alcance |
|---|---:|---|
| Markdown detectados | 175 archivos | Incluye 167 previos y 8 nuevos |
| Enlaces/referencias Markdown locales | 659 comprobados | Sin errores de ruta ni anchor |
| URLs externas inventariadas | 484 | No revalidación HTTP completa de cada URL histórica |
| Specs validadas por `scripts/validate_specs.py` | 60 | 59 históricas más HRP-93 |
| `git diff --check` | 0 errores | Whitespace y marcadores de conflicto |
| Tablas Markdown auditadas | 0 avisos | Separadores y número de columnas |

El verificador de enlaces cubre enlaces Markdown locales y anchors de headings;
ignora bloques de código, placeholders de plantillas y la validez viva de cada
URL externa. No es un navegador GitHub ni una prueba visual de render de Mermaid.
Los diagramas son Mermaid nativo y las cifras también tienen alternativa tabular.

Las fuentes oficiales se consultaron para bibliografía; no se comprobaron todas
las URLs históricas, estados Jira, revisiones individuales o ejecuciones CI remotas.

## Inventario completo

- **Guía vigente:** revisión técnica/editorial y reconciliación.
- **Spec histórica:** estado e integración contrastados; criterios originales conservados.
- **Historia:** alcance temporal, fuentes y relación con estado vigente.
- **Plantilla/política:** coherencia y referencias; no se convierte en evidencia de ejecución.
- **Fuente presentación:** narrativa, trazabilidad y límites preparados para NotebookLM.

| Archivo | Tipo de revisión | Acción |
|---|---|---|
| [.github/ISSUE_TEMPLATE/bug_report.md](../.github/ISSUE_TEMPLATE/bug_report.md) | Plantilla/política | Revisado; conservado |
| [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md) | Plantilla/política | Actualizado |
| [AGENTS.md](../AGENTS.md) | Plantilla/política | Revisado; conservado |
| [CLAUDE.md](../CLAUDE.md) | Plantilla/política | Revisado; conservado |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Guía vigente | Actualizado |
| [GEMINI.md](../GEMINI.md) | Plantilla/política | Revisado; conservado |
| [README.md](../README.md) | Guía vigente | Actualizado |
| [ai-specs/README.md](../ai-specs/README.md) | Plantilla/política | Revisado; conservado |
| [ai-specs/agents/ingestion-engineer.md](../ai-specs/agents/ingestion-engineer.md) | Plantilla/política | Revisado; conservado |
| [ai-specs/agents/platform-engineer.md](../ai-specs/agents/platform-engineer.md) | Plantilla/política | Revisado; conservado |
| [ai-specs/agents/serving-engineer.md](../ai-specs/agents/serving-engineer.md) | Plantilla/política | Actualizado |
| [ai-specs/agents/transformation-engineer.md](../ai-specs/agents/transformation-engineer.md) | Plantilla/política | Revisado; conservado |
| [ai-specs/skills/code-auditing/SKILL.md](../ai-specs/skills/code-auditing/SKILL.md) | Plantilla/política | Revisado; conservado |
| [ai-specs/skills/enrich-us/SKILL.md](../ai-specs/skills/enrich-us/SKILL.md) | Plantilla/política | Revisado; conservado |
| [ai-specs/skills/spec-driven-task/SKILL.md](../ai-specs/skills/spec-driven-task/SKILL.md) | Plantilla/política | Revisado; conservado |
| [ai-specs/skills/update-docs/SKILL.md](../ai-specs/skills/update-docs/SKILL.md) | Plantilla/política | Revisado; conservado |
| [ai-specs/skills/using-git-worktrees/SKILL.md](../ai-specs/skills/using-git-worktrees/SKILL.md) | Plantilla/política | Revisado; conservado |
| [codex.md](../codex.md) | Plantilla/política | Revisado; conservado |
| [docs/00-project-charter.md](00-project-charter.md) | Guía vigente | Actualizado |
| [docs/01-architecture.md](01-architecture.md) | Guía vigente | Actualizado |
| [docs/02-data-contract.md](02-data-contract.md) | Guía vigente | Actualizado |
| [docs/03-data-model.md](03-data-model.md) | Guía vigente | Actualizado |
| [docs/04-sdd-workflow.md](04-sdd-workflow.md) | Guía vigente | Revisado; conservado |
| [docs/05-test-harness.md](05-test-harness.md) | Guía vigente | Actualizado |
| [docs/06-observability.md](06-observability.md) | Guía vigente | Actualizado |
| [docs/07-runbook.md](07-runbook.md) | Guía vigente | Actualizado |
| [docs/08-git-governance.md](08-git-governance.md) | Guía vigente | Actualizado |
| [docs/09-evolving-swot.md](09-evolving-swot.md) | Guía vigente | Actualizado |
| [docs/10-reference-benchmark.md](10-reference-benchmark.md) | Guía vigente | Actualizado |
| [docs/README.md](README.md) | Guía vigente | Nuevo |
| [docs/adr/0001-monolito-modular.md](adr/0001-monolito-modular.md) | Guía vigente | Actualizado |
| [docs/adr/0002-raw-and-curated-storage.md](adr/0002-raw-and-curated-storage.md) | Guía vigente | Actualizado |
| [docs/adr/0003-evidence-first-data-contract.md](adr/0003-evidence-first-data-contract.md) | Guía vigente | Actualizado |
| [docs/adr/0004-configuration-and-secrets.md](adr/0004-configuration-and-secrets.md) | Guía vigente | Revisado; conservado |
| [docs/adr/0005-kafka-acknowledgement-after-raw-persistence.md](adr/0005-kafka-acknowledgement-after-raw-persistence.md) | Guía vigente | Actualizado |
| [docs/adr/0006-person-correlation-key.md](adr/0006-person-correlation-key.md) | Guía vigente | Actualizado |
| [docs/adr/0007-accessibility-and-sustainable-delivery.md](adr/0007-accessibility-and-sustainable-delivery.md) | Guía vigente | Revisado; conservado |
| [docs/ai/README.md](ai/README.md) | Plantilla/política | Actualizado |
| [docs/ai/agent-charter.md](ai/agent-charter.md) | Plantilla/política | Revisado; conservado |
| [docs/ai/evaluation-rubric.md](ai/evaluation-rubric.md) | Plantilla/política | Actualizado |
| [docs/ai/human-approval-policy.md](ai/human-approval-policy.md) | Plantilla/política | Revisado; conservado |
| [docs/ai/prompts/analista-spec.md](ai/prompts/analista-spec.md) | Plantilla/política | Revisado; conservado |
| [docs/ai/prompts/coordinador-sprint.md](ai/prompts/coordinador-sprint.md) | Plantilla/política | Actualizado |
| [docs/ai/prompts/curador-presentacion.md](ai/prompts/curador-presentacion.md) | Plantilla/política | Actualizado |
| [docs/ai/prompts/disenador-pruebas.md](ai/prompts/disenador-pruebas.md) | Plantilla/política | Actualizado |
| [docs/ai/prompts/revisor-arquitectura.md](ai/prompts/revisor-arquitectura.md) | Plantilla/política | Revisado; conservado |
| [docs/ai/prompts/revisor-pr.md](ai/prompts/revisor-pr.md) | Plantilla/política | Revisado; conservado |
| [docs/ai/task-packet-template.md](ai/task-packet-template.md) | Plantilla/política | Revisado; conservado |
| [docs/ai/task-packets/HRP-24-contrato-datos.md](ai/task-packets/HRP-24-contrato-datos.md) | Historia | Actualizado |
| [docs/ai/task-packets/HRP-25-modelo-datos.md](ai/task-packets/HRP-25-modelo-datos.md) | Historia | Actualizado |
| [docs/ai/task-packets/HRP-29-observacion-kafka.md](ai/task-packets/HRP-29-observacion-kafka.md) | Historia | Actualizado |
| [docs/ai/task-packets/HRP-34-align-raw-persistence.md](ai/task-packets/HRP-34-align-raw-persistence.md) | Historia | Actualizado |
| [docs/ai/task-packets/HRP-52-tablas-relaciones.md](ai/task-packets/HRP-52-tablas-relaciones.md) | Historia | Actualizado |
| [docs/ai/task-packets/HRP-53-postgres-docker.md](ai/task-packets/HRP-53-postgres-docker.md) | Historia | Actualizado |
| [docs/ai/task-packets/HRP-54-postgres-schema.md](ai/task-packets/HRP-54-postgres-schema.md) | Historia | Actualizado |
| [docs/ai/task-packets/README.md](ai/task-packets/README.md) | Plantilla/política | Actualizado |
| [docs/api-reference.md](api-reference.md) | Guía vigente | Nuevo |
| [docs/backend-standards.md](backend-standards.md) | Plantilla/política | Actualizado |
| [docs/base-standards.md](base-standards.md) | Plantilla/política | Actualizado |
| [docs/configuration.md](configuration.md) | Guía vigente | Nuevo |
| [docs/dailies/2026-08-27-kickoff.md](dailies/2026-08-27-kickoff.md) | Historia | Actualizado |
| [docs/dailies/2026-08-28-progress-and-benchmark.md](dailies/2026-08-28-progress-and-benchmark.md) | Historia | Actualizado |
| [docs/dailies/2026-08-31-global-closeout.md](dailies/2026-08-31-global-closeout.md) | Historia | Actualizado |
| [docs/dailies/2026-09-01-transformation-foundation.md](dailies/2026-09-01-transformation-foundation.md) | Historia | Actualizado |
| [docs/dailies/2026-09-02-transformation-and-consolidation.md](dailies/2026-09-02-transformation-and-consolidation.md) | Historia | Actualizado |
| [docs/dailies/2026-09-03-serving-and-quality.md](dailies/2026-09-03-serving-and-quality.md) | Historia | Actualizado |
| [docs/dailies/2026-09-04-api-redis-and-integration.md](dailies/2026-09-04-api-redis-and-integration.md) | Historia | Actualizado |
| [docs/dailies/2026-09-07-observability-and-runtime.md](dailies/2026-09-07-observability-and-runtime.md) | Historia | Actualizado |
| [docs/dailies/2026-09-08-project-closeout.md](dailies/2026-09-08-project-closeout.md) | Historia | Actualizado |
| [docs/dailies/README.md](dailies/README.md) | Historia | Actualizado |
| [docs/dailies/_template.md](dailies/_template.md) | Plantilla/política | Revisado; conservado |
| [docs/data-model.md](data-model.md) | Guía vigente | Actualizado |
| [docs/delivery-evidence.md](delivery-evidence.md) | Guía vigente | Nuevo |
| [docs/development_guide.md](development_guide.md) | Guía vigente | Actualizado |
| [docs/documentation-audit.md](documentation-audit.md) | Inventario y controles | Nuevo |
| [docs/documentation-standards.md](documentation-standards.md) | Plantilla/política | Actualizado |
| [docs/external-dependencies.md](external-dependencies.md) | Guía vigente | Revisado; conservado |
| [docs/observations/2026-08-27-HRP-29-kafka.md](observations/2026-08-27-HRP-29-kafka.md) | Historia | Actualizado |
| [docs/observations/2026-09-01-HRP-43-person-correlation.md](observations/2026-09-01-HRP-43-person-correlation.md) | Historia | Actualizado |
| [docs/observations/2026-09-02-HRP-50-adr0006-correlation-evidence.md](observations/2026-09-02-HRP-50-adr0006-correlation-evidence.md) | Historia | Actualizado |
| [docs/observations/README.md](observations/README.md) | Historia | Actualizado |
| [docs/observations/_template.md](observations/_template.md) | Historia | Revisado; conservado |
| [docs/onboarding/ai-assisted-workflow.md](onboarding/ai-assisted-workflow.md) | Guía vigente | Actualizado |
| [docs/presentation-sources/00-project-story.md](presentation-sources/00-project-story.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/01-architecture-story.md](presentation-sources/01-architecture-story.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/02-evolving-swot.md](presentation-sources/02-evolving-swot.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/03-delivery-timeline.md](presentation-sources/03-delivery-timeline.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/04-final-acceptance.md](presentation-sources/04-final-acceptance.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/05-references.md](presentation-sources/05-references.md) | Fuente presentación | Nuevo |
| [docs/presentation-sources/NOTEBOOKLM-PACK.md](presentation-sources/NOTEBOOKLM-PACK.md) | Fuente presentación | Nuevo |
| [docs/presentation-sources/README.md](presentation-sources/README.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/2026-08-27.md](presentation-sources/daily/2026-08-27.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/2026-08-28.md](presentation-sources/daily/2026-08-28.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/2026-08-31.md](presentation-sources/daily/2026-08-31.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/2026-09-01.md](presentation-sources/daily/2026-09-01.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/2026-09-02.md](presentation-sources/daily/2026-09-02.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/2026-09-03.md](presentation-sources/daily/2026-09-03.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/2026-09-04.md](presentation-sources/daily/2026-09-04.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/2026-09-07.md](presentation-sources/daily/2026-09-07.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/2026-09-08.md](presentation-sources/daily/2026-09-08.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/README.md](presentation-sources/daily/README.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/daily/_template.md](presentation-sources/daily/_template.md) | Plantilla/política | Revisado; conservado |
| [docs/presentation-sources/evidence/2026-08-27-foundation-and-local-mongodb.md](presentation-sources/evidence/2026-08-27-foundation-and-local-mongodb.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/evidence/2026-08-28-kafka-contract-and-quality-baseline.md](presentation-sources/evidence/2026-08-28-kafka-contract-and-quality-baseline.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/evidence/2026-08-31-ingestion-storage-and-quality.md](presentation-sources/evidence/2026-08-31-ingestion-storage-and-quality.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/evidence/2026-09-08-closeout.md](presentation-sources/evidence/2026-09-08-closeout.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/evidence/README.md](presentation-sources/evidence/README.md) | Fuente presentación | Actualizado |
| [docs/presentation-sources/manifest.md](presentation-sources/manifest.md) | Fuente presentación | Actualizado |
| [docs/project-closeout.md](project-closeout.md) | Guía vigente | Actualizado |
| [docs/specs/HRP-21-git-quality-workflow.md](specs/HRP-21-git-quality-workflow.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-22-project-evolution-and-presentation.md](specs/HRP-22-project-evolution-and-presentation.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-23-architecture-baseline.md](specs/HRP-23-architecture-baseline.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-24-observed-data-contract.md](specs/HRP-24-observed-data-contract.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-25-modelo-datos.md](specs/HRP-25-modelo-datos.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-26-readme-onboarding.md](specs/HRP-26-readme-onboarding.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-29-kafka-observation.md](specs/HRP-29-kafka-observation.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-30-kafka-consumer.md](specs/HRP-30-kafka-consumer.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-31-continuous-ingestion.md](specs/HRP-31-continuous-ingestion.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-33-local-mongodb-environment.md](specs/HRP-33-local-mongodb-environment.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-34-align-kafka-mongodb-raw-boundary.md](specs/HRP-34-align-kafka-mongodb-raw-boundary.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-43-person-correlation.md](specs/HRP-43-person-correlation.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-44-domain-classification.md](specs/HRP-44-domain-classification.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-45-validation-cleaning.md](specs/HRP-45-validation-cleaning.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-46-group-location-by-person.md](specs/HRP-46-group-location-by-person.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-47-group-professional-by-person.md](specs/HRP-47-group-professional-by-person.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-48-group-bank-by-person.md](specs/HRP-48-group-bank-by-person.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-49-group-net-by-person.md](specs/HRP-49-group-net-by-person.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-50-consolidated-person-record.md](specs/HRP-50-consolidated-person-record.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-51-handle-incomplete-duplicate-order.md](specs/HRP-51-handle-incomplete-duplicate-order.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-52-tablas-relaciones.md](specs/HRP-52-tablas-relaciones.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-53-postgres-docker.md](specs/HRP-53-postgres-docker.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-54-postgres-schema.md](specs/HRP-54-postgres-schema.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-55-etl-postgres-connection.md](specs/HRP-55-etl-postgres-connection.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-56-insert-processed-person-records.md](specs/HRP-56-insert-processed-person-records.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-57-update-records-on-new-data.md](specs/HRP-57-update-records-on-new-data.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-58-avoid-duplicate-records.md](specs/HRP-58-avoid-duplicate-records.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-59-sql-validation-queries.md](specs/HRP-59-sql-validation-queries.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-60-grouped-data-persistence-verification.md](specs/HRP-60-grouped-data-persistence-verification.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-61-group-personal-by-person.md](specs/HRP-61-group-personal-by-person.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-62-application-dockerfile.md](specs/HRP-62-application-dockerfile.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-63-docker-compose-application-mongodb-postgresql.md](specs/HRP-63-docker-compose-application-mongodb-postgresql.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-64-environment-configuration.md](specs/HRP-64-environment-configuration.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-65-kafka-consumer-logging.md](specs/HRP-65-kafka-consumer-logging.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-66-etl-processing-logging.md](specs/HRP-66-etl-processing-logging.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-67-database-logging.md](specs/HRP-67-database-logging.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-68-kafka-consumer-unit-tests.md](specs/HRP-68-kafka-consumer-unit-tests.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-69-etl-unit-tests.md](specs/HRP-69-etl-unit-tests.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-70-sql-persistence-tests-ci.md](specs/HRP-70-sql-persistence-tests-ci.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-71-kafka-mongodb-postgresql-e2e-test.md](specs/HRP-71-kafka-mongodb-postgresql-e2e-test.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-72-ci-test-automation.md](specs/HRP-72-ci-test-automation.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-73-configure-redis.md](specs/HRP-73-configure-redis.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-74-store-partial-person-data-redis.md](specs/HRP-74-store-partial-person-data-redis.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-75-retrieve-partial-person-data-redis.md](specs/HRP-75-retrieve-partial-person-data-redis.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-76-configure-redis-temporary-data-expiration.md](specs/HRP-76-configure-redis-temporary-data-expiration.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-77-measure-consumed-messages-per-second.md](specs/HRP-77-measure-consumed-messages-per-second.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-78-measure-processing-time.md](specs/HRP-78-measure-processing-time.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-79-measure-persistence-time.md](specs/HRP-79-measure-persistence-time.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-80-expose-prometheus-metrics.md](specs/HRP-80-expose-prometheus-metrics.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-81-configure-prometheus.md](specs/HRP-81-configure-prometheus.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-82-basic-monitoring-dashboard.md](specs/HRP-82-basic-monitoring-dashboard.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-83-postgres-query-api.md](specs/HRP-83-postgres-query-api.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-84-search-person-endpoint.md](specs/HRP-84-search-person-endpoint.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-85-search-by-location-profession.md](specs/HRP-85-search-by-location-profession.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-86-statistics-endpoint.md](specs/HRP-86-statistics-endpoint.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-87-continuous-pipeline-runtime.md](specs/HRP-87-continuous-pipeline-runtime.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-88-docker-service-restart-policy.md](specs/HRP-88-docker-service-restart-policy.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-93-project-documentation-closeout.md](specs/HRP-93-project-documentation-closeout.md) | Guía vigente | Nuevo |
| [docs/specs/HRP-94-accessibility-sustainability-policy.md](specs/HRP-94-accessibility-sustainability-policy.md) | Spec histórica | Actualizado |
| [docs/specs/HRP-96-consolidation-contract-hardening.md](specs/HRP-96-consolidation-contract-hardening.md) | Spec histórica | Actualizado |
| [docs/specs/README.md](specs/README.md) | Guía vigente | Actualizado |
| [docs/specs/sprint-01-foundation-ingestion.md](specs/sprint-01-foundation-ingestion.md) | Guía vigente | Actualizado |
| [docs/specs/template.md](specs/template.md) | Plantilla/política | Revisado; conservado |
| [infra/README.md](../infra/README.md) | Guía vigente | Actualizado |
| [scripts/README.md](../scripts/README.md) | Guía vigente | Actualizado |
| [tests/fixtures/README.md](../tests/fixtures/README.md) | Guía vigente | Actualizado |

## Límites no resueltos por documentación

El worker continuo Mongo→Redis→SQL ya forma parte del Compose local. Siguen sin
acreditarse benchmark, alta disponibilidad ni recuperación ante desastres. El
prefijo durable de offsets es por lote y no conserva huecos entre lotes; la API
no tiene auth, Redis es efímero y el resultado local histórico no era verde.
Esta revisión no los corrige con código ni los oculta tras la aceptación.
Las dailies faltantes se reconstruyen por integraciones, no por supuestas reuniones.
El paquete es material de entrada de NotebookLM, no la presentación final generada.

## Estado de publicación

La revisión se guarda en la rama local codex/HRP-93-project-closeout.
No se publica, fusiona, etiqueta ni cierra Jira en esta intervención.
GitHub solo mostrará estos cambios tras subir la rama y, para develop, integrar su PR.

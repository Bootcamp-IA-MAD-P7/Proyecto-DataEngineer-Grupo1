# Manifest de fuentes para NotebookLM

| Fuente | Propósito en la presentación | Estado | Responsable |
|---|---|---|---|
| `00-project-story.md` | Contexto, objetivos y equipo | Inicial | Miguel |
| `01-architecture-story.md` | Arquitectura y recorrido del dato | Inicial | Miguel |
| `02-evolving-swot.md` | DAFO actual y evolución por hitos | Evolutivo | Miguel + equipo |
| `daily/` | Línea temporal, decisiones y avances | Continuo | Todo el equipo |
| `evidence/` | Evidencia de demo, pruebas y métricas | Activa: solo evidencia verificada | Responsable de cada área |
| `evidence/2026-08-27-foundation-and-local-mongodb.md` | Hito de fundación, calidad y MongoDB local | Verificado; no es demo final | Miguel + Anahí |
| `evidence/2026-08-28-kafka-contract-and-quality-baseline.md` | Contrato Kafka, consumer y calidad | Verificado con límites explícitos | Equipo |
| `evidence/2026-08-31-ingestion-storage-and-quality.md` | Ingesta, MongoDB inicial, tests y CI actuales | Verificado con límites explícitos | Equipo |
| `../01-architecture.md` | Detalle técnico ampliado | Actualizado con cada ADR | Miguel + revisores |
| `../05-test-harness.md` | Estrategia de calidad | Actualizado con pruebas | Miguel + Gaby |
| `../06-observability.md` | Métricas y monitorización | Pendiente de nivel avanzado | Gaby |

## Lista de carga por hito

### Sprint 1

- `00-project-story.md`
- `01-architecture-story.md`
- `02-evolving-swot.md`
- Último fichero válido de `daily/`
- `evidence/2026-08-27-foundation-and-local-mongodb.md`
- `evidence/2026-08-28-kafka-contract-and-quality-baseline.md`
- `evidence/2026-08-31-ingestion-storage-and-quality.md`
- `../01-architecture.md`
- `../04-sdd-workflow.md`

### Demo final

- Todas las fuentes anteriores.
- Evidencia de Kafka a MongoDB a PostgreSQL.
- Capturas o enlaces de Prometheus, API y frontend accesible.
- Resultado de pruebas y tag de release.
- Dailies que contengan decisiones relevantes, no necesariamente todas.

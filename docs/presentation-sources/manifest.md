# Manifest de fuentes para NotebookLM

| Fuente | Propósito en la presentación | Estado | Responsable |
|---|---|---|---|
| `00-project-story.md` | Contexto, objetivos y equipo | Inicial | Miguel |
| `01-architecture-story.md` | Arquitectura y recorrido del dato | Inicial | Miguel |
| `daily/` | Línea temporal, decisiones y avances | Continuo | Todo el equipo |
| `evidence/` | Evidencia de demo, pruebas y métricas | Pendiente de implementación | Responsable de cada área |
| `../01-architecture.md` | Detalle técnico ampliado | Actualizado con cada ADR | Miguel + revisores |
| `../05-test-harness.md` | Estrategia de calidad | Actualizado con pruebas | Miguel + Gaby |
| `../06-observability.md` | Métricas y monitorización | Pendiente de nivel avanzado | Gaby |

## Lista de carga por hito

### Sprint 1

- `00-project-story.md`
- `01-architecture-story.md`
- Último fichero válido de `daily/`
- `../01-architecture.md`
- `../04-sdd-workflow.md`

### Demo final

- Todas las fuentes anteriores.
- Evidencia de Kafka → MongoDB → PostgreSQL.
- Capturas o enlaces de Prometheus, API y Streamlit.
- Resultado de pruebas y tag de release.
- Dailies que contengan decisiones relevantes, no necesariamente todas.

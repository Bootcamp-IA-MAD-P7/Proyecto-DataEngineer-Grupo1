# Dailies compartidas

Cada daily se registra en Markdown con el formato `YYYY-MM-DD.md` o
`YYYY-MM-DD-descripcion.md`. Es un resumen breve y compartible; Jira sigue siendo la
fuente de estado de las tareas.

## Índice

- `2026-08-27-kickoff.md`: fundación, reparto inicial y gobernanza.
- `2026-08-28-progress-and-benchmark.md`: contrato Kafka, consumo continuo, benchmark,
  calidad y siguiente corte raw.
- `2026-08-31-global-closeout.md`: estado global tras integrar ingesta, MongoDB,
  modelo SQL, CI, accesibilidad y fuentes de presentación.
- `2026-09-01-transformation-foundation.md`: correlación y clasificación.
- `2026-09-02-transformation-and-consolidation.md`: agrupación, consolidación y reconciliación.
- `2026-09-03-serving-and-quality.md`: PostgreSQL, idempotencia y pruebas.
- `2026-09-04-api-redis-and-integration.md`: Docker, Redis, API e integración.
- `2026-09-07-observability-and-runtime.md`: métricas, Prometheus, dashboard y runtime.
- `2026-09-08-project-closeout.md`: cierre documental de HRP-93, estado final revisado,
  limitaciones y handoff.

## Norma

- Máximo cinco minutos por persona.
- No incluir datos sensibles ni mensajes completos de Kafka.
- Enlazar tareas Jira y pull requests cuando existan.
- Registrar bloqueos con una acción concreta y una persona responsable.

Usar [`_template.md`](_template.md) para cada nueva daily.

Las dailies del 1, 2, 3, 4 y 7 de septiembre están reconstruidas exclusivamente a
partir de commits y pull requests versionados. No inventan reuniones, responsables ni
decisiones que no estén respaldadas por el repositorio.

No se crean dailies artificiales para el 5 y 6 de septiembre porque no existe actividad
versionada ni evidencia de trabajo en esas fechas.

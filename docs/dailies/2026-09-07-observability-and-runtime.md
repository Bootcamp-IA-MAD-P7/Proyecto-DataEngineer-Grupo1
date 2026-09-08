# Daily — 2026-09-07 — TTL y observabilidad de ingesta

## Naturaleza del registro

Reconstrucción retrospectiva el 2026-09-08 basada en integraciones Git; no es un acta de reunión ni una reconstrucción de horas trabajadas.
La fecha es la de integración en develop; puede diferir de la fecha de autoría.
No se atribuyen conversaciones, aprobaciones personales ni bloqueos sin evidencia.

## Resultado de la jornada

TTL Redis, contador de consumo y duraciones de procesamiento/persistencia MongoDB; endpoint Prometheus, scraper y dashboard Grafana. HRP-87/88 documentan ingesta continua y reinicios.

## Evidencia integrada

| Commit | Integración registrada |
|---|---|
| [f3a952b](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/f3a952b) | HRP-88 docs: document Docker restart policy (#79) |
| [b0b6db6](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/b0b6db6) | HRP-87 docs: document continuous pipeline runtime (#78) |
| [2f9091f](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/2f9091f) | HRP-82 chore: add basic monitoring dashboard (#77) |
| [790e5c4](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/790e5c4) | HRP-81 chore: configure Prometheus (#76) |
| [ac9e872](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/ac9e872) | HRP-80 feat: expose ingestion metrics for Prometheus (#75) |
| [35f3047](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/35f3047) | HRP-79 feat: measure ingestion persistence duration (#74) |
| [40e74b3](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/40e74b3) | HRP-78 feat: measure ingestion processing duration (#73) |
| [201e6e2](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/201e6e2) | HRP-77 feat: add Kafka consumed-message metric (#72) |
| [35c7ee5](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/35c7ee5) | HRP-76 feat: configure Redis partial-state expiration (#70) |

## Límites y decisiones

No hay worker productivo continuo hasta SQL, métricas SQL/Redis/API ni benchmark. Los histogramas tienen solo bucket +Inf; no ofrecen p95/p99 útiles.

## Continuidad

Consultar la [siguiente jornada disponible y el índice](README.md).
Las tareas y estados actuales de Jira no se han consultado en esta revisión.
El historial acredita commits, no asistencia a una daily ni validación de cada criterio.

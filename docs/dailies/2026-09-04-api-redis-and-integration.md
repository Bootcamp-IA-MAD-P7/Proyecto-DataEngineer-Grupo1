# Daily — 2026-09-04 — API, Redis e integración sintética

## Naturaleza del registro

Reconstrucción retrospectiva el 2026-09-08 basada en integraciones Git; no es un acta de reunión ni una reconstrucción de horas trabajadas.
La fecha es la de integración en develop; puede diferir de la fecha de autoría.
No se atribuyen conversaciones, aprobaciones personales ni bloqueos sin evidencia.

## Resultado de la jornada

Compose de app y bases; logs ETL/SQL, CI con PostgreSQL, tests consumer, adapter Redis y endpoints FastAPI, incluidas estadísticas.

## Evidencia integrada

| Commit | Integración registrada |
|---|---|
| [444f47a](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/444f47a) | Merge pull request #69 from Bootcamp-IA-MAD-P7/feature/HRP-86-statistics-endpoint |
| [a0929b6](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/a0929b6) | Merge pull request #67 from Bootcamp-IA-MAD-P7/feature/HRP-75-retrieve-partial-data-redis-etl |
| [e0306a1](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/e0306a1) | Merge pull request #68 from Bootcamp-IA-MAD-P7/feature/HRP-85-search-by-location-profession |
| [ef69376](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/ef69376) | Merge pull request #66 from Bootcamp-IA-MAD-P7/feature/HRP-74-store-partial-person-data-redis |
| [fa156b9](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/fa156b9) | HRP-71 test: add kafka mongodb postgresql e2e coverage (#65) |
| [846b753](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/846b753) | Merge pull request #64 from Bootcamp-IA-MAD-P7/feature/HRP-84-search-person-endpoint |
| [82ae7a2](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/82ae7a2) | Merge pull request #63 from Bootcamp-IA-MAD-P7/feature/HRP-68-kafka-consumer-unit-tests |
| [c39495b](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/c39495b) | Merge pull request #62 from Bootcamp-IA-MAD-P7/feature/HRP-73-configure-redis |
| [a60e03a](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/a60e03a) | Merge pull request #61 from Bootcamp-IA-MAD-P7/feature/HRP-67-database-logging |
| [d072a9e](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/d072a9e) | HRP-83 feat: add PostgreSQL query API skeleton (#60) |
| [3192c5f](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/3192c5f) | HRP-66 fix: reject non finite log durations (#59) |
| [75a8048](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/75a8048) | Merge pull request #58 from Bootcamp-IA-MAD-P7/feature/HRP-66-etl-processing-logs |
| [1773be4](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/1773be4) | Merge pull request #57 from Bootcamp-IA-MAD-P7/feature/HRP-63-docker-compose-app-mongo-postgres |
| [ee977e7](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/ee977e7) | HRP-70 ci: run SQL persistence tests against a real postgres in CI (#56) |

## Límites y decisiones

HRP-71 conecta MongoDB, transformación y PostgreSQL con eventos sintéticos equivalentes a Kafka; no broker real ni Redis. El TTL configurable se incorpora el día 7.

## Continuidad

Consultar la [siguiente jornada disponible y el índice](README.md).
Las tareas y estados actuales de Jira no se han consultado en esta revisión.
El historial acredita commits, no asistencia a una daily ni validación de cada criterio.

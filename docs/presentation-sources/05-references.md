# Bibliografía y trazabilidad para la presentación

**Fecha de consulta:** 2026-09-08. Fuentes oficiales consultadas en esta revisión.
Las páginas de producto pueden evolucionar; las versiones desplegadas se obtienen de
Compose y pyproject, no del número de versión de la documentación online.
No son fuentes el código del generador ni payloads personales.

## Fuentes externas primarias

| ID | Autor y título | Qué fundamenta / límite | Diapositiva |
|---|---|---|---|
| R1 | Confluent: [Python client API](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html) | Consultar poll, commit y configuración del cliente; no demuestra el throughput del proyecto. | 4 |
| R2 | MongoDB: [Unique indexes](https://www.mongodb.com/docs/manual/core/index-unique/) | Fundamenta la restricción compuesta de coordenadas dentro de una colección. | 4 |
| R3 | PostgreSQL Global Development Group: [PostgreSQL 16: constraints](https://www.postgresql.org/docs/16/ddl-constraints.html) | PK, FK y unicidad; no convierte passport en clave única de negocio. | 6 |
| R4 | Redis: [EXPIRE](https://redis.io/docs/latest/commands/expire/) | Expiración y renovación de TTL; la política de 3600 s procede del código propio. | 6 |
| R5 | Prometheus: [Histograms and summaries](https://prometheus.io/docs/practices/histograms/) | Distinguir sum/count y distribución por buckets al interpretar duraciones. | 8 |
| R6 | FastAPI: [Tutorial / User Guide](https://fastapi.tiangolo.com/tutorial/) | Contexto de API, validación y OpenAPI; rutas y errores propios están en el repositorio. | 7 |
| R7 | Docker: [Compose services reference](https://docs.docker.com/reference/compose-file/services/) | Interpretar profiles, healthchecks y restart; no certifica disponibilidad productiva. | 3, 9 |
| R8 | Grafana Labs: [Provision Grafana](https://grafana.com/docs/grafana/latest/administration/provisioning/) | Explicar configuración versionada de datasource/dashboard. | 8 |
| R9 | GitHub: [Understanding GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions) | Contexto de workflows/jobs/checks; no demuestra que el último run esté verde. | 9 |

## Fuentes propias y evidencia primaria

| ID | Fuente | Qué permite afirmar |
|---|---|---|
| P1 | [Código revisado f3a952b](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/tree/f3a952b) | Componentes y configuración presentes en el corte |
| P2 | [PR #33](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/33) / [d1a2393](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/d1a2393) | Frontera raw corregida |
| P3 | [PR #42](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/42) / [0512612](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/0512612) | Decisión operacional de correlación |
| P4 | [PR #65](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/65) / [fa156b9](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/fa156b9) | Prueba E2E sintética, no broker real |
| P5 | [PR #80](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/80) / [275131a](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/275131a) | Primera documentación de cierre integrada |
| P6 | [Dailies](../dailies/README.md) | Evolución por integraciones fechadas |
| P7 | [Matriz](../delivery-evidence.md) | Aceptación declarada y límites separados |
| P8 | [Test harness](../05-test-harness.md) | Último resultado local reportado; no log adjunto ni nuevo run |
| P9 | [Observación HRP-29](../observations/2026-08-27-HRP-29-kafka.md) | Formas observadas en muestra de 20 eventos |
| P10 | [Observación HRP-43](../observations/2026-09-01-HRP-43-person-correlation.md) | Análisis acotado de 2.000 raw; no ground truth de identidad |

## Regla de citación

En cada diapositiva técnica citar P1 o la spec/PR que soporte la implementación y
R1–R9 solo para el concepto general. Las fuentes externas no prueban que una
característica esté implementada aquí. Indicar fecha y alcance en cifras.
No decir «CI verde actual» sin un enlace al run correspondiente.
Los hashes cortos identifican commits, no ramas móviles; las notas actuales
se corresponden con este corte documental.

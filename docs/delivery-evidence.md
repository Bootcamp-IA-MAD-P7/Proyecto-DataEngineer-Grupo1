# Matriz de entrega y evidencia — HRP-93

Corte: 2026-09-08. Responsable de aceptación: Miguel.
La numeración conserva los 19 checks del README anterior; no redefine el briefing.
**Aceptación comunicada: 18/19; frontend excluido.** Aceptado no significa medido,
ejecutado de nuevo ni certificado por esta revisión documental.

| ID / bloque | Requisito | Aceptación | Evidencia y límite técnico |
|---|---|---|---|
| D1 Entrega | GitHub con código documentado | Aceptado | README, guías, specs y PR #80; esta revisión se publica cuando se suba su rama |
| D2 Entrega | Programa Dockerizado conectado a Kafka, procesamiento, MongoDB y SQL | Aceptado | `app`, `etl` y `api` en Compose; Kafka educativo permanece externo |
| D3 Entrega | Demo en vivo | Aceptado | Recorrido ejecutado localmente y runbook reproducible; no se aporta grabación |
| D4 Entrega | Presentación técnica | Aceptado | Fuentes autocontenidas y guion; no equivalen a un deck ya generado |
| D5 Entrega | Kanban del proyecto | Aceptado | Claves HRP y enlace Jira; estados actuales de Jira no consultados |
| E1 Esencial | Consumer en tiempo real y miles de mensajes por segundo | Aceptado | Consumer continuo HRP-30/31; no hay benchmark que certifique ese throughput |
| E2 Esencial | Persistir Kafka en MongoDB | Aceptado | HRP-34; raw e índices; prefijo durable por lote, sin control global de huecos entre lotes |
| E3 Esencial | Agrupar los cinco dominios por persona | Aceptado | HRP-44–51/61/96 y ADR-0006; correlación operacional exacta, no identidad real |
| E4 Esencial | Persistir agrupados en SQL | Aceptado | Worker ETL, esquema, mapper, repositorio y pruebas HRP-56–60/70/71/87 |
| E5 Esencial | Ramas organizadas y commits limpios | Aceptado | Historial de PRs; no se certifican reglas remotas sin consulta |
| E6 Esencial | Código documentado y README en GitHub | Aceptado | Documentos versionados; cambios locales no son automáticamente visibles en GitHub |
| M1 Medio | Sistema de logs | Aceptado | Logs técnicos de ingesta, ETL y SQL; LOG_LEVEL de plantilla no gobierna el logger actual |
| M2 Medio | Tests unitarios | Aceptado | Extensión: 270 unitarios pasan; suite completa histórica: 246 pasan, 21 fallan, 40 omitidos |
| M3 Medio | Aplicación con Compose | Aceptado | Ocho servicios; Kafka externo; ingesta, ETL y API dockerizados |
| A1 Avanzado | Redis como caché intermedia | Aceptado | Estado parcial con Sets, claves opacas y TTL integrado en `etl` |
| A2 Avanzado | Monitorizar consumo, velocidad, procesamiento y persistencia | Aceptado | Tres métricas de ingesta; persistencia medida es MongoDB, no SQL; sin p95/p99 útiles |
| A3 Avanzado | API sobre SQL | Aceptado | Health, búsquedas y estadísticas; sin autenticación ni frontend |
| X1 Experto | Actualización continua de las bases mientras Kafka publica | Aceptado | `app` actualiza MongoDB y `etl` actualiza Redis/PostgreSQL continuamente |
| X2 Experto | Frontend sencillo de consulta | Excluido | No se presenta como implementado ni como parte entregada |

## Interpretación obligatoria

Los límites de D2, E1 y X1 son diferencias entre el enunciado completo y la evidencia
técnica disponible, no simples incidencias de Windows. La decisión del responsable
se registra sin inventar un benchmark ni alta disponibilidad. Si se requiere demostrar
literalmente esos enunciados, hará falta trabajo o evidencia adicional fuera de esta
revisión documental. No se oculta esa diferencia aumentando contadores.

| Bloque | Aceptados / total |
|---|---:|
| Entrega | 5/5 |
| Esencial | 6/6 |
| Medio | 3/3 |
| Avanzado | 3/3 |
| Experto | 1/2 |

## Fuentes de comprobación

- [Arquitectura y runtime](01-architecture.md).
- [Modelo y persistencia](03-data-model.md).
- [Resultados y alcance de tests](05-test-harness.md).
- [Métricas efectivas](06-observability.md).
- [API y privacidad](api-reference.md).
- [Cierre](project-closeout.md) y [revisión documental](documentation-audit.md).

Esta matriz es la fuente canónica de aceptación. Las specs conservan sus criterios
históricos; sus casillas no deben sumarse para reconstruir el progreso del briefing.

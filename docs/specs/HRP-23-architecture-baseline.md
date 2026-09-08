# HRP-23 — Definir arquitectura del proyecto

**Estado de integración (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [5a8dc0c](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/5a8dc0c) / [PR #6](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/6) (2026-08-27).
**Closeout interpretation:** This is the architecture decision scope. The current app runs ingestion; process-worker and frontend are not delivered services.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Original recorded status:** Lista para implementar

**Responsable:** Miguel Redondo Núñez
**Jira:** HRP-23
**Dependencias:** ninguna
**ADRs:** 0001, 0002, 0003 y 0004

## Objetivo

Definir una arquitectura que cubra todos los niveles del briefing sin introducir
complejidad prematura y que permita a cuatro personas trabajar en paralelo.

## Decisión

Se adopta un monolito modular Python desplegado como servicios independientes en
Docker Compose. Cada servicio tiene una responsabilidad única y sus contratos se
mantienen dentro del repositorio:

| Servicio | Responsabilidad | Fuente de verdad |
|---|---|---|
| `ingest-worker` | Consumir Kafka y guardar el mensaje sin modificar | MongoDB `raw_events` |
| `process-worker` | Validar, clasificar, correlacionar y publicar datos curados | PostgreSQL; Redis es temporal |
| `api` | Consultar exclusivamente datos curados | PostgreSQL |
| `dashboard` | Mostrar consultas y métricas sin lógica de negocio | API y Prometheus |
| `prometheus` | Recoger métricas de los servicios | No almacena datos de negocio |

## Criterios de aceptación

- [x] Los límites de Kafka, MongoDB, Redis, PostgreSQL, API y frontend están definidos.
- [x] La propiedad de cada dato y el recorrido raw → curado son explícitos.
- [x] La configuración externa y los secretos no viven en código.
- [x] Las decisiones reversibles y no reversibles tienen ADR.
- [x] El contrato real de Kafka queda bloqueado por evidencia de HRP-29.

## Evidencia prevista

- Documento de arquitectura actualizado.
- ADRs enlazadas.
- Revisión de Anahí, Gaby y Johans sobre los límites de sus componentes.

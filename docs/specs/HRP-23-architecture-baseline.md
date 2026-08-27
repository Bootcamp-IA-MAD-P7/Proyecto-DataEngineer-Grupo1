# HRP-23 — Definir arquitectura del proyecto

**Estado:** Lista para implementar
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

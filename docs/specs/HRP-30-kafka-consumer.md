# HRP-30 — Crear consumer Kafka configurable

**Estado de integración (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [447e017](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/447e017) / [PR #10](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/10) (2026-08-27).
**Closeout interpretation:** See current architecture, runbook and test harness for subsequent changes and runtime limits.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Original recorded status:** En curso

**Responsable:** Anahí
**Jira:** HRP-30
**Dependencias:** HRP-28 finalizada; los topics reales se confirman mediante HRP-29.

## Objetivo

Disponer de un consumer Python configurable que reciba mensajes de topics
autorizados, gestione errores y se cierre limpiamente sin interpretar ni exponer el
payload.

## Contexto y alcance

- Incluye: configuración por entorno, polling, logs técnicos y pruebas unitarias con mocks.
- Excluye: persistencia MongoDB, transformación, clasificación, Docker y decisiones semánticas.
- Supuestos verificables: Kafka y los topics se proporcionan mediante variables autorizadas.
- Riesgos: HRP-29 puede modificar el valor operativo de `KAFKA_TOPICS`, no la interfaz.

## Diseño

`KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_CONSUMER_GROUP` y `KAFKA_TOPICS` se leen del
entorno. `KAFKA_TOPICS` admite una lista separada por comas. El consumer registra
solo topic, partición, offset y tamaño del mensaje. La persistencia raw se añade en
HRP-34 y HRP-35.

## Criterios de aceptación

- [ ] Se puede crear el consumer con configuración válida del entorno.
- [ ] Los topics solo proceden de `KAFKA_TOPICS` autorizado.
- [ ] Un mensaje válido suma un contador técnico sin registrar el payload.
- [ ] Un error Kafka o mensaje sin cuerpo no detiene el bucle.
- [ ] El cierre siempre llama a `consumer.close()`.
- [ ] Pruebas unitarias y comprobaciones de calidad pasan.

## Estrategia de pruebas

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Unitario | Configuración válida y topics configurables | Settings esperados |
| Unitario | Error Kafka y mensaje sin cuerpo | Bucle continúa hasta el siguiente mensaje |
| Unitario | Cierre del consumer | `close()` invocado |
| Manual | Broker autorizado tras HRP-29 | Metadatos técnicos, sin payload |

## Evidencia de cierre

- Rama / PR: pendiente.
- Commit: pendiente.
- Comandos ejecutados y resultado: pendiente.
- Comentario Jira con el resultado: pendiente.

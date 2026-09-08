# HRP-26 — Crear README inicial con objetivo, tecnologías e instrucciones

**Estado de integración (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [73b0cfa](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/73b0cfa) / [PR #4](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/4) (2026-08-27).
**Closeout interpretation:** The initial README is superseded by the HRP-93 closeout README.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Original recorded status:** Implementada; pendiente de integración de la PR

**Responsable:** Miguel Redondo Núñez
**Jira:** HRP-26
**Dependencias:** HRP-23 y HRP-24

## Objetivo

Permitir que una persona nueva entienda el alcance, las reglas de datos, la
arquitectura y el flujo de contribución sin recorrer el código.

## Criterios de aceptación

- [x] El README explica propósito, arquitectura objetivo y alcance por fases.
- [x] La prohibición de inspeccionar el generador es visible y explícita.
- [x] Enlaza la documentación operativa, SDD, specs, ADRs y dailies.
- [x] Describe la rama de integración y la forma de iniciar una tarea.
- [x] Define un punto de entrada común para Codex, Gemini y Claude, estándares
      centralizados y roles/workflows de IA versionados.
- [x] Añade instrucciones reproducibles para arrancar el entorno Kafka educativo
      autorizado, sin inspeccionar el generador ni versionar configuración local.

## Pendiente deliberado

Las instrucciones de MongoDB y PostgreSQL no se publican como definitivas hasta que
estén implementadas y verificadas por sus responsables. El arranque del Kafka
educativo está documentado como dependencia externa autorizada.

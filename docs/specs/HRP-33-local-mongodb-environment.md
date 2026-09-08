# HRP-33 — Preparar MongoDB local para desarrollo

**Integration status (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [9373626](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/9373626) / [PR #27](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/27) (2026-08-31).
**Closeout interpretation:** See current architecture, runbook and test harness for subsequent changes and runtime limits.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Jira:** HRP-33
**Tipo:** habilitador de desarrollo para la persistencia raw
**Dependencias:** Docker Desktop local; no depende de conocer el generador educativo.

## Objetivo

Ofrecer a Anahi un MongoDB local, reproducible y aislado para implementar y
probar la persistencia de mensajes originales de Kafka.

## Alcance

- Un servicio MongoDB de desarrollo con volumen persistente y healthcheck.
- Acceso limitado a `localhost` y URI local documentada.
- Instrucciones minimas de inicio y parada.

## Fuera de alcance

- Dockerizar la aplicacion, PostgreSQL, Redis, Prometheus o Kafka.
- Crear colecciones, indices o interpretar payloads Kafka: eso pertenece a la
  implementacion de HRP-33 y a la evidencia de HRP-29.

## Criterios de aceptación

- [ ] `docker compose -f infra/compose.dev.yml up -d mongo` deja MongoDB sano.
- [ ] El servicio no se publica fuera de `localhost`.
- [ ] `.env.example` contiene la URI local y no incluye secretos.
- [ ] La guia distingue este habilitador del Compose final de la plataforma.

## Evidencia esperada

Salida de `docker compose -f infra/compose.dev.yml ps` mostrando el estado
saludable, enlazada en la PR y en el cierre de Jira.

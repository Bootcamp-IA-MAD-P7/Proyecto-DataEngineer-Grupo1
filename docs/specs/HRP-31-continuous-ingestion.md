# HRP-31 — Configurar el consumer para recibir mensajes continuamente

**Estado de integración (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [69a51ce](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/69a51ce) / [PR #14](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/14) (2026-08-28).
**Closeout interpretation:** See current architecture, runbook and test harness for subsequent changes and runtime limits.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Original recorded status:** En revisión

**Responsable:** Anahí
**Jira:** HRP-31
**Dependencias:** HRP-28 finalizada; HRP-29 finalizada; consumer configurable integrado por HRP-30.
**ADR relacionada:** `docs/adr/0003-evidence-first-data-contract.md`

## Objetivo

Validar que el consumer configurable integrado puede mantener el polling contra el
broker Kafka autorizado hasta recibir una orden de parada, sin exponer valores de
payload y sin detenerse ante errores técnicos recuperables.

## Contexto y alcance

- Incluye: configuración local autorizada, recepción continua, logs técnicos,
  cierre limpio y evidencia de validación manual del broker.
- Excluye: lectura del generador educativo, persistencia MongoDB, Redis,
  PostgreSQL, clasificación de fragmentos, validación de negocio y ETL.
- Supuestos verificables: el runtime educativo publica Kafka en
  `localhost:29092`; el topic observado se suministra como `KAFKA_TOPICS=probando`
  en un `.env` local no versionado.
- Riesgos: el runtime local puede no estar disponible aunque el consumer esté
  correctamente configurado; la evidencia debe distinguir conexión fallida de
  validación satisfactoria.

## Diseño

HRP-30 ya proporciona el bucle de polling, la configuración mediante
`KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_CONSUMER_GROUP` y `KAFKA_TOPICS`, la gestión de
errores de polling y el cierre mediante `consumer.close()`.

HRP-31 no fija el topic en código. Para la validación local autorizada se utiliza
`KAFKA_TOPICS=probando` fuera del repositorio. Los logs se limitan a topic,
partición, offset y tamaño del mensaje. No se imprime, almacena ni versiona el
cuerpo de ningún mensaje.

## Criterios de aceptación

- [x] El consumer configurado mantiene el polling hasta una parada controlada.
- [x] Un error de polling recuperable no interrumpe el bucle.
- [x] El cierre controlado invoca `consumer.close()`.
- [x] La configuración de broker, grupo y topics procede del entorno.
- [x] Una validación manual contra el broker autorizado recibe mensajes desde el
      topic configurado sin mostrar payloads.
- [x] Las comprobaciones de calidad aplicables pasan en la rama de integración.
- [x] La evidencia de ejecución se registra en Jira y la revisión humana de Gaby
      aprueba el alcance antes del cierre.

## Estrategia de pruebas

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Unitario | Polling, error recuperable y cierre | Tests con mocks de HRP-30 pasan. |
| Manual | Broker local autorizado disponible | Logs técnicos, sin payload, y cierre limpio. |
| Manual | Broker local no disponible | Error técnico de conexión; no se afirma recepción de datos. |
| Calidad | Formato, tipos y tests | `pre-commit`, `ruff`, `mypy` y `pytest` pasan. |

## Evidencia de cierre

- Rama / PR: `feature/HRP-31-continuous-ingestion` /
  [PR #14](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/14).
- Commits de evidencia: `6a68d1a` (especificación) y `9e91b5f` (validación del
  runtime Kafka).
- Validación manual (2026-08-28): con el runtime Kafka autorizado disponible en
  `localhost:29092` y `KAFKA_TOPICS=probando` en entorno local no versionado, el
  consumer recibió mensajes durante una ventana acotada, emitió exclusivamente
  metadatos técnicos y se cerró correctamente. No se registraron payloads ni valores
  de mensajes.
- Revisión humana: Gaby aprobó la PR #14 el 2026-08-28 desde el límite de
  Transformation e integración.
- Pendiente: merge en `develop`, verificación posterior y cierre formal de Jira.

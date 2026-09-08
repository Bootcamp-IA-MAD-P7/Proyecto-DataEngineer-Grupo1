# HRP-87 — Continuous pipeline runtime

**Estado de integración (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [b0b6db6](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/b0b6db6) / [PR #78](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/78) (2026-09-07).
**Closeout interpretation:** Integrated scope is continuous ingestion Kafka → MongoDB, not an automatic MongoDB → ETL → SQL worker.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Original recorded status:** En curso; pendiente de revisión humana y merge

**Responsable:** Miguel
**Jira:** HRP-87
**Dependencias:** HRP-30, HRP-31, HRP-34, HRP-50, HRP-55, HRP-63, HRP-80, HRP-81, HRP-82
**ADR relacionada:** `docs/adr/0005-kafka-acknowledgement-after-raw-persistence.md`

## Objetivo

Documentar y validar el modo operativo para mantener el pipeline de ingesta
ejecutándose continuamente mientras el Kafka autorizado sigue enviando datos.

## Contexto y alcance

- Incluye: especificación HRP-87, procedimiento de ejecución continua en el
  runbook y evidencia de que el comportamiento requerido ya se apoya en los
  componentes existentes.
- Excluye: cambios en Kafka, generador educativo, nuevas métricas, dashboards,
  Redis, API, frontend, reglas de negocio, MongoDB RAW, PostgreSQL, ETL,
  correlación, validación o limpieza.
- Supuestos verificables: el runtime Kafka externo está levantado y la aplicación
  recibe `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_TOPICS` y `KAFKA_CONSUMER_GROUP`
  mediante un `.env` local no versionado.
- Riesgos: si Kafka externo no está disponible o la configuración local es
  incorrecta, el contenedor `app` puede reiniciarse. Ese estado debe tratarse
  como incidencia de runtime/configuración, no como autorización para hardcodear
  topics, brokers o datos.

## Diseño

HRP-87 no introduce un nuevo worker. El modo continuo se compone de piezas ya
implementadas y revisadas:

- `src/hr_pro_platform/ingestion/consumer.py` mantiene el polling mientras no se
  recibe señal de parada.
- `src/hr_pro_platform/ingestion/main.py` arranca el endpoint de métricas y
  reintenta el arranque de ingesta ante errores iniciales.
- `infra/compose.dev.yml` ejecuta la aplicación con `restart: unless-stopped`,
  de modo que Docker Compose mantiene el proceso vivo salvo parada explícita.
- HRP-80/81/82 permiten observar el estado del proceso mediante Prometheus y
  Grafana sin exponer payloads ni PII.

El pipeline continuo sigue respetando ADR-0005: MongoDB RAW permanece como
límite durable antes del commit de offsets Kafka. HRP-87 no modifica esa decisión.

## Criterios de aceptación

- [x] Existe un procedimiento documentado para arrancar el pipeline en modo
  continuo.
- [x] El procedimiento usa Compose y el servicio `app` existente.
- [x] Kafka se mantiene como runtime externo autorizado y no se incorpora al repo.
- [x] La configuración Kafka procede de `.env` local o variables de entorno, no
  de valores hardcodeados.
- [x] El proceso puede mantenerse vivo con `restart: unless-stopped`.
- [x] La parada sigue siendo explícita mediante Docker Compose o señales del
  proceso.
- [x] La observabilidad existente permite ver si la ingesta está activa.
- [x] No se versionan payloads, PII, secretos ni `.env`.

## Accessibility and sustainability applicability

- Accessibility: not applicable — HRP-87 define operación backend continua y no
  introduce una interfaz de usuario nueva.
- Sustainability: applicable — se reutiliza el worker y Compose existentes en
  lugar de crear procesos duplicados; la operación continua se mantiene limitada
  al runtime local y a métricas técnicas ya existentes.
- Deferred claims: no se declara throughput garantizado, escalado productivo,
  alta disponibilidad, consumo energético medido, AWS ni operación 24/7 real.

## Estrategia de pruebas

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Configuración | Validar Compose | `docker compose -f infra/compose.dev.yml config --quiet` pasa |
| Configuración | Validar specs | `python scripts/validate_specs.py` pasa |
| Manual | Runtime continuo | Con Kafka externo configurado, `app` queda `Up` y Prometheus/Grafana muestran actividad técnica |
| Manual | Parada controlada | `docker compose -f infra/compose.dev.yml stop app` detiene el proceso sin tocar datos ni volúmenes |

## Evidencia de cierre

- Rama / PR: `feature/HRP-87-continuous-pipeline-runtime` / PR #78.
- Commit: `76f21d1`.
- Comandos ejecutados y resultado: `git diff --check` pasó;
  `python scripts/validate_specs.py` pasó con 58 specs; `docker compose -f
  infra/compose.dev.yml config --quiet` pasó; `pre-commit run --all-files`
  pasó; `ruff check .` pasó; `ruff format --check .` pasó; `mypy src` pasó.
  `pytest` no se ejecutó localmente porque HRP-87 no modifica código Python ni
  tests.
- Comentario Jira con el resultado: pendiente tras revisión, merge y evidencia final.

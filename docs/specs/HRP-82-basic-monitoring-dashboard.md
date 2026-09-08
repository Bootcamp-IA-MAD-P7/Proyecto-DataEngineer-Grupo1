# HRP-82 — Basic monitoring dashboard

**Estado de integración (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [2f9091f](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/2f9091f) / [PR #77](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/77) (2026-09-07).
**Closeout interpretation:** Grafana dashboard is integrated with anonymous local Viewer access. No load results or new runtime screenshot are produced here.

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
**Jira:** HRP-82
**Dependencias:** HRP-77, HRP-78, HRP-79, HRP-80, HRP-81
**ADR relacionada:** N/A

## Objetivo

Crear un dashboard básico y reproducible para visualizar las métricas técnicas
de ingesta ya expuestas por el proyecto.

## Contexto y alcance

- Incluye: servicio Grafana local, datasource Prometheus provisionado,
  dashboard versionado y documentación mínima de uso.
- Excluye: métricas nuevas, alertas, reglas Prometheus, monitorización
  productiva, cambios en Kafka, MongoDB, PostgreSQL, Redis, API, frontend, ETL,
  payloads o generador educativo.
- Supuestos verificables: HRP-80 expone métricas Prometheus-compatible; HRP-81
  configura Prometheus y registra el target `hr-pro-ingestion`.
- Riesgos: los paneles aparecerán sin datos o con el target `DOWN` si la app no
  está ejecutándose, si Kafka externo no está configurado o si Prometheus todavía
  no ha scrapeado muestras suficientes para calcular tasas.

## Diseño

Se añade Grafana OSS como servicio local en `infra/compose.dev.yml`, publicado
solo en `127.0.0.1:3000`. El servicio carga de forma automática:

- datasource Prometheus en `http://prometheus:9090`;
- dashboard `HR Pro Ingestion Overview`.

El dashboard usa únicamente métricas técnicas ya aprobadas:

- `up{job="hr-pro-ingestion"}`;
- `hr_pro_platform_ingestion_messages_consumed_total`;
- `rate(hr_pro_platform_ingestion_messages_consumed_total[1m])`;
- duración media de procesamiento a partir de
  `hr_pro_platform_ingestion_processing_duration_seconds_sum/count`;
- duración media de persistencia MongoDB a partir de
  `hr_pro_platform_ingestion_persistence_duration_seconds_sum/count`.

No se muestran payloads, datos personales, claves de correlación, documentos
MongoDB RAW, registros PostgreSQL ni contenido Kafka.

## Criterios de aceptación

- [x] Existe un dashboard básico versionado.
- [x] El dashboard usa Prometheus como datasource provisionado.
- [x] El dashboard visualiza solo métricas existentes de HRP-77, HRP-78,
  HRP-79, HRP-80 y HRP-81.
- [x] No se crean métricas nuevas ni se alteran nombres, tipos, unidades o
  límites de medición.
- [x] Grafana se publica solo en localhost para desarrollo.
- [x] No se versionan secretos, `.env`, payloads ni PII.
- [x] El generador educativo no se lee, clona, inspecciona ni infiere.
- [x] La documentación explica cómo abrir el dashboard y sus límites runtime.

## Accessibility and sustainability applicability

- Accessibility: applicable in a limited way — Grafana is a third-party local
  UI. HRP-82 does not claim WCAG conformance; it keeps panel names clear and
  avoids relying on hidden payload values.
- Sustainability: applicable — the dashboard reuses existing metrics, has a
  moderate refresh interval (`10s`) and avoids persistent Grafana storage in the
  development stack.
- Deferred claims: no production monitoring, alerting, accessibility
  certification, carbon, energy or cloud deployment claim is made.

## Estrategia de pruebas

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Configuración | Validar Compose | `docker compose -f infra/compose.dev.yml config --quiet` pasa |
| Configuración | Validar specs | `python scripts/validate_specs.py` pasa |
| Manual | Dashboard local | Grafana arranca y carga el dashboard `HR Pro Ingestion Overview` |
| Manual | Prometheus datasource | Los paneles consultan Prometheus; pueden no mostrar datos si la app no está activa |

## Evidencia de cierre

- Rama / PR: `feature/HRP-82-basic-monitoring-dashboard` / PR #77.
- Commit: `5c8043a`.
- Comandos ejecutados y resultado: `git diff --check` pasó;
  `python scripts/validate_specs.py` pasó con 57 specs; `docker compose -f
  infra/compose.dev.yml config --quiet` pasó; validación de sintaxis JSON del
  dashboard pasó; `pre-commit run --all-files` pasó; `ruff check .` pasó;
  `ruff format --check .` pasó; `mypy src` pasó. `pytest` no se ejecutó
  localmente porque HRP-82 no modifica código Python ni tests.
- Comentario Jira con el resultado: pendiente tras revisión, merge y evidencia final.

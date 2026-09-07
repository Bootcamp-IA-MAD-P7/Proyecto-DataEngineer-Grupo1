# HRP-82 — Basic monitoring dashboard

**Estado:** En curso; pendiente de revisión humana y merge
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

- Rama / PR: `feature/HRP-82-basic-monitoring-dashboard` / pendiente.
- Commit: pendiente.
- Comandos ejecutados y resultado: pendiente.
- Comentario Jira con el resultado: pendiente tras revisión, merge y evidencia final.

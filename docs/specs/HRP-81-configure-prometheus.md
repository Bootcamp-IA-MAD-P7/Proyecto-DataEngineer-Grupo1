# HRP-81 — Configure Prometheus

**Estado:** En curso
**Responsable:** Miguel
**Jira:** HRP-81
**Dependencias:** HRP-77, HRP-78, HRP-79, HRP-80
**ADR relacionada:** N/A

## Objetivo

Configurar Prometheus en el Docker Compose de desarrollo para que pueda recopilar
las métricas de ingesta expuestas por HRP-80 en `GET /metrics`.

## Contexto y alcance

- Incluye: servicio Prometheus en `infra/compose.dev.yml`, archivo
  `infra/prometheus/prometheus.yml`, variables documentadas de exposición de
  métricas y runbook mínimo.
- Excluye: creación de métricas nuevas, dashboards, alertas, Grafana, cambios en
  Kafka, MongoDB, PostgreSQL, Redis, API, frontend, ETL o generador educativo.
- Supuestos verificables: la aplicación expone `/metrics` en `app:9464` dentro
  de la red Compose cuando se arranca con el perfil `app`.
- Riesgos: Prometheus puede mostrar el target como `DOWN` si la aplicación no se
  está ejecutando o si Kafka externo no está configurado para el proceso de
  ingesta. Eso no cambia la validez de la configuración de Prometheus.

## Diseño

HRP-80 ya define el endpoint Prometheus-compatible de la aplicación:

- Host interno: `INGESTION_METRICS_HOST=0.0.0.0`
- Puerto interno: `INGESTION_METRICS_PORT=9464`
- Ruta: `/metrics`

HRP-81 añade Prometheus como servicio independiente del Compose de desarrollo y
lo configura para raspar el target `app:9464`. El servicio publica solo la UI de
Prometheus en `127.0.0.1:9090` para validación local. No se añaden credenciales,
volúmenes persistentes de métricas, reglas de alertado ni dashboards.

## Criterios de aceptación

- [x] `infra/compose.dev.yml` incluye un servicio Prometheus.
- [x] Prometheus usa configuración versionada en `infra/prometheus/prometheus.yml`.
- [x] El scrape job apunta a `/metrics` del servicio `app` en la red interna de
  Compose.
- [x] `.env.example` documenta las variables de exposición de métricas de la
  aplicación.
- [x] No se añade Kafka educativo, generador, payloads, secretos ni datos reales.
- [x] No se modifica la lógica de métricas ya aprobada por HRP-77, HRP-78,
  HRP-79 y HRP-80.
- [x] Documentación de uso y validación actualizada.

## Accessibility and sustainability applicability

- Accessibility: not applicable — HRP-81 no introduce una interfaz de usuario
  final; solo configura un servicio técnico local de observabilidad.
- Sustainability: applicable — el scrape interval se mantiene moderado (`15s`) y
  no se configura retención persistente local, evitando almacenamiento innecesario
  para el entorno de desarrollo.
- Deferred claims: no se declara monitorización productiva, alertado, dashboard,
  consumo energético medido ni conformidad de UI.

## Estrategia de pruebas

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Configuración | Validar Compose | `docker compose -f infra/compose.dev.yml config --quiet` pasa |
| Configuración | Validar specs | `python scripts/validate_specs.py` pasa |
| Manual | Prometheus local | Prometheus arranca y muestra el target `hr-pro-ingestion`; el target solo estará `UP` cuando `app` esté ejecutando `/metrics` |

## Evidencia de cierre

- Rama / PR: `feature/HRP-81-configure-prometheus` / pendiente
- Commit: pendiente
- Comandos ejecutados y resultado: pendiente
- Comentario Jira con el resultado: pendiente tras revisión, merge y evidencia final

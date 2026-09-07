# HRP-88 — Docker service restart policy

**Estado:** En curso; pendiente de revisión humana y merge
**Responsable:** Miguel
**Jira:** HRP-88
**Dependencias:** HRP-63, HRP-73, HRP-81, HRP-82
**ADR relacionada:** N/A

## Objetivo

Garantizar que los servicios locales del Docker Compose de desarrollo tienen una
política explícita de reinicio automático para recuperarse de caídas de
contenedor durante la demo y la ejecución local.

## Contexto y alcance

- Incluye: revisión de `infra/compose.dev.yml`, evidencia de política de
  reinicio por servicio y documentación operativa mínima.
- Excluye: alta disponibilidad productiva, Kubernetes, AWS, cambios en Docker
  images, puertos, volúmenes, credenciales, healthchecks, Kafka educativo,
  aplicación, MongoDB RAW, PostgreSQL, Redis, Prometheus, Grafana, API,
  frontend, ETL, métricas o dashboards.
- Supuestos verificables: Docker Compose respeta `restart: unless-stopped` para
  reiniciar contenedores tras fallos mientras no hayan sido detenidos
  explícitamente por el usuario.
- Riesgos: esta política reinicia contenedores, pero no garantiza disponibilidad
  productiva ni corrige errores de configuración. Si falta Kafka externo o `.env`
  local, la app puede reiniciarse repetidamente hasta que se corrija el entorno.

## Diseño

La revisión confirma que los servicios locales relevantes ya tienen política
explícita:

| Servicio | Política |
|---|---|
| `app` | `restart: unless-stopped` |
| `mongo` | `restart: unless-stopped` |
| `postgres` | `restart: unless-stopped` |
| `redis` | `restart: unless-stopped` |
| `prometheus` | `restart: unless-stopped` |
| `grafana` | `restart: unless-stopped` |

No se modifica `infra/compose.dev.yml` porque el criterio funcional ya está
implementado. HRP-88 queda como tarea de trazabilidad/evidencia y runbook.

## Criterios de aceptación

- [x] Todos los servicios locales relevantes tienen una política de reinicio
  explícita.
- [x] La política elegida es `unless-stopped` para evitar reinicios después de
  una parada manual deliberada.
- [x] La configuración queda limitada a Docker Compose local.
- [x] No se introducen cambios funcionales en aplicación, datos, métricas ni
  servicios.
- [x] No se añaden dependencias, servicios nuevos, puertos, volúmenes ni
  credenciales.
- [x] `.env` sigue sin versionarse.
- [x] La validación de Compose pasa.

## Accessibility and sustainability applicability

- Accessibility: not applicable — HRP-88 no introduce interfaz de usuario ni flujo
  accesible.
- Sustainability: applicable in a limited operational sense — `unless-stopped`
  evita reinicios inesperados tras paradas manuales y no añade procesos
  duplicados.
- Deferred claims: no se declara alta disponibilidad, tolerancia a fallos
  productiva, AWS, consumo energético medido ni resiliencia 24/7.

## Estrategia de pruebas

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Configuración | Revisar Compose | Todos los servicios relevantes declaran `restart: unless-stopped` |
| Configuración | Validar Compose | `docker compose -f infra/compose.dev.yml config --quiet` pasa |
| Configuración | Validar specs | `python scripts/validate_specs.py` pasa |

## Evidencia de cierre

- Rama / PR: `feature/HRP-88-docker-service-restart-policy` / PR #79.
- Commit: `e60e73e`.
- Comandos ejecutados y resultado: `git diff --check` pasó;
  `python scripts/validate_specs.py` pasó con 58 specs; `docker compose -f
  infra/compose.dev.yml config --quiet` pasó; `pre-commit run --all-files`
  pasó; `ruff check .` pasó; `ruff format --check .` pasó; `mypy src` pasó.
  `pytest` no se ejecutó localmente porque HRP-88 no modifica código Python ni
  tests.
- Comentario Jira con el resultado: pendiente tras revisión, merge y evidencia final.

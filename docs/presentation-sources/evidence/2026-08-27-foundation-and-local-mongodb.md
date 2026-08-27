# Evidencia de presentación — Fundación y MongoDB local

**Fecha:** 2026-08-27
**Alcance:** Sprint 1 / habilitador de Sprint 2
**Estado:** verificación local completada; las PRs indicadas siguen sujetas a revisión humana.

## Qué demuestra este hito

El equipo ya dispone de una base profesional para desarrollar de forma trazable:
gobernanza Git, especificaciones, validación de calidad y un servicio MongoDB local
reproducible. Esto no demuestra todavía el pipeline completo Kafka a PostgreSQL.

## Evidencia verificable

| Elemento | Evidencia | Qué demuestra |
|---|---|---|
| Flujo de PR y calidad | PR #1 fusionada | Plantilla en inglés, trazabilidad Jira y checks de calidad. |
| Observación Kafka | PR #2 | Plantilla segura de observación; no contiene una observación real. |
| Cierre de jornada | PRs #3 y #5 | Daily y automatización revisable de fuentes de presentación. |
| Onboarding de equipo | PR #4 | Guías de trabajo asistido por IA y SDD. |
| Arnés SDD | PR #6 | Validación automática de estructura de specs en CI. |
| MongoDB local | PR #7 | Compose mínimo para desbloquear persistencia raw. |

## Validación de MongoDB local

Ejecutado desde la raíz del repositorio:

```text
docker compose -f infra/compose.dev.yml config --quiet
docker compose -f infra/compose.dev.yml up -d mongo
docker compose -f infra/compose.dev.yml ps
docker compose -f infra/compose.dev.yml exec -T mongo mongosh --quiet --eval "db.adminCommand('ping').ok"
```

Resultado observado: servicio `hr-pro-mongo-dev` en estado `healthy`, expuesto solo
en `127.0.0.1:27017`; el comando de ping devolvió `1`.

Como comprobación adicional pasaron `ruff check .`, `ruff format --check .`,
`mypy src` y `pytest`.

## Estado operativo asociado

- HRP-20 y HRP-28 están finalizadas.
- HRP-21 y HRP-23 están en revisión.
- HRP-24 y HRP-25 siguen bloqueadas de forma explícita por la observación real de
  HRP-29.
- HRP-29, HRP-30 y HRP-33 están en curso.

## Restricciones que deben aparecer en la presentación

- El generador educativo se trata como caja negra: no se ha leído ni analizado su
  código.
- Esta evidencia no contiene payloads de Kafka, secretos ni datos personales.
- MongoDB local habilita desarrollo; no prueba aún el pipeline esencial completo.

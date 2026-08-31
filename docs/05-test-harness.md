# Arnés de validación

El arnés permite demostrar que el pipeline cumple el briefing sin depender del
generador educativo ni de un entorno manual irrepetible. Es un contrato ejecutable:
fixtures autorizados + pruebas + datos de salida esperados + métricas.

## Mapa del harness

No se añade una capa documental distinta para cada concepto: este repositorio usa las
guías existentes para prevenir errores y los sensores para detectarlos antes del merge.

| Capa | Artefactos canónicos | Función |
|---|---|---|
| Guías | `AGENTS.md`, arquitectura, contrato, SDD, ADRs y specs | Delimitan contexto, reglas y alcance antes de trabajar |
| Sandbox | Rama de tarea + entorno local + Docker Compose cuando exista | Aísla cambios y servicios de desarrollo |
| Sensores | Pre-commit, `validate_specs.py`, Ruff, mypy, pytest, CI y revisión humana | Rechazan errores y desviaciones comprobables |
| Evidencia persistente | Spec, pruebas, PR, daily y comentario Jira | Mantiene el estado fuera de la conversación del agente |

La regla es deliberadamente simple: no se añade RAG, un servicio extra o una librería
de guardrails mientras las guías y sensores actuales sean suficientes.

## Pirámide de pruebas

| Capa | Objetivo | Dependencias | Ejecución |
|---|---|---|---|
| Unitarias | Reglas puras de clasificación, validación y correlación | Ninguna | Cada commit |
| Contrato | Validar eventos contra el contrato observado | Fixtures JSON | Cada PR |
| Integración | MongoDB, Redis y PostgreSQL reales | Docker Compose/test containers | Cada PR relevante |
| E2E | Kafka fixture → raw → curado | Stack local completo | Antes de demo/release |
| Carga | Medir volumen, latencia y errores | Reproductor de fixtures | Sprint de rendimiento |

## Política de fixtures

1. HRP-29 observa datos desde Kafka sin inspeccionar el generador.
2. Se extrae el mínimo ejemplo estructural necesario.
3. Se eliminan o reemplazan valores que no sean esenciales para probar el esquema.
4. El fixture referencia la spec y la fecha de observación en un comentario o README.
5. Nunca se comitean capturas de tráfico completas, secretos o datos locales.

## Matriz mínima de comportamiento

| ID | Caso | Nivel | Resultado esperado |
|---|---|---|---|
| H-01 | Evento válido por categoría | Unitario/contrato | Clasificación correcta |
| H-02 | Campo obligatorio ausente | Unitario | Error aislado y auditado |
| H-03 | Payload no parseable | Unitario/integración | Consumer continúa |
| H-04 | Repetición de topic-partition-offset | Integración | Un único raw event |
| H-05 | Fragmentos de una persona desordenados | Integración | Persona correcta al completarse |
| H-06 | Claves de correlación inconsistentes | Unitario/integración | No se mezcla información |
| H-07 | Redis expira estado parcial | Integración | Sin corrupción; reproceso posible |
| H-08 | Reinicio del worker | E2E | Sin duplicados ni pérdida observable |
| H-09 | Falla MongoDB/PostgreSQL transitoria | Integración | Reintento/registro y métrica |
| H-10 | Carga sostenida de fixtures | Carga | Métricas de consumo y latencia |
| H-11 | MongoDB falla antes de persistir | Integración prevista para HRP-34 | La propuesta ADR-0005 impide confirmar el offset |

## Convención de nombres

```text
tests/unit/test_classifier.py
tests/contract/test_kafka_event_contract.py
tests/integration/test_raw_event_repository.py
tests/e2e/test_kafka_to_postgres.py
tests/fixtures/observed/<categoria>-valid.json
tests/fixtures/invalid/<caso>.json
```

Cada prueba tiene nombre de comportamiento: `test_duplicate_offset_is_not_persisted_twice`,
no `test_case_1`.

Cuando una spec tenga varios criterios de aceptación que afecten comportamiento, estos
se identifican como `AC-01`, `AC-02`, etc. El nombre o docstring de la prueba debe
referenciar ese identificador. No se exige esta convención a las specs de diseño ya
existentes ni se inventan pruebas antes de que exista implementación.

## Accessibility and sustainable-delivery evidence

When a task introduces a user-facing flow, the harness includes an automated
accessibility check against the rendered interface and a documented keyboard-only
manual check. Advanced widgets, dynamic updates, dialogs and charts also require
screen-reader validation when applicable. Charts and status indicators need an
equivalent textual or tabular alternative.

Tasks affecting APIs, frontend delivery, Docker or AWS document the applicable
efficiency evidence: for example bounded API responses, request count, transfer size,
query cost, container resources or retained data. No carbon score, energy saving or
deployment claim is accepted without measured evidence and its boundary.

## Comandos de calidad

```powershell
pre-commit run --all-files
python scripts/validate_specs.py
ruff check .
ruff format --check .
mypy src
pytest
```

La cobertura de línea parte de un umbral exigible del 75 %. Es un suelo inicial: no
se reduce para hacer pasar una PR y debe elevarse gradualmente cuando crezca el código.
La cobertura no sustituye las pruebas de comportamiento ni demuestra por sí sola que
el pipeline sea correcto.

La configuración de Compose de desarrollo también se valida sin arrancar servicios:

```powershell
docker compose -f infra/compose.dev.yml config --quiet
```

Los comandos de integración, E2E y carga se documentarán en `docs/07-runbook.md`
cuando sus servicios existan. Una tarea no puede afirmar que están ejecutados antes.

# Arnés de validación

El arnés permite demostrar que el pipeline cumple el briefing sin depender del
generador educativo ni de un entorno manual irrepetible. Es un contrato ejecutable:
fixtures autorizados + pruebas + datos de salida esperados + métricas.

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

## Comandos de calidad

```powershell
pre-commit run --all-files
ruff check .
ruff format --check .
mypy src
pytest
```

Los comandos de integración, E2E y carga se documentarán en `docs/07-runbook.md`
cuando sus servicios existan. Una tarea no puede afirmar que están ejecutados antes.

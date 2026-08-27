# Paquete de tarea — HRP-29

**Estado:** Borrador
**Responsable:** Anahí
**Revisor humano:** Gaby
**Jira:** HRP-29
**Spec:** `docs/specs/HRP-29-*.md`
**Rama prevista:** `feature/HRP-29-observacion-kafka`

## Resultado esperado

Registrar una observación reproducible y minimizada del topic: metadatos Kafka,
clases de mensaje, claves, tipos, nulos, identificador de correlación, orden y
repeticiones. La evidencia permite actualizar el contrato sin revelar PII.

## Contexto autorizado

- Briefing / documento: requisitos esenciales y README público autorizado.
- Documentación local relevante: `docs/02-data-contract.md`, `docs/01-architecture.md`, ADR-0003.
- Evidencia Kafka observada (si aplica): pendiente de registrar; no sustituir con ejemplos del README.
- Decisiones o ADRs relacionadas: `docs/adr/0003-evidence-first-data-contract.md`.

## Dependencias y límites

- Depende de: HRP-28 completada; broker y configuración autorizada accesibles.
- No incluye: consumer de producción, persistencia MongoDB ni lectura del generador.
- Riesgo o incógnita: topic, key de correlación y campos exactos no están confirmados.
- Restricción: no leer, clonar ni analizar el generador educativo.

## Petición al asistente

**Rol:** Diseñador de pruebas o analista de spec.
**Pregunta concreta:** ¿Qué observaciones mínimas y no sensibles hacen falta para que HRP-24 pueda fijar un contrato inicial?
**Formato de salida esperado:** tabla de campos de observación, casos límite y checklist de evidencia.
**Criterios con los que se evaluará:** rúbrica de `docs/ai/evaluation-rubric.md` y ausencia de supuestos sobre payload.

## Revisión humana del resultado

- [ ] Hechos y supuestos están separados.
- [ ] Las rutas y referencias citadas existen.
- [ ] No se inventan campos, topics o comportamientos de Kafka.
- [ ] La propuesta respeta alcance y seguridad.
- [ ] Se ha aplicado o descartado el resultado, indicando motivo.

## Registro del uso de IA

- Herramienta / rol:
- Fecha:
- Salida resumida:
- Decisión humana:
- Revisor:

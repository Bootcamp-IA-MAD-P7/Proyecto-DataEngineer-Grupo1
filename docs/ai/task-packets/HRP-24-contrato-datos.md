# Paquete de tarea — HRP-24

**Estado:** Borrador  
**Responsable:** Gaby  
**Revisor humano:** Anahí  
**Jira:** HRP-24  
**Spec:** `docs/specs/HRP-24-*.md`  
**Rama prevista:** `feature/HRP-24-contrato-datos`

## Resultado esperado

Actualizar el contrato de datos con evidencia observada, reglas de clasificación y
validación, marcando claramente los elementos pendientes.

## Contexto autorizado

- Briefing / documento: requisitos de agrupación de Personal, Location, Professional, Bank y Net Data.
- Documentación local relevante: `docs/02-data-contract.md`, `docs/03-data-model.md`, ADR-0003.
- Evidencia Kafka observada (si aplica): pendiente de HRP-29.
- Decisiones o ADRs relacionadas: `docs/adr/0003-evidence-first-data-contract.md`.

## Dependencias y límites

- Depende de: HRP-29.
- No incluye: implementar el ETL ni declarar como real un esquema no observado.
- Riesgo o incógnita: los nombres de campos y la key de correlación definitiva.
- Restricción: no leer, clonar ni analizar el generador educativo.

## Petición al asistente

**Rol:** Analista de spec.  
**Pregunta concreta:** Con la evidencia HRP-29, ¿qué contrato mínimo permite validar y agrupar sin inventar semántica?  
**Formato de salida esperado:** propuesta de criterios de aceptación y huecos abiertos.  
**Criterios con los que se evaluará:** rúbrica de `docs/ai/evaluation-rubric.md`, revisión Anahí y trazabilidad a HRP-29.

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

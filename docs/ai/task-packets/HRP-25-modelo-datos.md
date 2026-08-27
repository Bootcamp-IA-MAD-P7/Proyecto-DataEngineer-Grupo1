# Paquete de tarea — HRP-25

**Estado:** Borrador  
**Responsable:** Johans  
**Revisor humano:** Gaby  
**Jira:** HRP-25  
**Spec:** `docs/specs/HRP-25-*.md`  
**Rama prevista:** `feature/HRP-25-modelo-datos`

## Resultado esperado

Definir una propuesta de modelo MongoDB/PostgreSQL que mantenga eventos raw,
estado temporal y registros curados trazables e idempotentes, validada contra el
contrato disponible.

## Contexto autorizado

- Briefing / documento: requisitos de MongoDB, SQL y agrupación por persona.
- Documentación local relevante: `docs/01-architecture.md`, `docs/02-data-contract.md`, `docs/03-data-model.md`.
- Evidencia Kafka observada (si aplica): pendiente de HRP-29 y consolidación HRP-24.
- Decisiones o ADRs relacionadas: ADR-0001, ADR-0002 y ADR-0003.

## Dependencias y límites

- Depende de: HRP-23 y HRP-24; HRP-24 depende de HRP-29.
- No incluye: crear tablas finales ni codificar la persistencia.
- Riesgo o incógnita: identidad canónica, cardinalidades y tipos definitivos.
- Restricción: no leer, clonar ni analizar el generador educativo.

## Petición al asistente

**Rol:** Revisor de arquitectura.  
**Pregunta concreta:** ¿La propuesta mantiene separación raw/temporal/curada, trazabilidad e idempotencia sin fijar datos no observados?  
**Formato de salida esperado:** riesgos, decisiones que requieren ADR y pruebas de persistencia.  
**Criterios con los que se evaluará:** rúbrica de `docs/ai/evaluation-rubric.md` y revisión Gaby.

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


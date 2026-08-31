# Paquete de tarea — HRP-52

**Estado:** Borrador
**Responsable:** Johans
**Revisor humano:** Miguel
**Jira:** HRP-52
**Spec:** `docs/specs/HRP-52-tablas-relaciones.md`
**Rama prevista:** `feature/HRP-52-tablas-relaciones`

## Resultado esperado

Diseño relacional documentado y revisable de las tablas PostgreSQL ya propuestas en
HRP-25: claves primarias, claves foráneas candidatas, índices técnicos candidatos y
convención de nombres, sin fijar una clave de correlación de negocio ni crear SQL.

## Contexto autorizado

- Briefing / documento: tarea Jira HRP-52, hija de HRP-39.
- Documentación local relevante: `docs/specs/HRP-25-modelo-datos.md`,
  `docs/03-data-model.md`, `docs/adr/0002-raw-and-curated-storage.md`,
  `docs/adr/0006-person-correlation-key.md`.
- Evidencia Kafka observada (si aplica): la misma de HRP-24/HRP-29; no se realizó
  observación nueva para HRP-52.
- Decisiones o ADRs relacionadas: ADR-0002, ADR-0006 (permanece `Proposed`).

## Dependencias y límites

- Depende de: HRP-25 (fusionada, PR #18/#19). Sin enlace formal "depende de" en
  Jira, pero condicionada por el comentario de Miguel en HRP-52 exigiendo
  coherencia con el modelo global.
- No incluye: crear tablas reales, SQL, migraciones, Docker ni ETL (eso es HRP-54 y
  HRP-53, que HRP-52 bloquea).
- Riesgo o incógnita: cardinalidad real entre `employees` y las tablas dependientes,
  pendiente de ADR-0006.
- Restricción: no leer, clonar ni analizar el generador educativo.

## Petición al asistente

**Rol:** Revisor/diseñador de arquitectura de datos (serving-engineer).
**Pregunta concreta:** ¿El diseño de claves e índices formaliza HRP-25 sin fijar una
cardinalidad o restricción única que ADR-0006 no haya aprobado?
**Formato de salida esperado:** tablas de claves/índices por entidad, diagrama de
relaciones candidatas y lista de lo que sigue pendiente.
**Criterios con los que se evaluará:** coherencia con HRP-25, ausencia de reglas de
negocio inventadas, revisión de Miguel.

## Revisión humana del resultado

- [ ] Hechos y supuestos están separados.
- [ ] Las rutas y referencias citadas existen.
- [ ] No se inventan campos, topics o comportamientos de Kafka.
- [ ] La propuesta respeta alcance y seguridad.
- [ ] Se ha aplicado o descartado el resultado, indicando motivo.

## Registro del uso de IA

- Herramienta / rol: Claude Code, rol de revisor/diseñador de arquitectura de datos
  (serving-engineer).
- Fecha: 2026-08-31.
- Salida resumida: formalización de claves primarias, claves foráneas candidatas,
  índices técnicos y convención de nombres para las tablas PostgreSQL ya propuestas
  en HRP-25, en `docs/specs/HRP-52-tablas-relaciones.md`, sin resolver la clave de
  correlación de persona (ADR-0006 permanece `Proposed`).
- Decisión humana: pendiente.
- Revisor: Miguel (pendiente de revisión).

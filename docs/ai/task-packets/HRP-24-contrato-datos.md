# Paquete de tarea — HRP-24

**Estado:** En curso — implementación documental autorizada; cierre no aprobado
**Responsable:** Gaby
**Revisor humano:** Anahí
**Jira:** HRP-24
**Spec:** `docs/specs/HRP-24-observed-data-contract.md`
**Rama prevista:** `feature/HRP-24-contrato-datos`

## Resultado esperado

Actualizar el contrato de datos con evidencia observada, reglas de clasificación y
validación, marcando claramente los elementos pendientes.

## Contexto autorizado

- Briefing / documento: requisitos de agrupación de Personal, Location, Professional, Bank y Net Data.
- Documentación local relevante: `docs/02-data-contract.md`, `docs/03-data-model.md`, ADR-0003.
- Evidencia Kafka observada: `docs/observations/2026-08-27-HRP-29-kafka.md`,
  revisada, aprobada y disponible en `develop`.
- Decisiones o ADRs relacionadas: `docs/adr/0003-evidence-first-data-contract.md`.

## Dependencias y límites

- Dependencia resuelta: HRP-29 completada.
- No incluye: implementar el ETL ni declarar como real un esquema no observado.
- Riesgo o incógnita: la estabilidad futura y semántica de los campos observados, y
  la key de correlación definitiva.
- Restricción: no leer, clonar ni analizar el generador educativo.

## Petición al asistente

**Rol:** Analista de spec.
**Pregunta concreta:** Con la evidencia HRP-29, ¿qué contrato mínimo permite clasificar
conformidad provisional sin inventar semántica ni autorizar agrupación de personas?
**Formato de salida esperado:** propuesta de criterios de aceptación y huecos abiertos.
**Criterios con los que se evaluará:** rúbrica de `docs/ai/evaluation-rubric.md`, revisión Anahí y trazabilidad a HRP-29.

## Revisión humana del resultado

- [x] Hechos y supuestos están separados.
- [x] Las rutas y referencias citadas existen.
- [x] No se inventan campos, topics o comportamientos de Kafka.
- [x] La propuesta respeta alcance y seguridad.
- [x] El resultado ha sido revisado y aceptado por Gaby como base documental.

La aceptación de la propuesta no aprueba el cierre de HRP-24. Anahí mantiene la
responsabilidad de revisión humana del cambio documental final.

## Registro del uso de IA

- Herramienta / rol: Codex — analista de spec.
- Fecha: 2026-08-28.
- Salida resumida: contrato estructural provisional basado únicamente en HRP-29, con
  variantes A–E neutrales y correlación, agrupación, ordering y semántica pendientes.
- Decisión humana: Gaby revisó y aceptó la propuesta como base para la implementación
  documental; no autorizó el cierre de HRP-24.
- Revisor: Gaby para la propuesta; Anahí mantiene la revisión humana final.

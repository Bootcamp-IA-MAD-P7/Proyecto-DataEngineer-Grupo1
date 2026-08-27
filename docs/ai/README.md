# Capa agéntica supervisada

Esta carpeta convierte el uso de asistentes de IA en un proceso reproducible y auditable. No añade un agente autónomo al pipeline de datos: los asistentes son ayudantes de desarrollo bajo control humano.

## Regla principal

Un asistente puede proponer, analizar y redactar. Una persona del equipo decide, aprueba, ejecuta acciones externas y cierra tareas.

No se le da acceso ni se le pide que lea, clone, infiera o reconstruya el código del generador educativo. Los únicos datos válidos para diseño son el briefing, el README público autorizado y observaciones reales de Kafka registradas por HRP-29.

## Flujo de uso

1. La persona responsable crea el paquete de tarea desde [`task-packet-template.md`](task-packet-template.md) o ejecuta `./scripts/new-task-packet.ps1 -JiraKey HRP-XX -Slug resumen`.
2. Rellena el contexto mínimo: Jira, spec, dependencias, límites y evidencia disponible.
3. Elige un rol de [`prompts/`](prompts/) y pide una propuesta acotada.
4. Evalúa el resultado con la [`evaluation-rubric.md`](evaluation-rubric.md).
5. La persona responsable aplica solo los cambios aceptados, ejecuta el arnés y los somete a PR.
6. Un revisor humano valida la spec, pruebas y evidencia antes de actualizar Jira.

## Roles disponibles

| Rol | Aporta | No puede decidir |
|---|---|---|
| Analista de spec | Ambigüedades, criterios y dependencias | Contrato real sin observación Kafka |
| Revisor de arquitectura | Límites, ADR y riesgos | Cambios de arquitectura sin aprobación |
| Diseñador de pruebas | Casos, fixtures y huecos de cobertura | Inventar payloads como hechos |
| Revisor de PR | Coherencia entre diff, spec y tests | Aprobar, fusionar o cerrar por sí mismo |
| Coordinador de sprint | Resumen, riesgos y siguiente paso | Cambiar estados Jira sin persona responsable |
| Curador de presentación | Evidencias y relato para NotebookLM | Presentar planes como resultados |

Lee [`agent-charter.md`](agent-charter.md) y [`human-approval-policy.md`](human-approval-policy.md) antes del primer uso.

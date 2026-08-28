# Especificaciones de trabajo

Cada tarea que cambie comportamiento, infraestructura, contrato de datos, modelo o
operación debe tener una spec antes de empezar a implementarse.

## Convención

`HRP-XX-nombre-corto.md`

Ejemplos:

- `HRP-23-architecture-baseline.md`
- `HRP-30-kafka-consumer.md`
- `HRP-36-idempotent-raw-events.md`

## Estado de una spec

- **Borrador**: puede contener incógnitas explícitas.
- **Lista para implementar**: tiene criterios de aceptación, pruebas y dependencias.
- **Implementada**: enlaza código/PR y evidencia de validación.
- **Sustituida**: referencia la spec o ADR que la reemplaza.

No se usa una spec como sustituto de la observación real. HRP-29 ya aportó evidencia
obtenida del broker; el contrato Kafka sigue siendo provisional por el alcance acotado
de esa observación y debe mantener explícitas las incógnitas no demostradas.

Usa [la plantilla](template.md) para nuevas tareas.

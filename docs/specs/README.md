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

No se usa una spec como sustituto de la observación real. En especial, el contrato de
Kafka seguirá siendo provisional hasta que HRP-29 aporte evidencia obtenida del broker.

Usa [la plantilla](template.md) para nuevas tareas.

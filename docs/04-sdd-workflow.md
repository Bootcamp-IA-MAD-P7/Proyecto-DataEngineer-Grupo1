# Flujo SDD (Specification-Driven Development)

## Regla de trabajo

Ninguna tarea de implementación se inicia sin una especificación breve y criterios de aceptación verificables.

## Ciclo obligatorio

1. Abrir o seleccionar una tarea Jira.
2. Crear o actualizar su spec en `docs/specs/`.
3. Definir criterios de aceptación y casos de prueba.
4. Crear una rama `feature/HRP-XX-descripcion`.
5. Implementar el cambio mínimo necesario.
6. Ejecutar el arnés local de calidad.
7. Abrir pull request y vincularlo con Jira.
8. Obtener revisión de otra persona.
9. Actualizar documentación y cerrar la tarea.

## Definition of Ready

Una tarea puede empezar si tiene responsable, objetivo, dependencia conocida, criterios de aceptación y spec asociada cuando afecta comportamiento técnico.

## Definition of Done

- Código y documentación actualizados.
- Pruebas relevantes añadidas o justificadamente no aplicables.
- Validaciones automáticas en verde.
- Pull request revisada por otra persona.
- Tarea Jira actualizada.


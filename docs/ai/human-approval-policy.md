# Política de aprobación humana

## Principio

La responsabilidad del producto y de los datos permanece en el equipo. La IA no es un aprobador ni una fuente de verdad.

## Aprobaciones requeridas

| Acción | Aprueba |
|---|---|
| Crear o modificar una spec | Responsable de la tarea |
| Adoptar una decisión arquitectónica o de datos | Responsable + revisor; ADR si es duradera |
| Añadir fixture basado en Kafka | Anahí o Gaby, con evidencia HRP-29 y revisión |
| Abrir o fusionar PR | Autor + revisor distinto; CI en verde |
| Cerrar una tarea Jira | Responsable, tras merge y evidencia verificable |
| Crear tag/release o cambiar protección de rama | Miguel, tras acuerdo del equipo |
| Añadir credenciales o cambiar servicios externos | Persona responsable del servicio, nunca en Git |

## Evidencia mínima antes de aprobar

- La spec sigue siendo correcta y está enlazada.
- Los hechos observados se distinguen de los supuestos.
- Los tests relevantes y los controles de calidad han pasado.
- No hay secretos, datos sensibles ni material del generador educativo.
- Existe una reversión razonable o se ha documentado por qué no aplica.

## Registro

Registrar el uso de IA solo cuando haya afectado una decisión, diseño, prueba o texto que llegue a PR: rol, artefactos consultados, conclusión y nombre del revisor. No se registran conversaciones que contengan información sensible.

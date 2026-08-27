# Runbook operativo

## Inicio de un desarrollo

1. Actualizar `develop`.
2. Revisar la tarea Jira y su spec.
3. Crear rama asociada.
4. Ejecutar las comprobaciones locales antes de abrir PR.

## Incidencia de datos

1. Localizar el evento con sus metadatos Kafka en `raw_events`.
2. Consultar `processing_audit`.
3. Determinar si el error es de contrato, clasificación, agrupación o almacenamiento.
4. Añadir fixture de regresión antes de corregir la lógica.
5. Registrar la decisión en una ADR si cambia la estrategia de datos.

## Incidencia de infraestructura

1. Consultar logs del servicio.
2. Comprobar conectividad a Kafka y estado de contenedores.
3. No eliminar volúmenes ni datos sin acuerdo explícito del equipo.


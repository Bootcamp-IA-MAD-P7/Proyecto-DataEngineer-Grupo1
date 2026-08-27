# Modelo de datos

## MongoDB: zona raw

Colecciones previstas:

- `raw_events`: evento original, metadatos Kafka, fecha de recepción y estado de proceso.
- `invalid_events`: evento que no supera la validación, junto al motivo.
- `processing_audit`: trazabilidad de transformación y carga.

Índice técnico previsto para evitar duplicados: `topic + partition + offset`.

## PostgreSQL: zona curada

Tablas previstas:

- `employees`
- `locations`
- `professional_profiles`
- `bank_accounts`
- `network_data`
- `processing_audit`

El diseño final se aprobará en la tarea Jira de modelo relacional después de validar el contrato de eventos reales.

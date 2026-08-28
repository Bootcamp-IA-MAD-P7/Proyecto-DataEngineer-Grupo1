# Modelo de datos

## MongoDB: zona raw

Colecciones previstas:

- `raw_events`: evento original, metadatos Kafka, fecha de recepción y estado de proceso.
- `invalid_events`: evento que no supera la validación, junto al motivo.
- `processing_audit`: trazabilidad de transformación y carga.

Índice técnico previsto para evitar duplicados: `topic + partition + offset`.

Sobre mínimo propuesto del documento raw:

| Campo | Tipo | Propósito |
|---|---|---|
| `payload` | objeto JSON | Evidencia original, sin renombrar ni normalizar |
| `topic` | string | Metadato técnico de Kafka |
| `partition` | integer | Metadato técnico de Kafka |
| `offset` | integer | Metadato técnico de Kafka |
| `received_at` | datetime UTC | Momento de recepción en la plataforma |
| `processing_status` | string técnico | Estado operativo, no clasificación de negocio |

ADR-0005 propone que el índice compuesto sea único y que la confirmación del offset
solo ocurra tras una inserción correcta o cuando MongoDB demuestre que las mismas
coordenadas ya existen. HRP-34 debe validar este diseño con pruebas antes de que la
propuesta pueda aceptarse; HRP-35 y HRP-36 deberán respetar la decisión finalmente
aprobada. Véase
[ADR-0005](adr/0005-kafka-acknowledgement-after-raw-persistence.md).

## PostgreSQL: zona curada

Tablas previstas:

- `employees`
- `locations`
- `professional_profiles`
- `bank_accounts`
- `network_data`
- `processing_audit`

El diseño final se aprobará en la tarea Jira de modelo relacional después de validar el contrato de eventos reales.

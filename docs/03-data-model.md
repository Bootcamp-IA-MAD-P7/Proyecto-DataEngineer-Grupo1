# Modelo de datos

## MongoDB: zona raw

Colecciones previstas:

- `raw_events`: evento original, metadatos Kafka, fecha de recepción y estado de proceso.
- `invalid_events`: evento que no supera la validación, junto al motivo.
- `processing_audit`: trazabilidad de transformación y carga.

Índice técnico previsto para evitar duplicados: `topic + partition + offset`.

Sobre mínimo del documento raw:

| Campo | Tipo | Propósito |
|---|---|---|
| `payload` | objeto JSON | Evidencia original, sin renombrar ni normalizar |
| `topic` | string | Metadato técnico de Kafka |
| `partition` | integer | Metadato técnico de Kafka |
| `offset` | integer | Metadato técnico de Kafka |
| `received_at` | datetime UTC | Momento de recepción en la plataforma |
| `processing_status` | string técnico | Estado operativo, no clasificación de negocio |

El índice compuesto debe ser único. La confirmación del offset solo ocurre tras una
inserción correcta o cuando MongoDB demuestra que las mismas coordenadas ya existen.
HRP-34, HRP-35 y HRP-36 implementarán este contrato conforme a
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

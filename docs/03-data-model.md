# Modelo de datos

El diseño detallado (colecciones, tablas, columnas propuestas y límites raw/curado)
vive en [docs/specs/HRP-25-modelo-datos.md](specs/HRP-25-modelo-datos.md). Este
documento resume ese diseño; ante cualquier discrepancia, la spec HRP-25 es la
fuente de verdad hasta que se apruebe una tarea de implementación.

## MongoDB: zona raw

Colecciones previstas:

- `raw_events`: evento original, metadatos Kafka, fecha de recepción y estado de proceso.
- `invalid_events`: evento que no supera la validación técnica (no la clasificación
  estructural `non-conforming/unknown`), junto al motivo.
- `processing_audit`: trazabilidad de transformación y carga, del lado raw.

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

La clasificación estructural (A–E o `non-conforming/unknown`, según
`docs/02-data-contract.md`) no se persiste como campo de `raw_events` en este
diseño: es un resultado de proceso, no un hecho raw. Dónde auditar esa
clasificación queda pendiente (ver HRP-25).

ADR-0005 propone que el índice compuesto sea único y que la confirmación del offset
solo ocurra tras una inserción correcta o cuando MongoDB demuestre que las mismas
coordenadas ya existen. HRP-34 debe validar este diseño con pruebas antes de que la
propuesta pueda aceptarse; HRP-35 y HRP-36 deberán respetar la decisión finalmente
aprobada. Véase
[ADR-0005](adr/0005-kafka-acknowledgement-after-raw-persistence.md).

## PostgreSQL: zona curada

Tablas previstas, con columnas candidatas detalladas en
[docs/specs/HRP-25-modelo-datos.md](specs/HRP-25-modelo-datos.md):

- `employees`
- `locations`
- `professional_profiles`
- `bank_accounts`
- `network_data`
- `processing_audit`

Ninguna tabla incluye todavía una restricción única de negocio (p. ej. sobre
`passport`): `passport`, `fullname` y `address` son candidatos de correlación
observados por HRP-29, no una clave aprobada. La clave de correlación de persona,
la cardinalidad entre `employees` y las tablas dependientes, y la política de
upsert idempotente quedan pendientes de
[ADR-0006](adr/0006-person-correlation-key.md), que permanece `Proposed` hasta
disponer de evidencia adicional revisada por una persona.

El diseño final se aprobará en la tarea Jira de modelo relacional después de validar
el contrato de eventos reales. Esta spec (HRP-25) no autoriza SQL, migraciones,
Docker, ETL ni código de API: esas tareas son responsabilidad de futuros tickets
Jira (persistencia raw, conexión ETL → PostgreSQL, creación de tablas) una vez el
diseño reciba revisión humana.

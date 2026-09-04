# Observabilidad

HRP-34 prohíbe registrar payloads, BSON Binary, PII, secretos u operaciones MongoDB.
Los conflictos registran solo coordenadas y tipo técnico y no autorizan acknowledgement.
La evidencia de sostenibilidad se limita a batching acotado, idempotencia y evitar
redelivery no acotado, sin afirmaciones de energía o carbono.

## Logs

Los logs serán estructurados y contendrán, cuando estén disponibles: `topic`,
`partition`, `offset`, `status`, `error_type` y `processing_time_ms`.

Nunca incluirán payloads, IBAN, pasaportes, emails, teléfonos, direcciones ni valores
de correlación. Un filtro común de redacción actuará como defensa adicional, pero no
autoriza a registrar PII. Los servicios emitirán JSON por `stdout` para que Docker y
la futura capa de monitorización puedan recogerlo sin acoplamiento.

HRP-66 añade un helper reutilizable para logs técnicos de ETL. Este helper solo acepta
metadatos acotados de procesamiento: etapa, estado, dominio, contadores, tipo de error
y duración. No acepta payloads, claves de correlación, secretos ni valores personales.

## Métricas

- Eventos consumidos por segundo.
- Eventos persistidos en MongoDB.
- Eventos inválidos.
- Latencia de transformación.
- Latencia de persistencia SQL.
- Eventos pendientes o incompletos en Redis.
- Confirmaciones de offsets Kafka.
- Fallos de persistencia raw que dejan offsets sin confirmar.
- Reentregas descartadas por el índice único de MongoDB.

Prometheus y un dashboard básico se implementarán en el Sprint 5.

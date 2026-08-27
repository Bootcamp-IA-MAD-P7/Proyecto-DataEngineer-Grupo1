# Observabilidad

## Logs

Los logs serán estructurados y contendrán, cuando estén disponibles: `event_id`, `person_key`, `topic`, `partition`, `offset`, `status`, `error_type` y `processing_time_ms`.

## Métricas

- Eventos consumidos por segundo.
- Eventos persistidos en MongoDB.
- Eventos inválidos.
- Latencia de transformación.
- Latencia de persistencia SQL.
- Eventos pendientes o incompletos en Redis.

Prometheus y un dashboard básico se implementarán en el Sprint 5.


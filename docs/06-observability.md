# Observabilidad implementada

**Corte:** 2026-09-08. Fuentes:
[metrics.py](../src/hr_pro_platform/observability/metrics.py),
[consumer](../src/hr_pro_platform/ingestion/consumer.py),
[MongoDB](../src/hr_pro_platform/ingestion/mongo.py).

## Catálogo exacto

| Familia | Tipo / unidad | Límite de medición |
|---|---|---|
| hr_pro_platform_ingestion_messages_consumed_total | Counter / mensajes | Fetch exitoso; incluye payload técnicamente inválido, excluye errores Kafka |
| hr_pro_platform_ingestion_processing_duration_seconds | Histogram / segundos | Procesamiento de ingesta, separado de persistencia |
| hr_pro_platform_ingestion_persistence_duration_seconds | Histogram / segundos | Intentos de persistencia MongoDB instrumentados |

Los histogramas exponen sum, count y solo el bucket +Inf. Permiten medias,
pero no percentiles p95/p99 útiles. El endpoint usa un registro propio, sin
etiquetas de persona, payload, topic de alta cardinalidad ni métricas SQL.
No hay gauge de pendientes Redis, contador de errores separado o lag Kafka en
este catálogo. Las listas más amplias de versiones anteriores eran aspiracionales.

## PromQL para la demo

Tasa de mensajes:

```promql
rate(hr_pro_platform_ingestion_messages_consumed_total[5m])
```

Duración media de procesamiento:

```promql
rate(hr_pro_platform_ingestion_processing_duration_seconds_sum[5m])
/
rate(hr_pro_platform_ingestion_processing_duration_seconds_count[5m])
```

Para persistencia, sustituir processing por persistence en ambos nombres.
Un denominador cero puede dar NaN; ausencia de tráfico no prueba latencia cero.
El Counter se reinicia con el proceso; la tasa de Prometheus contempla resets.

## Exposición y dashboard

Prometheus usa app:9464/metrics dentro de Compose. El puerto 9464 no está publicado
en el host por el servicio app. Prometheus está en localhost:9090 y Grafana en
localhost:3000. Dashboard: HR Pro Ingestion Overview. Puede estar disponible aunque
el target esté DOWN. [Arranque](07-runbook.md).

## Logs reales

El logger compartido emite texto con fecha, nivel, nombre y mensaje por stdout,
a nivel INFO. No usa LOG_LEVEL. El helper ETL serializa un evento JSON controlado
como mensaje dentro de ese logger: la línea completa no es necesariamente JSON puro.
No existe un filtro global de redacción implementado que permita registrar PII.
La seguridad depende de evitar valores sensibles en las llamadas de logging.
El consumer conserva interpolación de texto de excepciones en sus manejadores
Kafka/genérico (`Unexpected error: {e}`); no hay garantía universal de que un mensaje
de excepción externo no incluya datos sensibles. Es un riesgo funcional identificado,
no corregido en esta revisión. Revisar cualquier log antes de compartirlo.

El alcance documentado de HRP-67 limita detalles de errores de base de datos;
no constituye una auditoría de todas las excepciones futuras.
Payloads, secretos y claves de correlación no se incluyen en la demo.

## Sostenibilidad y límites

TTL, estado efímero y metadatos acotados son decisiones de diseño.
No hay medición energética, huella de carbono ni garantía de throughput.
[Fundamento oficial sobre histogramas](https://prometheus.io/docs/practices/histograms/).

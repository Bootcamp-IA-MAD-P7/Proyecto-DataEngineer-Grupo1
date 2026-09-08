# Arquitectura — fuente para exposición

## Tres responsabilidades de datos

- MongoDB: conserva el objeto raw y sus coordenadas Kafka.
- Redis: adapter de estado parcial efímero con Sets y TTL, no fuente de verdad.
- PostgreSQL: tablas curadas para repositorios y API.

## Recorrido implementado

Kafka externo → proceso app de ingesta → MongoDB. El mismo proceso emite contador
de mensajes y tiempos de procesamiento/persistencia MongoDB a Prometheus y Grafana.
El servicio `etl` toma continuamente los RAW pendientes, clasifica los cinco
dominios, usa Redis como estado temporal de correlación y actualiza PostgreSQL.
El servicio `api` consulta el resultado curado. HRP-71 conserva su alcance de
prueba sintética, mientras la extensión de HRP-87 aporta la orquestación real.

## Correlación defendible

Clasificar por conjunto exacto de claves; validar técnicamente; agrupar; consolidar
con las cuatro relaciones de ADR-0006. Mantener complete/incomplete/ambiguous,
entradas no resueltas y procedencia. No normalizar ni fusionar silenciosamente
datos conflictivos. Las coincidencias son operacionales, no identidad probada.

## Visual recomendado

Una banda continua Kafka → app → MongoDB → etl ↔ Redis → PostgreSQL → API,
con Prometheus/Grafana observando la ingesta. Rotular HRP-71 como prueba sintética
histórica y no dibujar un frontend entregado.

[Arquitectura canónica](../01-architecture.md), [modelo](../03-data-model.md),
[API](../api-reference.md), [observabilidad](../06-observability.md).

Límite de durabilidad: el prefijo de acknowledgement se evalúa por lote; sin control
de huecos entre lotes no se acredita ausencia global de pérdida. Evitar esa promesa.

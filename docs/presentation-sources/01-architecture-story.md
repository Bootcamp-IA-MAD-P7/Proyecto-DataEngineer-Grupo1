# Arquitectura — fuente para exposición

## Tres responsabilidades de datos

- MongoDB: conserva el objeto raw y sus coordenadas Kafka.
- Redis: adapter de estado parcial efímero con Sets y TTL, no fuente de verdad.
- PostgreSQL: tablas curadas para repositorios y API.

## Recorrido implementado

Kafka externo → proceso app de ingesta → MongoDB. El mismo proceso emite contador
de mensajes y tiempos de procesamiento/persistencia MongoDB a Prometheus y Grafana.
Transformación y repositorio SQL son componentes; HRP-71 los une explícitamente
con MongoDB usando eventos sintéticos equivalentes a Kafka.
Redis no participa en esa prueba. No hay un worker productivo que conecte
continuamente MongoDB → ETL → SQL. La API se inicia separadamente.

## Correlación defendible

Clasificar por conjunto exacto de claves; validar técnicamente; agrupar; consolidar
con las cuatro relaciones de ADR-0006. Mantener complete/incomplete/ambiguous,
entradas no resueltas y procedencia. No normalizar ni fusionar silenciosamente
datos conflictivos. Las coincidencias son operacionales, no identidad probada.

## Visual recomendado

Dos bandas: arriba runtime continuo Kafka → app → MongoDB y monitorización;
abajo componentes de transformación/Redis/SQL/API. La conexión de prueba debe ir
discontinua y rotulada «HRP-71 sintético». No dibujar un frontend entregado.

[Arquitectura canónica](../01-architecture.md), [modelo](../03-data-model.md),
[API](../api-reference.md), [observabilidad](../06-observability.md).

Límite de durabilidad: el prefijo de acknowledgement se evalúa por lote; sin control
de huecos entre lotes no se acredita ausencia global de pérdida. Evitar esa promesa.

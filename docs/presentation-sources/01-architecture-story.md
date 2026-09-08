# Arquitectura — fuente narrativa

**Lectura del diagrama:** representa el baseline entregado al cierre de 2026-09-08.
Los componentes están versionados y documentados; la ejecución prolongada con servicios
reales depende del entorno de validación disponible.

## Idea principal

La arquitectura separa datos originales, estado temporal y datos listos para consulta.
Esta separación permite escalar, auditar y reprocesar sin mezclar responsabilidades.

```text
Kafka externo
   -> ingest-worker
      -> MongoDB: eventos raw, inmutables y trazables
      -> process-worker + Redis: correlación temporal de fragmentos
         -> PostgreSQL: información curada e idempotente
            -> FastAPI -> frontend accesible

Todos los componentes emiten logs y métricas para Prometheus.
```

## Por qué cada tecnología

| Tecnología | Papel | Beneficio |
|---|---|---|
| Kafka | Entrada continua | Procesa eventos en tiempo real |
| MongoDB | Zona raw | Auditoría, reproceso y protección contra duplicados técnicos |
| Redis | Estado temporal | Agrupa datos que llegan en distinto orden |
| PostgreSQL | Zona curada | Consultas consistentes y eficientes |
| Docker Compose | Entorno reproducible | Misma ejecución para desarrollo y demo |
| Prometheus | Observabilidad | Mide volumen, latencia y errores |
| FastAPI + frontend accesible | Consulta y demo | Hace visible el valor final sin acoplar la UI al almacenamiento |

## Invariantes del baseline

- El evento raw se persiste antes de transformarse.
- ADR-0005 guía la confirmación Kafka después de persistencia raw o reconocimiento de
  duplicado técnico.
- Reprocesar el mismo evento no duplica información.
- Un mensaje erróneo no detiene la ingesta.
- Redis no es fuente de verdad y sus datos expiran.
- El contrato se basa en mensajes observados, no en el código del productor.

La documentación técnica completa está en `docs/01-architecture.md`. El frontend no
forma parte de la capacidad entregada en este cierre.

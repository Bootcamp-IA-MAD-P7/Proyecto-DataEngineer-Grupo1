# Arquitectura — fuente narrativa

**Lectura del diagrama:** representa la arquitectura objetivo. A 2026-08-31 están
validados Kafka, el consumer, MongoDB local y una persistencia inicial de fragmentos.
El sobre raw definitivo aún debe revisarse antes de usarlo como contrato del ETL.

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

## Invariantes objetivo y propuestas pendientes

- El evento raw se persiste antes de transformarse.
- ADR-0005 guía la confirmación Kafka después de persistencia raw o reconocimiento de
  duplicado técnico; su aplicación debe quedar alineada con el sobre raw final.
- Reprocesar el mismo evento no duplica información.
- Un mensaje erróneo no detiene la ingesta.
- Redis no es fuente de verdad y sus datos expiran.
- El contrato se basa en mensajes observados, no en el código del productor.

La documentación técnica completa está en `docs/01-architecture.md`.

# Arquitectura — fuente narrativa

**Lectura del diagrama:** representa la arquitectura objetivo. A 2026-08-28 están
validados Kafka y el consumer; MongoDB local existe, pero su persistencia raw aún no
está integrada con el consumer.

## Idea principal

La arquitectura separa datos originales, estado temporal y datos listos para consulta.
Esta separación permite escalar, auditar y reprocesar sin mezclar responsabilidades.

```text
Kafka externo
   -> ingest-worker
      -> MongoDB: eventos raw, inmutables y trazables
      -> process-worker + Redis: correlación temporal de fragmentos
         -> PostgreSQL: información curada e idempotente
            -> FastAPI -> Streamlit

Todos los componentes emiten logs y métricas para Prometheus.
```

## Por qué cada tecnología

| Tecnología | Papel | Beneficio |
|---|---|---|
| Kafka | Entrada continua | Procesa eventos en tiempo real |
| MongoDB | Zona raw | Auditoría y reproceso sin perder el original |
| Redis | Estado temporal | Agrupa datos que llegan en distinto orden |
| PostgreSQL | Zona curada | Consultas consistentes y eficientes |
| Docker Compose | Entorno reproducible | Misma ejecución para desarrollo y demo |
| Prometheus | Observabilidad | Mide volumen, latencia y errores |
| FastAPI + Streamlit | Consulta y demo | Hace visible el valor final |

## Invariantes que se demuestran

- El evento raw se persiste antes de transformarse.
- Kafka se confirma después de insertar raw o reconocer un duplicado técnico.
- Reprocesar el mismo evento no duplica información.
- Un mensaje erróneo no detiene la ingesta.
- Redis no es fuente de verdad y sus datos expiran.
- El contrato se basa en mensajes observados, no en el código del productor.

La documentación técnica completa está en `docs/01-architecture.md`.

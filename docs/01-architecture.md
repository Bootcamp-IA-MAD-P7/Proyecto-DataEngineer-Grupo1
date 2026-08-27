# Arquitectura

## Diseño objetivo

```text
Kafka (externo)
       |
       v
Ingest worker -----> MongoDB / raw_events
       |                    |
       |                    v
       +---------------> auditoría y reproceso
       |
       v
Process worker <----> Redis / estado temporal
       |
       v
PostgreSQL / datos integrados
       |
       v
FastAPI -----> Streamlit

Todos los servicios -> logs estructurados + métricas Prometheus
```

## Decisiones de diseño

- Un repositorio y un monolito modular, con procesos separados (`ingest`, `process`, `api`) cuando haya código.
- El servidor Kafka educativo es una dependencia externa configurable con variables de entorno.
- MongoDB recibe los eventos sin modificar y con metadatos técnicos.
- PostgreSQL contiene datos curados e idempotentes para consultas.
- Redis no es fuente de verdad; solo almacena información parcial mientras se agrupa una persona.

## Límites del sistema

No se crea ni mantiene el productor Kafka. El equipo solo consume los mensajes publicados y no inspecciona el código generador.


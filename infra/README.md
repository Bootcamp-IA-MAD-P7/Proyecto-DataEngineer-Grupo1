# Infraestructura local

El Compose canónico es [compose.dev.yml](compose.dev.yml).
[Runbook](../docs/07-runbook.md) · [Configuración](../docs/configuration.md).

| Servicio | Imagen / build | Puerto del host | Persistencia |
|---|---|---|---|
| app | Dockerfile Python 3.11-slim; usuario no root | Ninguno; métricas internas 9464 | Escribe en MongoDB |
| etl | Misma imagen; worker de transformación | Ninguno | MongoDB → Redis → PostgreSQL |
| api | Misma imagen; FastAPI | 127.0.0.1:8000 | Solo lectura de PostgreSQL |
| mongo | mongo:7.0 | 127.0.0.1:27017 | mongo_data |
| postgres | postgres:16 | 127.0.0.1:5432 | postgres_data |
| redis | redis:7.2 | Ninguno | tmpfs; estado efímero |
| prometheus | prom/prometheus:v2.55.1 | 127.0.0.1:9090 | Sin volumen persistente declarado |
| grafana | grafana/grafana-oss:11.3.0 | 127.0.0.1:3000 | Configuración provisionada desde archivos |

Todos declaran restart: unless-stopped. MongoDB, PostgreSQL y Redis tienen
healthcheck; `app`, `etl` y `api` esperan sus dependencias saludables.
Kafka permanece externo. Las imágenes tienen tags, no digests inmutables.

## Arranque

```bash
docker compose -f infra/compose.dev.yml up -d mongo postgres redis prometheus grafana
docker compose -f infra/compose.dev.yml --profile app up -d --build app etl api
docker compose -f infra/compose.dev.yml --profile app ps
```

Preparar antes .env con el broker autorizado y credenciales locales.
No copiar configuración expandida a una PR. Usar config --quiet para comprobar sintaxis.

## Límites

Redis conserva temporalmente fragmentos clasificados bajo identificadores opacos y
con TTL; el worker ETL los recupera antes de consolidar. Prometheus observa
app:9464/metrics.
Grafana permite lectura anónima local; no está configurado para exposición pública.
Un restart no demuestra progreso del pipeline ni disponibilidad 24/7.

Parar con stop para conservar volúmenes. No usar down -v como limpieza rutinaria.

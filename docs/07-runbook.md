# Runbook operativo

**Corte:** 2026-09-08. Ejecutar desde la raíz del repositorio HR Pro.
[Configuración por variable y red](configuration.md).

## 1. Preparar

Crear venv, instalar `.[dev]` y copiar .env.example solo si .env no existe, siguiendo
el [README](../README.md#inicio-rápido). Completar configuración autorizada localmente.
No leer el generador educativo ni cambiar su entorno desde estos procedimientos.

## 2. Datos y esquema

```bash
docker compose -f infra/compose.dev.yml config --quiet
docker compose -f infra/compose.dev.yml up -d mongo postgres redis
docker compose -f infra/compose.dev.yml ps
python -m hr_pro_platform.storage.main
```

El inicializador crea tablas e índices en la base configurada y termina.
No es un migrador de versiones ni un worker ETL. Un healthcheck de PostgreSQL
no prueba existencia de tablas o registros. Las contraseñas de un volumen PostgreSQL
existente no cambian por editar el archivo de entorno.

## 3. Ingesta continua

Configurar Kafka para ser accesible desde Docker. El Compose incluye env_file de
ejemplo y .env opcional; las variables explícitas de app fijan MongoDB interno.

```bash
docker compose -f infra/compose.dev.yml --profile app up -d --build app prometheus grafana
docker compose -f infra/compose.dev.yml --profile app ps
```

Este comando mantiene Kafka → MongoDB, no ejecuta continuamente MongoDB → SQL.
HRP-87 no añadió ese worker. `restart: unless-stopped` es una política de reinicio
del contenedor, no una garantía de salud, progreso, reconciliación o ausencia de pérdida.

## 4. Consultas

```bash
python -m uvicorn hr_pro_platform.api.main:app --host 127.0.0.1 --port 8000
```

Abrir /docs y /health. /statistics consulta agregados de tablas existentes.
Una API saludable puede devolver cero registros. Consultar únicamente datos sintéticos
en presentaciones. [Contrato de endpoints](api-reference.md).

## 5. Observabilidad

- [Prometheus targets](http://localhost:9090/targets): hr-pro-ingestion.
- [Grafana](http://localhost:3000): HR Pro Ingestion Overview.
- [Métricas y PromQL](06-observability.md).

Prometheus scrapea app:9464, no localhost:9464. Grafana tiene lectura anónima local.
Redis no publica 6379 al host; confirmar disponibilidad dentro de su contenedor:

```bash
docker compose -f infra/compose.dev.yml exec -T redis redis-cli ping
```

## 6. Comprobación de integración

HRP-71 usa MongoDB/PostgreSQL reales y eventos sintéticos, sin broker ni Redis.
Solo ejecutar pruebas de integración sobre bases desechables preparadas: sus fixtures
escriben y eliminan datos. En particular, HRP-71 limpia colecciones en
hrp71_synthetic; nunca usar esa base para información que deba conservarse.

```bash
python -m pytest tests/e2e/test_kafka_mongodb_postgresql_flow.py -q --no-cov
```

El resultado debe indicar pass, fail o skip. Un skip no demuestra la integración.
No se ejecutaron estas pruebas de datos en la revisión exclusivamente documental.

## 7. Diagnóstico

| Síntoma | Comprobar |
|---|---|
| app termina o se reinicia | Kafka autorizado accesible desde Docker; variables no vacías |
| DLL cimpl bloqueada en Windows | Import aislado de confluent_kafka; política de Control de aplicaciones |
| AttributeError al parchear consumer en tests | El ImportError original puede estar oculto por unittest.mock |
| API 503 | PostgreSQL configurado, conexión y esquema; no publicar detalles de excepción |
| API vacía | Datos curados no cargados; el arranque de app solo guarda raw |
| Target Prometheus DOWN | app activo y endpoint interno 9464; comprobar reinicios |
| Grafana sin series | Target UP, tráfico y ventana de consulta suficiente |
| Redis inaccesible desde host | No publica puerto; usar cliente en red Compose o endpoint de test explícito |
| Tablas con definición antigua | CREATE IF NOT EXISTS no migra columnas; requiere un cambio de esquema diseñado |

La incidencia Windows observada en esta conversación bloqueó la extensión nativa.
No modificar políticas de seguridad para ocultar el fallo. Un entorno Linux autorizado
puede permitir otra validación, pero no se presupone que haya pasado.

## 8. Parada y conservación

```bash
docker compose -f infra/compose.dev.yml stop app
```

O detener todos los servicios HR Pro:

```bash
docker compose -f infra/compose.dev.yml stop
```

No ejecutar down -v para una parada normal. Los volúmenes MongoDB/PostgreSQL
conservan datos; Redis es efímero. No hay procedimiento de backup/restore probado
en esta entrega; no afirmar recuperación ante desastres.

## 9. Guion de demo controlada

1. Explicar el problema y el límite del productor externo.
2. Mostrar servicios y métricas sin abrir payloads ni .env.
3. Explicar durabilidad raw y correlación con ejemplos sintéticos.
4. Mostrar evidencia de HRP-71 indicando “Kafka equivalente, sintético”.
5. Consultar API/estadísticas sobre una base de demo preparada.
6. Mostrar aceptación de cierre, límite del frontend y siguientes pasos.

Fuentes y guion de exposición: [NotebookLM](presentation-sources/README.md).

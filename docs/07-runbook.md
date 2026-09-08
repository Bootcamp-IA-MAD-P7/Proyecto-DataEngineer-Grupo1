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

## 3. Pipeline continuo

Configurar Kafka para ser accesible desde Docker. El Compose incluye env_file de
ejemplo y .env opcional; las variables explícitas de app fijan MongoDB interno.

```bash
docker compose -f infra/compose.dev.yml --profile app up -d --build app etl api prometheus grafana
docker compose -f infra/compose.dev.yml --profile app ps
```

`app` mantiene Kafka → MongoDB. `etl` toma RAW `pending` en lotes acotados,
clasifica, valida, mantiene correlación temporal en Redis y persiste componentes
curados en PostgreSQL. `api` consulta PostgreSQL en `127.0.0.1:8000`.
`restart: unless-stopped` es una política de reinicio, no una garantía de ausencia
de pérdida ni una afirmación de identidad real.

## 4. Consultas

Abrir /docs, /health y /statistics. La API arranca con el perfil `app` y consulta
las tablas que el worker ETL actualiza. Consultar únicamente datos sintéticos en
presentaciones. [Contrato de endpoints](api-reference.md).

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/statistics
```

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
| API vacía | `etl` activo, RAW pending, Redis accesible y credenciales PostgreSQL |
| Target Prometheus DOWN | app activo y endpoint interno 9464; comprobar reinicios |
| Grafana sin series | Target UP, tráfico y ventana de consulta suficiente |
| Redis inaccesible desde host | No publica puerto; usar cliente en red Compose o endpoint de test explícito |
| Tablas con definición antigua | CREATE IF NOT EXISTS no migra columnas; requiere un cambio de esquema diseñado |

La incidencia Windows observada en esta conversación bloqueó la extensión nativa.
No modificar políticas de seguridad para ocultar el fallo. Un entorno Linux autorizado
puede permitir otra validación, pero no se presupone que haya pasado.

## 8. Parada y conservación

```bash
docker compose -f infra/compose.dev.yml --profile app stop app etl api
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
2. Mostrar cinco mensajes sintéticos directamente desde Kafka:

```bash
docker exec kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic probando --max-messages 5 --timeout-ms 15000 --property print.partition=true --property print.offset=true
```

3. Mostrar RAW persistido en MongoDB con procedencia:

```bash
docker compose -f infra/compose.dev.yml exec -T mongo mongosh --quiet --eval 'db.getSiblingDB("hr_pro").raw_events.find({}, {_id:0, topic:1, partition:1, offset:1, received_at:1, payload:1}).sort({received_at:-1}).limit(5).toArray()'
```

4. Demostrar que el worker procesa lotes y que Redis mantiene estado temporal:

```bash
docker compose -f infra/compose.dev.yml logs --tail=100 etl
docker compose -f infra/compose.dev.yml exec -T redis redis-cli DBSIZE
```

5. Consultar las seis tablas PostgreSQL:

```bash
docker compose -f infra/compose.dev.yml exec -T postgres psql -U hr_pro -d hr_pro -c "SELECT 'employees' AS tabla, COUNT(*) AS registros FROM employees UNION ALL SELECT 'locations', COUNT(*) FROM locations UNION ALL SELECT 'professional_profiles', COUNT(*) FROM professional_profiles UNION ALL SELECT 'bank_accounts', COUNT(*) FROM bank_accounts UNION ALL SELECT 'network_data', COUNT(*) FROM network_data UNION ALL SELECT 'processing_audit', COUNT(*) FROM processing_audit;"
```

6. Mostrar un cliente que tenga los cinco dominios correlacionados:

```bash
docker compose -f infra/compose.dev.yml exec -T postgres psql -U hr_pro -d hr_pro -c "SELECT e.id, e.first_name, e.last_name, e.passport, l.city, l.address, p.company, p.job, b.iban, b.salary, n.ip_v4 FROM employees e JOIN locations l ON l.employee_id=e.id JOIN professional_profiles p ON p.employee_id=e.id JOIN bank_accounts b ON b.employee_id=e.id JOIN network_data n ON n.employee_id=e.id ORDER BY e.id DESC LIMIT 1;"
```

7. Consultar `/health`, `/statistics` y sustituir `ID` por el mostrado antes:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/statistics
curl "http://127.0.0.1:8000/people/search?id=ID"
```

8. Mostrar consumo, velocidad y latencias en Prometheus/Grafana. La consulta de
velocidad es `rate(hr_pro_platform_ingestion_messages_consumed_total[1m])`.
9. Cerrar con límites: datos sintéticos, correlación operacional, backlog,
sin benchmark/HA y frontend excluido.

Fuentes y guion de exposición: [NotebookLM](presentation-sources/README.md).

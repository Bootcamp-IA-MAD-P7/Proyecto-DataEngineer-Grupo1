# Runbook operativo

## Inicio de un desarrollo

1. Actualizar `develop`.
2. Revisar la tarea Jira y su spec.
3. Crear rama asociada.
4. Ejecutar las comprobaciones locales antes de abrir PR.

## Configuración local segura

1. Crear el archivo local a partir de la plantilla:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Completar únicamente los valores autorizados para el entorno actual. Nunca
   registrar el contenido de `.env` en Git, logs, chats, Jira, pull requests o
   fuentes de presentación.
3. Para el consumer actual, configurar `KAFKA_BOOTSTRAP_SERVERS`,
   `KAFKA_CONSUMER_GROUP` y `KAFKA_TOPICS`. Las variables definidas por el proceso
   tienen prioridad sobre las de `.env`.
4. `MONGODB_URI`, las variables `POSTGRES_*`, `REDIS_URL` y `LOG_LEVEL` están
   documentadas en `.env.example` para los componentes futuros. No implican que esos
   consumidores de configuración estén implementados todavía.
5. Consultar el catálogo y las reglas de cada variable en la sección
   [Configurar el consumer](../README.md#4-configurar-el-consumer) del README.

## Entorno Kafka educativo autorizado

Este entorno es externo al repositorio del equipo. Se obtiene únicamente para ejecutar
el Docker Compose documentado; el código del generador nunca se abre, inspecciona,
busca, analiza ni se emplea como fuente de contrato.

1. Crear una carpeta independiente del repositorio del equipo.
2. Obtener el repositorio educativo y, desde su raíz, ejecutar:

   ```powershell
   docker compose up --build -d
   docker compose ps
   ```

3. Usar el puerto publicado por el servicio Kafka en `docker compose ps` para
   configurar localmente `KAFKA_BOOTSTRAP_SERVERS` en `.env`.
4. Mantener `.env` fuera de Git y no copiar credenciales al chat, Jira o una PR.
5. Para HRP-29, realizar una observación limitada en memoria y registrar solo
   estructura, tipos aparentes y metadatos agregados. No guardar valores ni capturas
   completas de mensajes.
6. Para detener el entorno al finalizar la sesión:

   ```powershell
   docker compose down
   ```

No consultar logs del generador como mecanismo de descubrimiento. La evidencia válida
se registra en `docs/observations/` mediante una tarea HRP-29 revisable.

## Incidencia de datos

1. Localizar el evento con sus metadatos Kafka en `raw_events`.
2. Consultar `processing_audit`.
3. Determinar si el error es de contrato, clasificación, agrupación o almacenamiento.
4. Añadir fixture de regresión antes de corregir la lógica.
5. Registrar la decisión en una ADR si cambia la estrategia de datos.

## Incidencia de infraestructura

1. Consultar logs del servicio.
2. Comprobar conectividad a Kafka y estado de contenedores.
3. No eliminar volúmenes ni datos sin acuerdo explícito del equipo.

## Validación de la base local

Desde la raíz del repositorio del equipo:

```powershell
pre-commit run --all-files
ruff check .
ruff format --check .
mypy src
pytest
docker compose -f infra/compose.dev.yml config --quiet
docker build --tag hr-pro-platform:local .
docker compose -f infra/compose.dev.yml up -d mongo postgres
docker compose -f infra/compose.dev.yml ps
docker compose -f infra/compose.dev.yml exec -T mongo `
  mongosh --quiet --eval "db.adminCommand('ping').ok"
docker compose -f infra/compose.dev.yml exec -T postgres `
  pg_isready -U hr_pro -d hr_pro
```

El umbral inicial de cobertura es 75 %. Un contenedor saludable, un `ping` correcto
de MongoDB y un `pg_isready` correcto de PostgreSQL solo demuestran disponibilidad
de esos servicios; todavía no prueban la persistencia raw, la política de
confirmación de offsets ni ninguna tabla, esquema o dato curado en PostgreSQL (eso
corresponde a HRP-54).

La imagen de aplicación solo demuestra que el consumer puede empaquetarse sin incluir
el entorno local. No reemplaza el Compose final ni demuestra conectividad a Kafka.

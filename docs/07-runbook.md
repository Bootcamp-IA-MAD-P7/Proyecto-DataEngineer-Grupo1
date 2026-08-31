# Runbook operativo

## Inicio de un desarrollo

1. Actualizar `develop`.
2. Revisar la tarea Jira y su spec.
3. Crear rama asociada.
4. Ejecutar las comprobaciones locales antes de abrir PR.

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
docker compose -f infra/compose.dev.yml up -d mongo
docker compose -f infra/compose.dev.yml ps
docker compose -f infra/compose.dev.yml exec -T mongo `
  mongosh --quiet --eval "db.adminCommand('ping').ok"
```

El umbral inicial de cobertura es 75 %. Un contenedor saludable y un `ping` correcto
solo demuestran disponibilidad de MongoDB; todavía no prueban la persistencia raw ni
la política de confirmación de offsets.

La imagen de aplicación solo demuestra que el consumer puede empaquetarse sin incluir
el entorno local. No reemplaza el Compose final ni demuestra conectividad a Kafka.

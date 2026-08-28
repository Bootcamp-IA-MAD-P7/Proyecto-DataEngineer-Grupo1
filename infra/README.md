# Infraestructura local

Kafka es una dependencia externa suministrada por el proyecto educativo: no se
incluye su servidor ni el generador en este repositorio. La aplicacion recibira
su conexion mediante variables de entorno.

## MongoDB para desarrollo

Este Compose es un habilitador local de HRP-33 para que Anahi pueda desarrollar
la persistencia de eventos originales. No es todavia el Compose final de la
plataforma: PostgreSQL, Redis, Prometheus y la aplicacion se incorporaran en sus
tareas y specs correspondientes.

### Requisitos

- Docker Desktop iniciado.
- Docker Compose v2 (`docker compose version`).

### Uso

Desde la raiz del repositorio:

```powershell
Copy-Item .env.example .env
docker compose -f infra/compose.dev.yml up -d mongo
docker compose -f infra/compose.dev.yml ps
```

MongoDB queda disponible solo en `localhost:27017`. La URI de desarrollo es
`mongodb://localhost:27017/hr_pro` y esta reflejada en `.env.example`.

Para detenerlo y conservar el volumen:

```powershell
docker compose -f infra/compose.dev.yml down
```

Para eliminar tambien los datos locales (solo si son prescindibles):

```powershell
docker compose -f infra/compose.dev.yml down -v
```

No se deben subir `.env`, volcados, eventos capturados ni volumenes Docker al
repositorio.

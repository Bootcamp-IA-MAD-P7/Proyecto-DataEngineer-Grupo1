# Infraestructura local

Kafka es una dependencia externa suministrada por el proyecto educativo: no se
incluye su servidor ni el generador en este repositorio. La aplicacion recibira
su conexion mediante variables de entorno.

## MongoDB para desarrollo

Este Compose es un habilitador local de HRP-33 para que Anahi pueda desarrollar
la persistencia de eventos originales. No es todavia el Compose final de la
plataforma: Redis, Prometheus y la aplicacion se incorporaran en sus tareas y
specs correspondientes.

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

## PostgreSQL para desarrollo

Este Compose es un habilitador local de HRP-53: deja el motor PostgreSQL
disponible y vacio para que HRP-54 pueda crear las tablas y claves diseñadas en
HRP-52, y para que HRP-63 pueda integrar el Compose final junto con la
aplicacion y MongoDB. No crea ninguna tabla, esquema ni dato de negocio.

### Requisitos

- Docker Desktop iniciado.
- Docker Compose v2 (`docker compose version`).
- Archivo `.env` local (ver "Uso" abajo); el servicio no arranca de forma
  utilizable sin `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`.

### Uso

Desde la raiz del repositorio:

```powershell
Copy-Item .env.example .env
docker compose -f infra/compose.dev.yml up -d postgres
docker compose -f infra/compose.dev.yml ps
```

PostgreSQL queda disponible solo en `localhost:5432`, con las credenciales
locales definidas en `.env` (`POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`). El servicio lee esas variables desde el `.env` de la raiz
del repositorio mediante `env_file`; no las declares tambien como variables de
shell salvo que quieras sobrescribirlas.

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

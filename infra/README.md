# Infraestructura local

Kafka es una dependencia externa suministrada por el proyecto educativo: no se
incluye su servidor ni el generador en este repositorio. La aplicacion recibira
su conexion mediante variables de entorno.

## MongoDB para desarrollo

Este Compose es un habilitador local de HRP-33 para que Anahi pueda desarrollar
la persistencia de eventos originales. Redis y Prometheus se incorporaran en sus
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

## PostgreSQL para desarrollo

Este Compose es un habilitador local de HRP-53: deja el motor PostgreSQL
disponible y vacio para que HRP-54 pueda crear las tablas y claves diseñadas en
HRP-52, y para que HRP-63 pueda integrar el Compose final junto con la
aplicacion y MongoDB. No crea ninguna tabla, esquema ni dato de negocio.

### Requisitos

- Docker Desktop iniciado.
- Docker Compose v2 (`docker compose version`).
- Archivo `.env.example` versionado. El `.env` local es opcional y permite
  sobrescribir valores sin subirlos a Git.

### Uso

Desde la raiz del repositorio:

```powershell
docker compose -f infra/compose.dev.yml up -d postgres
docker compose -f infra/compose.dev.yml ps
```

PostgreSQL queda disponible solo en `localhost:5432`. El servicio lee primero
los valores no sensibles de `.env.example` y despues, si existe, los valores
locales de `.env`.

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

## Aplicacion, MongoDB y PostgreSQL

HRP-63 integra la imagen de aplicacion existente con MongoDB y PostgreSQL en el
mismo Compose de desarrollo. Kafka sigue siendo externo y autorizado por el
proyecto educativo: este repositorio no incluye su broker ni su generador.

El modo por defecto permite levantar solo las bases de datos:

```powershell
docker compose -f infra/compose.dev.yml up -d mongo postgres
docker compose -f infra/compose.dev.yml ps
```

Para arrancar tambien la aplicacion, crea un `.env` local y configura los valores
autorizados de `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_TOPICS` y
`KAFKA_CONSUMER_GROUP`. Si Kafka corre en Docker Desktop desde el host, la app
en contenedor normalmente debe usar una direccion alcanzable desde contenedores,
por ejemplo `host.docker.internal:29092`, no `localhost:29092`.

Despues, inicia el perfil de aplicacion:

```powershell
docker compose -f infra/compose.dev.yml --profile app up -d --build app
docker compose -f infra/compose.dev.yml --profile app ps
```

El servicio `app` sobrescribe internamente `MONGODB_URI` a
`mongodb://mongo:27017/hr_pro`, porque dentro de Compose `localhost` seria el
propio contenedor de la aplicacion.

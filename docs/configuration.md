# Runtime configuration

Read from [.env.example](../.env.example) and the actual consumers at the
2026-09-08 code cut. Copy the template only if no local .env exists. Process variables
take precedence where python-dotenv is used.

| Variable | Consumer / requirement |
|---|---|
| KAFKA_BOOTSTRAP_SERVERS | Ingestion; required non-empty authorized endpoint |
| KAFKA_TOPICS | Ingestion; required non-empty comma-separated topic list |
| KAFKA_CONSUMER_GROUP | Ingestion; required non-empty group |
| MONGODB_URI | Ingestion; required; Compose app overrides it with mongo service DNS |
| MONGODB_DB | Ingestion; required database |
| MONGODB_COLLECTION | Ingestion; required raw collection |
| MONGODB_INVALID_COLLECTION | Ingestion; required technical-invalid collection |
| POSTGRES_HOST / POSTGRES_PORT | SQL and API; required environment strings |
| POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD | SQL, API and postgres container; required |
| REDIS_URL | Redis adapter when no client/URL is supplied explicitly |
| HRP_REDIS_PARTIAL_STATE_TTL_SECONDS | Positive integer; default 3600 |
| INGESTION_METRICS_HOST / INGESTION_METRICS_PORT | Metrics module; defaults 0.0.0.0 / 9464 |
| LOG_LEVEL | Template placeholder; current shared logger fixes INFO and does not read it |

Ingestion validates non-empty values; SQL's _require checks presence, not emptiness.
Do not document stronger validation than the code implements.

## Host versus container

| Dependency | Python on host | Process inside Compose |
|---|---|---|
| MongoDB | localhost:27017 | mongo:27017 |
| PostgreSQL | localhost:5432 | postgres:5432 |
| Redis | Not published by current Compose | redis:6379 |
| Metrics | Set bind address for the host explicitly | app:9464 from Prometheus |
| Kafka | Authorized published address | Authorized address reachable from container |

The template REDIS_URL uses internal DNS; a host process cannot use it without an
appropriate network route. Redis integration tests require HRP74_REDIS_URL explicitly;
the supplied CI does not provision Redis.

Configuration modules read several values at import time. Set metrics variables in
the process environment before starting Python; do not rely on a later dotenv import
to change already-initialized module constants. Never print .env or expanded Compose
configuration to public logs; use `config --quiet`.

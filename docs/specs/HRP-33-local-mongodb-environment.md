# HRP-33 — Preparar MongoDB local para desarrollo

**Jira:** HRP-33  
**Tipo:** habilitador de desarrollo para la persistencia raw  
**Dependencias:** Docker Desktop local; no depende de conocer el generador educativo.

## Objetivo

Ofrecer a Anahi un MongoDB local, reproducible y aislado para implementar y
probar la persistencia de mensajes originales de Kafka.

## Alcance

- Un servicio MongoDB de desarrollo con volumen persistente y healthcheck.
- Acceso limitado a `localhost` y URI local documentada.
- Instrucciones minimas de inicio y parada.

## Fuera de alcance

- Dockerizar la aplicacion, PostgreSQL, Redis, Prometheus o Kafka.
- Crear colecciones, indices o interpretar payloads Kafka: eso pertenece a la
  implementacion de HRP-33 y a la evidencia de HRP-29.

## Criterios de aceptación

- [ ] `docker compose -f infra/compose.dev.yml up -d mongo` deja MongoDB sano.
- [ ] El servicio no se publica fuera de `localhost`.
- [ ] `.env.example` contiene la URI local y no incluye secretos.
- [ ] La guia distingue este habilitador del Compose final de la plataforma.

## Evidencia esperada

Salida de `docker compose -f infra/compose.dev.yml ps` mostrando el estado
saludable, enlazada en la PR y en el cierre de Jira.

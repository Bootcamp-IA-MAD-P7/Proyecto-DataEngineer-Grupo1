# ADR-0001: Monolito modular con workers independientes

## Estado

Aceptada.

## Contexto

El proyecto requiere ingesta, transformación, almacenamiento y una API, pero el equipo es de cuatro personas y el objetivo es una entrega educativa mantenible.

## Decisión

Se utilizará un único repositorio Python, organizado por módulos. Los componentes se ejecutarán como procesos/servicios distintos cuando proceda: `ingest-worker`, `process-worker`, `api` y `dashboard`.

## Consecuencias

- Menor complejidad operativa que una arquitectura de microservicios.
- Separación clara de responsabilidades y posibilidad de escalar workers.
- Docker Compose coordinará los servicios locales.

# Arnés de pruebas

## Finalidad

El arnés comprueba de manera repetible que un evento pasa desde la entrada hasta los almacenes correctos, sin depender del generador educativo ni de datos externos.

## Capas

1. **Unitarias:** clasificación, validación, claves de agrupación e idempotencia usando fixtures JSON.
2. **Integración:** MongoDB, PostgreSQL y Redis en contenedores temporales.
3. **E2E:** evento fixture -> ingesta -> raw_events -> transformación -> PostgreSQL.
4. **Carga:** reproducción controlada de fixtures para medir consumo y persistencia.

## Fixtures

Los fixtures se crean a partir de la observación autorizada de mensajes, eliminando cualquier dato irrelevante. Se guardan en `tests/fixtures/` y se versionan junto a la spec que los justifica.

## Casos mínimos

- Evento válido de cada tipo.
- Evento con campos ausentes.
- Evento duplicado.
- Datos de una persona recibidos en distinto orden.
- Claves de unión inconsistentes.
- Error transitorio de almacenamiento.


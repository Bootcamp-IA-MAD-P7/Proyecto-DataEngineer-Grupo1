# HRP-30 — Crear consumer Kafka configurable

**Estado:** En curso
**Responsable:** Anahí
**Jira:** HRP-30
**Dependencias:** HRP-28 finalizada; los topics reales se confirman mediante HRP-29.

## Objetivo

Disponer de un consumer Python configurable que reciba mensajes de topics
autorizados, gestione errores y se cierre limpiamente sin interpretar ni exponer el
payload.

## Contexto y alcance

- Incluye: configuración por entorno, polling, logs técnicos y pruebas unitarias con mocks.
- Excluye: persistencia MongoDB, transformación, clasificación, Docker y decisiones semánticas.
- Supuestos verificables: Kafka y los topics se proporcionan mediante variables autorizadas.
- Riesgos: HRP-29 puede modificar el valor operativo de `KAFKA_TOPICS`, no la interfaz.

## Diseño

`KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_CONSUMER_GROUP` y `KAFKA_TOPICS` se leen del
entorno. `KAFKA_TOPICS` admite una lista separada por comas. El consumer registra
solo topic, partición, offset y tamaño del mensaje. La persistencia raw se añade en
HRP-34 y HRP-35.

## Criterios de aceptación

- [ ] Se puede crear el consumer con configuración válida del entorno.
- [ ] Los topics solo proceden de `KAFKA_TOPICS` autorizado.
- [ ] Un mensaje válido suma un contador técnico sin registrar el payload.
- [ ] Un error Kafka o mensaje sin cuerpo no detiene el bucle.
- [ ] El cierre siempre llama a `consumer.close()`.
- [ ] Pruebas unitarias y comprobaciones de calidad pasan.

## Estrategia de pruebas

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Unitario | Configuración válida y topics configurables | Settings esperados |
| Unitario | Error Kafka y mensaje sin cuerpo | Bucle continúa hasta el siguiente mensaje |
| Unitario | Cierre del consumer | `close()` invocado |
| Manual | Broker autorizado tras HRP-29 | Metadatos técnicos, sin payload |

## Evidencia de cierre

- Rama / PR: pendiente.
- Commit: pendiente.
- Comandos ejecutados y resultado: pendiente.
- Comentario Jira con el resultado: pendiente.

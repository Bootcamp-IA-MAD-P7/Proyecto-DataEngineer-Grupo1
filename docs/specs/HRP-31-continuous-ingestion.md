# HRP-31 — Configurar el consumer para recibir mensajes continuamente

**Estado:** En curso
**Responsable:** Anahí
**Jira:** HRP-31
**Dependencias:** HRP-28 finalizada; HRP-29 finalizada; consumer configurable integrado por HRP-30.
**ADR relacionada:** `docs/adr/0003-evidence-first-data-contract.md`

## Objetivo

Validar que el consumer configurable integrado puede mantener el polling contra el
broker Kafka autorizado hasta recibir una orden de parada, sin exponer valores de
payload y sin detenerse ante errores técnicos recuperables.

## Contexto y alcance

- Incluye: configuración local autorizada, recepción continua, logs técnicos,
  cierre limpio y evidencia de validación manual del broker.
- Excluye: lectura del generador educativo, persistencia MongoDB, Redis,
  PostgreSQL, clasificación de fragmentos, validación de negocio y ETL.
- Supuestos verificables: el runtime educativo publica Kafka en
  `localhost:29092`; el topic observado se suministra como `KAFKA_TOPICS=probando`
  en un `.env` local no versionado.
- Riesgos: el runtime local puede no estar disponible aunque el consumer esté
  correctamente configurado; la evidencia debe distinguir conexión fallida de
  validación satisfactoria.

## Diseño

HRP-30 ya proporciona el bucle de polling, la configuración mediante
`KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_CONSUMER_GROUP` y `KAFKA_TOPICS`, la gestión de
errores de polling y el cierre mediante `consumer.close()`.

HRP-31 no fija el topic en código. Para la validación local autorizada se utiliza
`KAFKA_TOPICS=probando` fuera del repositorio. Los logs se limitan a topic,
partición, offset y tamaño del mensaje. No se imprime, almacena ni versiona el
cuerpo de ningún mensaje.

## Criterios de aceptación

- [x] El consumer configurado mantiene el polling hasta una parada controlada.
- [x] Un error de polling recuperable no interrumpe el bucle.
- [x] El cierre controlado invoca `consumer.close()`.
- [x] La configuración de broker, grupo y topics procede del entorno.
- [ ] Una validación manual contra el broker autorizado recibe mensajes desde el
      topic configurado sin mostrar payloads.
- [ ] Las comprobaciones de calidad aplicables pasan en la rama de integración.
- [ ] La evidencia de ejecución y el comentario de cierre se registran en Jira.

## Estrategia de pruebas

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Unitario | Polling, error recuperable y cierre | Tests con mocks de HRP-30 pasan. |
| Manual | Broker local autorizado disponible | Logs técnicos, sin payload, y cierre limpio. |
| Manual | Broker local no disponible | Error técnico de conexión; no se afirma recepción de datos. |
| Calidad | Formato, tipos y tests | `pre-commit`, `ruff`, `mypy` y `pytest` pasan. |

## Evidencia de cierre

- Rama / PR: `feature/HRP-31-continuous-ingestion` / pendiente.
- Commit: pendiente.
- Validación manual inicial (2026-08-28): el consumer arrancó y se suscribió a un
  topic configurado; el motor Linux de Docker Desktop no estaba disponible, por lo
  que no se pudo validar recepción contra el broker. No se registraron payloads.
- Pendiente: arrancar el runtime Kafka autorizado, repetir la prueba manual y
  registrar solo el resultado técnico en Jira.

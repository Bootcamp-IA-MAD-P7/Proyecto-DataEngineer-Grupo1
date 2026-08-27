# Spec — Sprint 1: Preparar el proyecto e iniciar la ingesta

## Objetivo

Dejar una base reproducible, documentada y conectable a Kafka para observar mensajes reales de manera segura.

## Tareas Jira cubiertas

- HRP-21 a HRP-26
- HRP-28 a HRP-31

## Criterios de aceptación

- El repositorio contiene normas de ramas, PR y documentación de arquitectura.
- El contrato inicial enumera la información conocida y sus incógnitas.
- La configuración Kafka se lee desde variables de entorno y no desde código.
- Es posible conectarse al broker y registrar metadatos de mensajes observados.
- No se consulta el código generador de datos.

## Fuera de alcance

- Persistencia en MongoDB.
- Transformación ETL.
- PostgreSQL, Redis, API y frontend.

## Evidencia esperada

- Pull requests vinculadas a Jira.
- Daily compartida.
- Log o captura de conexión a Kafka sin exponer datos innecesarios.


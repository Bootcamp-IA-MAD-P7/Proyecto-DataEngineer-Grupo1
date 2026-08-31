# HR Pro Data Platform — fuente ejecutiva

**Actualización:** 2026-08-31

**Estado:** nivel esencial en curso; contrato, consumo Kafka, MongoDB inicial,
deduplicación técnica y manejo de errores ya integrados. ETL de persona completa y
PostgreSQL ejecutable siguen pendientes.

## Problema

HR Pro necesita recibir y organizar información de recursos humanos que llega de forma
continua y heterogénea. El reto no es solo guardar datos: hay que preservar eventos
originales, agrupar fragmentos de una misma persona y ofrecer información fiable para
consulta.

## Objetivo de la solución

Construir un pipeline Dockerizado que:

1. Consuma eventos en tiempo real desde Kafka.
2. Conserve cada evento original y sus metadatos en MongoDB.
3. Valide, clasifique y agrupe los fragmentos de una persona.
4. Publique datos curados e idempotentes en PostgreSQL.
5. Evolucione con logs, pruebas, Redis, métricas, API y un frontend accesible.

## Equipo

| Miembro | Foco principal |
|---|---|
| Miguel | Coordinación, Git, Docker, calidad, documentación y demo |
| Anahí | Kafka y MongoDB |
| Gaby | ETL, Redis y monitorización |
| Johans | PostgreSQL, API y frontend |

## Decisión pedagógica y ética

El generador educativo de eventos se trata como una caja negra. El equipo utiliza el
README público, las instrucciones autorizadas y los mensajes recibidos desde Kafka,
pero no lee ni analiza el código que los produce. Esto permite trabajar como en un
caso real de integración con un sistema externo.

## Criterio de éxito

La demo final debe evidenciar un flujo continuo y trazable desde Kafka hasta las
consultas finales, pasando por MongoDB y PostgreSQL, con observabilidad y una interfaz
sencilla de consulta.

## Hito actual

La plataforma ya puede conectarse, consumir de forma continua y persistir fragmentos
iniciales en MongoDB sin exponer payloads en logs. El siguiente corte vertical es
alinear el sobre raw definitivo y usarlo como base segura para ETL y PostgreSQL.

# HRP-26 — Crear README inicial con objetivo, tecnologías e instrucciones

**Estado:** Implementada; pendiente de integración de la PR
**Responsable:** Miguel Redondo Núñez
**Jira:** HRP-26
**Dependencias:** HRP-23 y HRP-24

## Objetivo

Permitir que una persona nueva entienda el alcance, las reglas de datos, la
arquitectura y el flujo de contribución sin recorrer el código.

## Criterios de aceptación

- [x] El README explica propósito, arquitectura objetivo y alcance por fases.
- [x] La prohibición de inspeccionar el generador es visible y explícita.
- [x] Enlaza la documentación operativa, SDD, specs, ADRs y dailies.
- [x] Describe la rama de integración y la forma de iniciar una tarea.
- [x] Define un punto de entrada común para Codex, Gemini y Claude, estándares
      centralizados y roles/workflows de IA versionados.
- [x] Añade instrucciones reproducibles para arrancar el entorno Kafka educativo
      autorizado, sin inspeccionar el generador ni versionar configuración local.

## Pendiente deliberado

Las instrucciones de MongoDB y PostgreSQL no se publican como definitivas hasta que
estén implementadas y verificadas por sus responsables. El arranque del Kafka
educativo está documentado como dependencia externa autorizada.

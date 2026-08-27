# HRP-26 — Crear README inicial con objetivo, tecnologías e instrucciones

**Estado:** Lista para implementar
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
      centralizados y roles/workflows de IA versionados con una adaptación de Specboot.
- [ ] Añade instrucciones de arranque reproducibles cuando Docker Compose exista.

## Pendiente deliberado

Las instrucciones de Kafka, MongoDB y PostgreSQL no se publican como definitivas
hasta que estén implementadas y verificadas por sus responsables.

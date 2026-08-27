# ADR-0004: Configuración externa y secretos fuera del repositorio

## Estado

Aceptada.

## Decisión

Los endpoints, credenciales y parámetros operativos se reciben mediante variables de
entorno. El repositorio solo conserva `.env.example` con nombres de variables y valores
no sensibles. Docker Compose consumirá el entorno sin versionar archivos `.env`.

## Consecuencias

- El mismo artefacto se ejecuta localmente y en demo sin modificar código.
- Los secretos no llegan a commits, fixtures, logs ni comentarios Jira.
- Cada nueva variable debe documentarse en README, `.env.example` y runbook.

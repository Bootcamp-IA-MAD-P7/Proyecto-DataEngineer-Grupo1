# HR Pro Data Platform

Plataforma de ingeniería de datos en tiempo real para integrar datos de RR. HH. desde Kafka, conservar los eventos originales en MongoDB y publicar registros integrados en PostgreSQL.

## Estado

El proyecto está en fase de descubrimiento y diseño (Sprint 1). Las decisiones, el contrato de datos y los criterios de aceptación viven en `docs/`.

## Principios de trabajo

- No se lee, clona ni analiza el código que genera los datos del repositorio educativo.
- Las especificaciones y las pruebas se definen antes de implementar una funcionalidad.
- MongoDB conserva eventos crudos; PostgreSQL almacena datos procesados y consultables.
- Cada cambio pasa por una rama, pull request, revisión y validaciones automáticas.

## Documentación

- [Guía de inicio del proyecto](docs/00-project-charter.md)
- [Arquitectura](docs/01-architecture.md)
- [Contrato de datos](docs/02-data-contract.md)
- [Modelo de datos](docs/03-data-model.md)
- [Flujo SDD](docs/04-sdd-workflow.md)
- [Arnés de pruebas](docs/05-test-harness.md)
- [Guía de dailies](docs/dailies/README.md)

## Estructura

```text
docs/       Especificaciones, ADR, runbooks y dailies
src/        Código de aplicación (cuando se implemente)
tests/      Fixtures y pruebas automatizadas
infra/      Infraestructura y configuración de contenedores
scripts/    Comandos de desarrollo reproducibles
```

## Primeros pasos

1. Revisar `docs/specs/sprint-01-foundation-ingestion.md`.
2. Crear una rama asociada a una tarea Jira, por ejemplo `feature/HRP-21-git-workflow`.
3. No implementar comportamiento sin criterios de aceptación y pruebas definidos.


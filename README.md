# HR Pro Data Platform

Plataforma de datos de RR. HH. en tiempo real. Consume eventos publicados en Kafka,
conserva el evento original en MongoDB y publica una vista integrada, trazable e
idempotente en PostgreSQL. Redis, métricas, API y frontend se incorporan en los
sprints posteriores definidos en Jira.

> Estado: Sprint 1 — descubrimiento, diseño y contrato de datos. No se considera
> válido ningún supuesto sobre el payload hasta que HRP-29 lo haya observado desde
> Kafka y lo haya dejado documentado.

## Regla no negociable

El generador de datos educativo es una caja negra: **no se lee, clona, inspecciona
ni analiza su código**. Solo se usan el README público, las instrucciones de
ejecución permitidas y los mensajes realmente recibidos del broker.

## Arquitectura objetivo

```text
Kafka externo -> ingest-worker -> MongoDB (raw_events)
                                  |
                                  v
                         process-worker <-> Redis (estado temporal)
                                  |
                                  v
                           PostgreSQL (datos curados) -> API -> Streamlit

                    logs estructurados + métricas Prometheus en todos los servicios
```

La descripción completa, los límites y las decisiones viven en
[docs/01-architecture.md](docs/01-architecture.md).

## Forma de trabajo

Cada cambio recorre el mismo camino:

`Jira → spec → rama → pruebas → PR → revisión → evidencia de cierre → Jira`

- Rama de integración actual: `develop`. No se trabaja directamente sobre una
  rama de entrega.
- Una funcionalidad no empieza sin criterios de aceptación y casos de prueba.
- Un cierre de Jira debe enlazar evidencia verificable: PR, commit, prueba o
  documento.
- Las decisiones duraderas se registran como ADR; los acuerdos diarios, en
  `docs/dailies/`.

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir una rama o una PR.

## Documentación de referencia

| Necesidad | Documento |
|---|---|
| Alcance y objetivos | [Project charter](docs/00-project-charter.md) |
| Componentes y flujos | [Arquitectura](docs/01-architecture.md) |
| Contrato Kafka y reglas de evidencia | [Contrato de datos](docs/02-data-contract.md) |
| Persistencia raw y curada | [Modelo de datos](docs/03-data-model.md) |
| Método Specification-Driven Development | [Flujo SDD](docs/04-sdd-workflow.md) |
| Pirámide y matriz de pruebas | [Arnés de pruebas](docs/05-test-harness.md) |
| Métricas y operación | [Observabilidad](docs/06-observability.md) y [runbook](docs/07-runbook.md) |
| Ramas, PRs, automatizaciones y tags | [Gobernanza Git](docs/08-git-governance.md) |
| Especificaciones por tarea | [docs/specs](docs/specs/README.md) |
| Acuerdos y decisiones | [ADRs](docs/adr) y [dailies](docs/dailies/README.md) |

## Estructura

```text
docs/       Contratos, specs, ADRs, runbooks y dailies
src/        Aplicación Python modular
tests/      Fixtures autorizados y pruebas automatizadas
infra/      Docker Compose, configuración de servicios y monitorización
scripts/    Comandos reproducibles de desarrollo y calidad
```

## Inicio de una tarea

1. Comprueba que la tarea Jira cumple el Definition of Ready.
2. Crea o actualiza `docs/specs/HRP-XX-*.md` a partir de la plantilla.
3. Crea `feature/HRP-XX-resumen` desde `develop`.
4. Implementa el cambio y las pruebas descritas por la spec.
5. Ejecuta el arnés, abre PR contra `develop` y aporta la evidencia de cierre.

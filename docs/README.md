# Documentación del proyecto

Corte de cierre: 2026-09-08. La documentación vigente describe la implementación
hasta `f3a952b`; la primera entrega documental está integrada en `275131a`.
Las observaciones y dailies son registros fechados, no estados actuales de producto.

## Por dónde empezar

| Necesidad | Documento |
|---|---|
| Visión, progreso y arranque | [README principal](../README.md) |
| Requisitos aceptados y evidencia real | [Matriz de entrega](delivery-evidence.md) |
| Decisión y límites del cierre | [Cierre HRP-93](project-closeout.md) |
| Flujo y componentes efectivamente conectados | [Arquitectura](01-architecture.md) |
| Formas observadas y contrato runtime | [Contrato](02-data-contract.md) |
| Campos, relaciones y persistencia | [Modelo](03-data-model.md) |
| Variables de entorno | [Configuración](configuration.md) |
| Rutas, filtros y errores | [Referencia API](api-reference.md) |
| Métricas y logs realmente emitidos | [Observabilidad](06-observability.md) |
| Ejecutar y diagnosticar | [Runbook](07-runbook.md) |
| Entorno de contribución | [Development guide](development_guide.md) |
| Pruebas y resultados conocidos | [Test harness](05-test-harness.md) |
| PRs y releases | [Gobernanza](08-git-governance.md) |
| Preparar presentación | [Fuentes NotebookLM](presentation-sources/README.md) |
| Jornadas y evolución | [Dailies](dailies/README.md) |
| Qué se revisó y cómo | [Auditoría documental](documentation-audit.md) |

## Decisiones, evidencia y proceso

- [Objetivo y alcance](00-project-charter.md), [DAFO](09-evolving-swot.md),
  [benchmark histórico](10-reference-benchmark.md).
- [SDD](04-sdd-workflow.md), [specs](specs/README.md),
  [observaciones autorizadas](observations/README.md).
- ADRs: [modularidad](adr/0001-monolito-modular.md),
  [raw/curado](adr/0002-raw-and-curated-storage.md),
  [contrato evidence-first](adr/0003-evidence-first-data-contract.md),
  [configuración](adr/0004-configuration-and-secrets.md),
  [ack Kafka](adr/0005-kafka-acknowledgement-after-raw-persistence.md),
  [correlación](adr/0006-person-correlation-key.md),
  [accesibilidad/sostenibilidad](adr/0007-accessibility-and-sustainable-delivery.md).
- [Estándares base](base-standards.md), [backend](backend-standards.md),
  [documentación](documentation-standards.md), [dependencias](external-dependencies.md).
- [Trabajo asistido](onboarding/ai-assisted-workflow.md),
  [política IA](ai/README.md), [roles y skills](../ai-specs/README.md).
- [Infraestructura](../infra/README.md), [scripts](../scripts/README.md),
  [fixtures](../tests/fixtures/README.md).

## Precedencia y mantenimiento

La matriz es canónica para la aceptación comunicada por el responsable.
Código y configuración determinan comportamiento; las guías describen ese corte.
Una spec expresa requisitos y evidencia de una tarea, no sustituye una prueba actual.
Una observación acotada no establece verdad universal de negocio.
Plantillas y prompts no son evidencia de ejecución.

Las reconstrucciones diarias declaran su origen Git, sin inventar reuniones ni
bloqueos. Para NotebookLM cargar el paquete recomendado, no mezclarlo indiscriminadamente
con notas de sprint antiguas que describen trabajo entonces pendiente.

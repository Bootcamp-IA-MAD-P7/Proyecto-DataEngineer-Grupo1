# Development guide

Para instalar y ejecutar, seguir el [README](../README.md), el
[catálogo de variables](configuration.md) y el [runbook](07-runbook.md).
No hay un comando que arranque toda la transformación continua hasta PostgreSQL.

## Entorno

Python 3.11+, venv y `python -m pip install -e ".[dev]"`.
Instalar hooks con `pre-commit install`. No sobrescribir un .env existente.
Compose proporciona servicios locales; Kafka es externo. La API requiere un proceso
uvicorn separado. Redis no publica puerto de host por defecto.

## Contribuir

1. Comprobar rama y `git status --short`; conservar cambios ajenos.
2. Consultar [SDD](04-sdd-workflow.md) y la spec HRP correspondiente.
3. Trabajar en rama de tarea contra develop; para asistencia Codex se usa `codex/`.
4. Ejecutar controles proporcionales al cambio; registrar resultados y omisiones,
   nunca marcar automáticamente todos los tests como pasados.
5. Título de PR: `HRP-93 docs: reconcile project documentation` para esta tarea.
6. Publicar y seguir [gobernanza](08-git-governance.md); un commit local no aparece
   en GitHub hasta el push.

## Cambios exclusivamente documentales

Revisar enlaces, rutas, comandos, cifras, fuentes y `git diff --check`.
Si se modifican specs, ejecutar `python scripts/validate_specs.py`.
La autorización expresa de Miguel cubre esta revisión HRP-93 sin pedir otra
aprobación para editar; no desactiva los checks remotos ni autoriza cambiar código.
No arrancar servicios ni ejecutar pruebas con escrituras solo por retocar Markdown.

Para cambios funcionales, [test harness](05-test-harness.md) detalla Ruff, mypy,
pytest y las condiciones de integración. El bloqueo nativo de Kafka en Windows
debe registrarse; no se deshabilitan controles de seguridad del equipo.

## Contexto asistido

[Onboarding](onboarding/ai-assisted-workflow.md), [AGENTS](../AGENTS.md) y
[política IA](ai/human-approval-policy.md). La documentación histórica no debe
usarse para inferir que una característica sigue pendiente cuando su PR está integrada.

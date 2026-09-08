# Gobernanza Git, PRs y releases

Corte documental2026-09-08. Develop es integración; se han comprobado referencias
remotas y el historial, no la configuración actual del ruleset ni todos los runs.

## Evidencia local frente a configuración remota

Workflows, CODEOWNERS y labeler están versionados. La revisión independiente y la
protección de develop forman parte de la política del equipo. El repositorio no
demuestra por sí solo que una regla esté activada actualmente en GitHub.
No se atribuyen aprobaciones a revisores sin evidencia.

## Flujo

Rama por tarea → PR contra develop → checks y revisión → merge → evidencia de entrega.
Prefijos históricos: feature/, docs/, fix/, chore/; la revisión actual usa
codex/HRP-93-project-closeout. No reescribir historial ni forzar pushes.

Para esta extensión Miguel autoriza editar y fusionar directamente sin revisores.
Esta excepción de cierre no publica releases automáticamente ni reescribe historial.

## Título válido y diagnóstico de checks

El workflow [PR governance](../.github/workflows/pr-governance.yml) exige:

```text
HRP-93 docs: reconcile project documentation and presentation sources
```

Formato real: HRP-número, espacio, tipo (feat/fix/docs/test/refactor/chore/ci),
dos puntos, espacio y resumen no vacío. Se valida el **título**, no el cuerpo.
El error mostrado por el usuario corresponde a ese formato. El aviso de Node es
otro mensaje y no explica ese fallo de validación. Este cambio no modifica actions.

Los checks pueden aparecer en distintos workflows/jobs y estados; sin ver el run no
se puede concluir por una captura que todos fallen o que todos estén aprobados.

## Automatización versionada

| Workflow | Función y límite |
|---|---|
| quality | Specs, pre-commit, Ruff, mypy, pytest y Compose; resultado del run no inferido |
| PR governance | Valida título en eventos de PR, incluido edited |
| PR labels | Etiquetado por rutas; no prueba calidad |
| Generate presentation daily | Genera borrador diario mediante workflow manual; requiere completar contexto |
| Create release tag | Workflow manual, valida formato y existencia, crea y publica tag anotado |

El workflow de tags no ejecuta por sí mismo una demo ni la suite de release.
No crea una GitHub Release. No mover un tag publicado.
0.1.0 en pyproject es versión del paquete, no prueba de un tag.
Los tags de hitos sugeridos históricamente no se presentan como publicados.

## Estado de la revisión HRP-93

PR #80 integró la primera documentación en 275131a; el código permanece en f3a952b.
Las correcciones posteriores pertenecen a la rama local hasta su push.
Un archivo editado o un commit local **no se ve en GitHub automáticamente**.

Comprobar sin mutar estado remoto:

```bash
git status --short
git branch --show-current
git log -5 --oneline
git diff --stat
```

Publicar, fusionar y etiquetar son acciones diferentes de revisar Markdown.
Esta revisión no las realiza. Para revertir documentos identificar su commit y usar
un revert acotado, nunca resetear o descartar trabajo ajeno.

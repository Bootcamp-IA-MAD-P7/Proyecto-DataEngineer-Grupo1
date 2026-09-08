# HRP-21 — Configurar ramas, pull requests y norma de commits

**Estado de integración (2026-09-08):** Task changes integrated in develop; acceptance criteria not re-executed here.
**Git evidence:** [963a7c3](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/963a7c3) / [PR #1](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/1) (2026-08-27).
**Closeout interpretation:** Workflows and CODEOWNERS are versioned; remote protection settings and latest check results were not re-queried.

This integration record does not assert current Jira status, reviewer approval identity
or a new passing test run. [Current documentation](../README.md) and
[acceptance/evidence matrix](../delivery-evidence.md) define the closeout reading.

## Historical specification and task evidence

The scope, criteria, checkboxes and test results below are the task's original record.
They are not a live progress dashboard. Pending-review/merge references in this
historical record are superseded by the integration evidence above; unresolved
functional limitations are not automatically marked as passed.

**Original recorded status:** Lista para implementar

**Responsable:** Miguel Redondo Núñez
**Jira:** HRP-21
**Dependencia:** HRP-20 (finalizada)

## Objetivo

Hacer que cada cambio sea trazable y revisable antes de llegar a `develop`.

## Diseño acordado

- `develop` es la única rama de integración actual.
- Ramas cortas por tarea: `feature/HRP-XX-*`, `docs/HRP-XX-*`, `fix/HRP-XX-*` o
  `chore/HRP-XX-*`.
- Cada PR apunta a `develop`, tiene una clave Jira, una spec vinculada y al menos un
  revisor distinto del autor.
- Los commits incluyen la clave Jira y siguen Conventional Commits.
- GitHub Actions ejecuta formato, lint, tipos y pruebas en cada PR y push a `develop`.

## Criterios de aceptación

- [x] La rama de integración del repositorio es `develop`.
- [x] Existe una plantilla de PR con la evidencia y pruebas exigidas.
- [x] Existe una guía de contribución con ramas, commits y reglas de secretos.
- [x] CI se ejecuta para PRs y pushes a `develop`.
- [ ] Un cambio de prueba recorre el flujo completo: rama → PR → revisión → merge.

## Pruebas y evidencia

| Nivel | Caso | Evidencia esperada |
|---|---|---|
| Manual | Crear rama con clave Jira | Nombre conforme a la convención |
| CI | Abrir PR contra `develop` | Workflow `quality` en verde |
| Revisión | Validar plantilla de PR | Checklist completada por revisor |

## Riesgos

La protección de rama en GitHub depende de los permisos de la organización. Hasta que
se active, la regla de PR se mantiene como acuerdo operativo del equipo.

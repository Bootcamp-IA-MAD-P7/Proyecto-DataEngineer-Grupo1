# HRP-21 — Configurar ramas, pull requests y norma de commits

**Estado:** Lista para implementar
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

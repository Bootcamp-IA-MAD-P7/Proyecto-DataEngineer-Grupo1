# Gobernanza Git, GitHub y releases

## Roles del equipo

| Responsable | Áreas principales |
|---|---|
| Miguel | Coordinación, Git, Docker, calidad, documentación y demo |
| Anahí | Kafka y MongoDB |
| Gaby | ETL, Redis y monitorización |
| Johans | PostgreSQL, API y frontend |

## Flujo de ramas

```text
feature/docs/fix/chore (HRP-XX) -> pull request + CI + revisión -> develop
                                                                    |
                                                                    v
                                                   tag de hito revisado para demo
```

- `develop` es la integración actual.
- Cada rama contiene una sola tarea Jira.
- Las PRs se abren contra `develop`; no se fusionan por cuenta propia.
- El ruleset **Protect develop** exige pull request, una aprobación, revisión de
  `CODEOWNERS`, conversaciones resueltas y bloquea borrados y force-pushes.
- Los checks `quality`, `PR governance` y `PR labels` están detectados y forman parte
  del control previo al merge.

## Automatizaciones activas

| Automatización | Disparador | Resultado |
|---|---|---|
| `quality` | PR o push a `develop` | Formato, lint, tipos y tests |
| `PR governance` | PR a `develop` | Rechaza títulos sin clave Jira y tipo convencional |
| `PR labels` | PR a `develop` | Etiqueta por área modificada |
| `Generate presentation daily` | Ejecución manual | Genera una daily y abre una PR; nunca hace push directo a `develop` |
| `Create release tag` | Ejecución manual | Valida y crea un tag anotado inmutable |

Las etiquetas `area:docs`, `area:quality`, `area:ingestion`, `area:storage`,
`area:api` y `area:infra` están creadas. La asignación vive en
`.github/labeler.yml`.

## Política de tags y releases

No se etiqueta cada commit. Un tag representa un estado reproducible que puede
demostrarse en una revisión o demo.

| Hito | Tag sugerido | Condición |
|---|---|---|
| Fundaciones verificadas | `v0.1.0-foundation` | Arquitectura, SDD y CI revisados |
| Nivel esencial | `v0.2.0-essential` | Kafka → MongoDB → PostgreSQL demostrable |
| Nivel medio | `v0.3.0-quality` | Docker, logs y tests operativos |
| Nivel avanzado | `v0.4.0-observability` | Redis, métricas y API operativos |
| Demo final | `v1.0.0` | Todos los checks del briefing superados |

La persona que coordina ejecuta manualmente el workflow **Create release tag** tras
aprobación del equipo, indicando el tag y el commit o rama validada. El workflow
comprueba el formato SemVer, rechaza tags existentes y crea un tag anotado. No crea
releases de GitHub ni modifica ramas.

Un tag publicado es inmutable. Si aparece un error, se crea uno nuevo; no se mueve ni
se sobrescribe el anterior.

## CODEOWNERS activo

`.github/CODEOWNERS` está configurado con los handles confirmados: Miguel
(`@miguelRedondoWeb`), Anahí (`@anahi-am`), Gaby (`@gabrielagranja`) y Johans
(`@johans-salas`). GitHub solicitará automáticamente revisión según las rutas
modificadas cuando se abra una PR.

El ruleset activo convierte la revisión de `CODEOWNERS` en requisito de merge cuando
la ruta modificada lo requiere.

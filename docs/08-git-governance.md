# Gobernanza Git, GitHub y releases

## Roles del equipo

| Persona | Responsable | Áreas principales |
|---|---|---|
| Persona 1 | Miguel | Coordinación, Git, Docker, calidad, documentación y demo |
| Persona 2 | Anahí | Kafka y MongoDB |
| Persona 3 | Gaby | ETL, Redis y monitorización |
| Persona 4 | Johans | PostgreSQL, API y frontend |

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
- La protección de rama se activa en GitHub cuando el propietario de la organización
  tenga permisos: PR obligatoria, una aprobación y workflows `quality` y
  `PR governance` en verde.

## Automatizaciones activas

| Automatización | Disparador | Resultado |
|---|---|---|
| `quality` | PR o push a `develop` | Formato, lint, tipos y tests |
| `PR governance` | PR a `develop` | Rechaza títulos sin clave Jira y tipo convencional |
| `PR labels` | PR a `develop` | Etiqueta por área modificada |
| `Create release tag` | Ejecución manual | Valida y crea un tag anotado inmutable |

Antes de usar `PR labels`, un administrador debe crear una vez estas etiquetas:
`area:docs`, `area:quality`, `area:ingestion`, `area:storage`, `area:api` y
`area:infra`. La configuración está en `.github/labeler.yml`.

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

## CODEOWNERS, cuando se conozcan los usuarios

No se usan nombres personales como si fueran identificadores de GitHub. Cuando Miguel,
Anahí, Gaby y Johans confirmen sus handles, se crea `.github/CODEOWNERS` para asignar
revisión automática por rutas. Hasta entonces, la tabla de revisión de
[CONTRIBUTING.md](../CONTRIBUTING.md) es la fuente de verdad.

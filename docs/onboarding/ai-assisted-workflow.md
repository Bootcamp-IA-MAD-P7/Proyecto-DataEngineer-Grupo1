# Guía de trabajo asistido por IA

Esta guía adopta la estructura de **LIDR Specboot** adaptada a HR Pro: una fuente
única de estándares, roles reutilizables de IA y workflows versionados. La IA acelera
el trabajo, pero nunca sustituye la revisión humana ni convierte supuestos en hechos.

## Estructura instalada

```text
AGENTS.md                         # punto de entrada para cualquier asistente
docs/base-standards.md            # reglas únicas y obligatorias
docs/backend-standards.md         # Python, Kafka, bases de datos y API
docs/documentation-standards.md   # specs, evidencias y dailies
ai-specs/agents/                  # rol de IA según área del equipo
ai-specs/skills/                  # workflows reutilizables
docs/specs/                       # SDD por tarea Jira
```

Los archivos `codex.md`, `GEMINI.md` y `CLAUDE.md` apuntan al mismo contexto para que
todos trabajen con las mismas reglas independientemente de la IA.

## Flujo común del equipo

```text
Preparar ordenador una vez
  → Clonar y verificar el repositorio
  → Arrancar cada día desde develop actualizado
  → Jira → spec → rama → cambio + tests
  → harness → PR → revisión humana → Jira
```

No se salta un paso por usar IA. La IA trabaja dentro de este flujo.

## 1. Preparación única por ordenador

Instalar estas herramientas antes de clonar:

| Herramienta | Uso | Obligatoria ahora |
|---|---|---|
| Git | Clonar, ramas y PRs | Sí |
| Python 3.11 | Aplicación y tests | Sí |
| VS Code + extensión Python | Edición y terminal | Recomendada |
| Docker Desktop | MongoDB, PostgreSQL y Redis | Instalar ya; usar desde Sprint 2 |
| Node.js 20.19+ | Solo OpenSpec opcional | No |

## 2. Primera clonación y verificación

Ejecutar una sola vez por integrante:

```powershell
git clone https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1.git
cd Proyecto-DataEngineer-Grupo1
git switch develop
git pull --ff-only

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pre-commit install
pre-commit run --all-files
pytest
```

Si estos comandos terminan correctamente, la persona puede empezar una tarea. Si fallan, no crea ramas ni pide código a la IA: comunica el error al equipo.

## 3. Arranque diario

Cada día, antes de trabajar:

```powershell
git switch develop
git pull --ff-only
.\.venv\Scripts\Activate.ps1
```

Después abre Jira, selecciona solo una tarea lista y sigue el flujo de esta guía.

## 4. Preparación única por entorno Python

El entorno virtual se recrea solo cuando cambie Python o si se rompe. Para actualizar dependencias tras una PR:

```powershell
python -m pip install -e ".[dev]"
```

Las herramientas Python de calidad se instalan con `.[dev]`; no hay que instalarlas una a una. Docker solo será necesario cuando una tarea use servicios locales.

## 5. Specboot y OpenSpec: qué está instalado y qué es opcional

La capa Specboot ya está integrada y adaptada al proyecto: no hay que descargar ni
copiar otra plantilla. Cada clon recibe `AGENTS.md`, `docs/` y `ai-specs/`.

OpenSpec añade comandos para gestionar cambios (`/ff`, `/apply`, `/verify`,
`/adversarial-review`, `/archive`). Es opcional para este bootcamp y se instala una vez
por ordenador, no una vez por rama. Requiere Node.js 20.19 o superior:

```powershell
node --version
npm install -g @fission-ai/openspec@latest
openspec --version
```

No ejecutar `openspec init` individualmente. Si se adopta, Miguel abrirá una única PR
de integración, revisará los artefactos generados y dejará su configuración compartida.
Hasta entonces, el workflow `ai-specs/skills/spec-driven-task/SKILL.md` es el flujo
oficial y no depende de Node.js.

## 6. Flujo obligatorio por tarea Jira

1. Abrir la tarea Jira y comprobar responsable, dependencia y criterio de aceptación.
2. Elegir el rol: Anahí `ingestion-engineer`, Gaby `transformation-engineer`, Johans
   `serving-engineer` y Miguel `platform-engineer`.
3. Cargar `ai-specs/skills/enrich-us/SKILL.md` y actualizar o crear
   `docs/specs/HRP-XX-resumen.md`.
4. Crear el paquete de contexto si se usará IA:

   ```powershell
   .\scripts\new-task-packet.ps1 -JiraKey HRP-XX -Slug resumen
   ```

5. Crear una rama desde `develop`:

   ```powershell
   git switch develop
   git pull --ff-only
   git switch -c feature/HRP-XX-resumen
   ```

6. Implementar el cambio mínimo, su prueba y documentación asociada.
7. Ejecutar el arnés:

   ```powershell
   pre-commit run --all-files
   pytest
   ```

8. Cargar `ai-specs/skills/code-auditing/SKILL.md` y revisar el resultado.
9. Abrir PR contra `develop`, solicitar revisión y no fusionarla personalmente.
10. Tras merge, cargar `ai-specs/skills/update-docs/SKILL.md` y escribir el comentario
    de cierre con evidencia en Jira.

## 7. Prompts reutilizables

### Inicio de tarea

```text
Trabajo en HR Pro Data Platform. Lee AGENTS.md, docs/base-standards.md,
docs/04-sdd-workflow.md, la spec de HRP-XX y el rol/skill aplicable en ai-specs antes
de proponer cambios.

Mi tarea Jira es: [pegar título y enlace].
No leas, clones ni analices el generador educativo. Usa solo documentación autorizada y observaciones Kafka registradas.

Primero responde con: objetivo verificable, dependencias, alcance/no alcance,
criterios de aceptación, riesgos, pruebas necesarias y archivos que cambiarías.
No escribas código ni cambies Jira hasta que valide el plan.
```

### Implementación después de aprobar el plan

```text
Implementa exclusivamente el plan aprobado para HRP-XX en la rama actual siguiendo
ai-specs/skills/spec-driven-task/SKILL.md.
Mantén los cambios pequeños; añade o actualiza tests y documentación; no introduzcas secretos ni datos personales. Ejecuta pre-commit y pytest. Al terminar, entrega: resumen, archivos modificados, comandos ejecutados con resultado, riesgos pendientes, propuesta de título/descripción de PR y comentario Jira. No hagas merge ni cierres Jira.
```

### Revisión de una PR

```text
Revisa esta PR contra la tarea HRP-XX y su spec. Comprueba alcance, pruebas, idempotencia, manejo de errores, separación entre MongoDB raw, Redis temporal y PostgreSQL curado, seguridad de secretos y documentación. Separa bloqueantes, sugerencias y preguntas. No apruebes ni fusiones la PR; la decisión será humana.
```

### Cierre de tarea

```text
Con la PR fusionada y los resultados de calidad disponibles, redacta un comentario de cierre para HRP-XX con resultado, evidencia, validación, dependencia siguiente y riesgos. No afirmes observaciones Kafka ni resultados que no estén documentados.
```

## 8. Qué hacer si falta información

No adivinar. Crear una tarea de descubrimiento, registrar la incógnita en la spec o ADR y dejar la tarea bloqueada. Para datos Kafka, HRP-29 es la fuente de evidencia; el README público no sustituye un mensaje observado.

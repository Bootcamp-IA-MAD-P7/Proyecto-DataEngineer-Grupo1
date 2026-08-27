# Guía de trabajo asistido por IA

Esta guía permite que cualquier integrante use SDD, el arnés de calidad y un asistente de IA sin depender de conocimiento previo. La IA acelera el trabajo, pero nunca sustituye la revisión humana ni convierte supuestos en hechos.

## 1. Preparación única por ordenador

Instalar Git, Python 3.11 y Docker Desktop. Tras clonar el repositorio, ejecutar:

```powershell
git switch develop
git pull --ff-only
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pre-commit install
pre-commit run --all-files
pytest
```

Las herramientas Python de calidad se instalan con `.[dev]`; no hay que instalarlas una a una. Docker solo será necesario cuando una tarea use servicios locales.

## 2. OpenSpec y Specboot: uso recomendado

El repositorio ya incluye su propio sistema SDD, paquetes de tarea, prompts y arnés. No importar Specboot completo sobre esta estructura: duplicaría reglas y podría crear conflictos en `docs/`.

OpenSpec es opcional y se instala una vez por ordenador, no una vez por rama. Requiere Node.js 20.19 o superior:

```powershell
node --version
npm install -g @fission-ai/openspec@latest
openspec --version
```

No ejecutar `openspec init` individualmente. Miguel abrirá una PR de integración específica si el equipo decide adoptarlo; así se revisan los archivos que genere y se evita que cuatro configuraciones distintas entren en conflicto.

La inspiración de Specboot se usa de forma ligera: `AGENTS.md` es la fuente común de instrucciones y los archivos `codex.md`, `CLAUDE.md` y `GEMINI.md` remiten a ella.

## 3. Flujo obligatorio por tarea Jira

1. Abrir la tarea Jira y comprobar responsable, dependencia y criterio de aceptación.
2. Actualizar o crear `docs/specs/HRP-XX-resumen.md`.
3. Crear el paquete de contexto si se usará IA:

   ```powershell
   .\scripts\new-task-packet.ps1 -JiraKey HRP-XX -Slug resumen
   ```

4. Crear una rama desde `develop`:

   ```powershell
   git switch develop
   git pull --ff-only
   git switch -c feature/HRP-XX-resumen
   ```

5. Implementar el cambio mínimo, su prueba y documentación asociada.
6. Ejecutar el arnés:

   ```powershell
   pre-commit run --all-files
   pytest
   ```

7. Abrir PR contra `develop`, solicitar revisión y no fusionarla personalmente.
8. Tras merge, escribir el comentario de cierre con evidencia en Jira.

## 4. Prompts reutilizables

### Inicio de tarea

```text
Trabajo en HR Pro Data Platform. Lee AGENTS.md, CONTRIBUTING.md,
docs/04-sdd-workflow.md y la spec de HRP-XX antes de proponer cambios.

Mi tarea Jira es: [pegar título y enlace].
No leas, clones ni analices el generador educativo. Usa solo documentación autorizada y observaciones Kafka registradas.

Primero responde con: objetivo verificable, dependencias, alcance/no alcance,
criterios de aceptación, riesgos, pruebas necesarias y archivos que cambiarías.
No escribas código ni cambies Jira hasta que valide el plan.
```

### Implementación después de aprobar el plan

```text
Implementa exclusivamente el plan aprobado para HRP-XX en la rama actual.
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

## 5. Qué hacer si falta información

No adivinar. Crear una tarea de descubrimiento, registrar la incógnita en la spec o ADR y dejar la tarea bloqueada. Para datos Kafka, HRP-29 es la fuente de evidencia; el README público no sustituye un mensaje observado.

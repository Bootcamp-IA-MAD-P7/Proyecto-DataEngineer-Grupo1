# Guía de contribución

Este repositorio usa `develop` como rama de integración durante el desarrollo.
No se hacen commits directos sobre ella: todo cambio llega mediante pull request.

## Flujo por tarea

1. Comprueba que la tarea Jira tiene responsable, objetivo, dependencias y criterios
   de aceptación.
2. Crea o actualiza su especificación: `docs/specs/HRP-XX-resumen.md`.
3. Parte de `develop` y crea una rama con este formato:

   ```text
   feature/HRP-XX-resumen-corto
   fix/HRP-XX-resumen-corto
   docs/HRP-XX-resumen-corto
   chore/HRP-XX-resumen-corto
   codex/HRP-XX-resumen-corto
   ```

4. Realiza cambios pequeños, coherentes y acompañados de pruebas cuando apliquen.
5. Ejecuta el arnés local antes de abrir la PR.
6. Abre una PR hacia `develop`, asigna un revisor y vincula la tarea Jira.
7. Registra la evidencia final en Jira usando la plantilla de HRP-22.

## Convención de commits

Usamos Conventional Commits y la clave Jira al inicio:

```text
HRP-23 docs: define architecture boundaries
HRP-30 feat: add Kafka consumer bootstrap
HRP-36 fix: make raw-event persistence idempotent
HRP-65 test: cover invalid Kafka event
```

Tipos permitidos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.
Un commit no mezcla cambios no relacionados.

## Calidad mínima

```powershell
python -m pip install -e ".[dev]"
pre-commit install
pre-commit run --all-files
pytest
```

Las pruebas de integración y E2E sintético ya existen. Véase
[el arnés de pruebas](docs/05-test-harness.md) para dependencias, limpieza de fixtures
y resultados conocidos. Si una prueba no se ejecuta o no aplica, indicarlo en la PR;
no marcarla como pasada.

## Revisión por áreas

La persona responsable de una tarea propone la PR; la revisión la hace otra persona.
La distribución preferente es:

| Área afectada | Responsable | Revisor recomendado |
|---|---|---|
| Gestión, Git, Docker, calidad, documentación | Miguel (`@miguelRedondoWeb`) | Anahí, Gaby o Johans |
| Kafka y MongoDB | Anahí (`@anahi-am`) | Gaby o Miguel |
| ETL, Redis y monitorización | Gaby (`@gabrielagranja`) | Johans o Anahí |
| PostgreSQL, API y frontend | Johans (`@johans-salas`) | Miguel o Gaby |

Una PR que cambia límites entre áreas debe tener, como mínimo, un revisor de cada
área afectada. `.github/CODEOWNERS` solicita automáticamente la revisión por rutas;
la protección de `develop` debe exigir la revisión de propietarios de código.

## Reglas de datos y secretos

- Nunca subas `.env`, credenciales, eventos completos capturados ni volúmenes Docker.
- No leas ni clones el código del generador educativo.
- Los fixtures pueden ser sintéticos, identificados como tales y coherentes con
  contratos autorizados; los derivados de observación se minimizan y anonimizan.
  Ninguno debe presentarse como evidencia de identidad o payload real.
- No marques una tarea como finalizada sin evidencia revisable.

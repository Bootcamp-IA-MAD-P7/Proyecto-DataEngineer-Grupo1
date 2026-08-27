# Fuentes para la presentación en NotebookLM

Esta carpeta contiene fuentes concisas, ordenadas y aptas para cargar en NotebookLM
(Gemini) al preparar la presentación técnica solicitada en el briefing. No sustituye
la documentación de ingeniería: selecciona y resume lo que la presentación necesita.

## Qué subir a NotebookLM

1. `00-project-story.md`: problema, alcance, equipo y niveles del briefing.
2. `01-architecture-story.md`: recorrido del dato y decisiones técnicas.
3. `evidence/`: capturas, enlaces de PR, resultados de pruebas y demos validadas.
4. `daily/`: evolución cronológica, decisiones, bloqueos y logros.
5. `manifest.md`: lista curada de fuentes y estado de actualización.

## Regla de calidad

- Solo se registran hechos demostrables: enlaces, commits, comandos, métricas o
  decisiones aprobadas.
- Nunca incluir secretos, `.env`, payloads completos de Kafka ni datos personales.
- No describir el generador de datos ni usar información obtenida de su código.
- Un daily incompleto es preferible a uno que inventa avances.

## Automatización disponible

Ejecuta desde la raíz del repositorio:

```powershell
.\scripts\new-presentation-daily.ps1
```

El script crea `daily/YYYY-MM-DD.md` con fecha, participantes, commits recientes y
estado local de Git. Después cada miembro completa las secciones de Jira, decisiones,
evidencia y bloqueos. También existe el workflow manual **Generate presentation daily**
en GitHub Actions: genera el fichero y abre una pull request para revisión humana; no
puede hacer *push* directo a `develop`.

No se programa un commit diario automático: el contenido de una presentación debe
representar actividad real y una ejecución vacía añadiría ruido al historial.

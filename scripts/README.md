# Scripts de documentación y calidad

Ejecutar desde la raíz del repositorio.

| Comando | Función y efectos |
|---|---|
| `python scripts/validate_specs.py` | Lee specs HRP y comprueba estructura mínima; no certifica cumplimiento |
| `./scripts/new-task-packet.ps1 -JiraKey HRP-XX -Slug resumen` | Ejemplo de plantilla: sustituir HRP-XX por una clave numérica real; crea Markdown |
| `./scripts/new-presentation-daily.ps1 -Date YYYY-MM-DD` | Sustituir la fecha; crea un borrador de fuente diaria, no un acta completada |

Los dos scripts PowerShell rechazan sobrescribir un fichero existente salvo
`-Force`. No usar esa opción sobre las dailies de cierre para regenerarlas.
El script diario usa commits desde el día anterior, sin límite superior de fecha:
**no es adecuado para reconstruir una jornada antigua de forma automática**.
Además incluye el estado Git actual, no el estado histórico de aquella fecha.
Por eso las reconstrucciones HRP-93 se contrastan con integraciones fechadas
en [dailies](../docs/dailies/README.md).

El script de paquetes solo genera una plantilla; completar alcance, evidencia y
restricciones antes de usarla. No lee Jira ni genera avances reales del equipo.

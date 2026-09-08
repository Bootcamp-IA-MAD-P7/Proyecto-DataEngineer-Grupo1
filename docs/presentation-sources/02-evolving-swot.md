# DAFO de cierre — fuente para exposición

| Fortalezas | Debilidades |
|---|---|
| Raw y procedencia preservados; correlación explícita; specs y PRs | No hay worker productivo completo; no hay benchmark; resultado local no verde |
| Componentes SQL, API y métricas con pruebas versionadas | API sin autenticación; Redis efímero; frontend excluido |

| Oportunidades | Amenazas |
|---|---|
| Conectar la orquestación, medir con carga autorizada y añadir producto sobre API | Colisiones de claves aparentes; drift documental; dependencia de entornos externos |
| Mejorar auth y métricas antes de exposición productiva | Confundir tests sintéticos con una demo real o aceptación con verificación |

## Evolución que merece una diapositiva

De desconocer las formas del dato a observarlas de forma acotada; de candidatos
de correlación a una decisión operacional que conserva incertidumbre; de diseño
SQL a componentes consultables. El cierre reconoce lo que está conectado y lo que no.

No afirmar reducción de costes, energía, tiempos o defectos sin medición.
No atribuir puntuaciones de rendimiento a miembros del equipo.
[DAFO canónico](../09-evolving-swot.md) y [cronología](03-delivery-timeline.md).

# Fuentes de cierre para NotebookLM

## Qué cargar

**Opción recomendada:** cargar únicamente [NOTEBOOKLM-PACK.md](NOTEBOOKLM-PACK.md).
Contiene historia, arquitectura real, cifras con alcance, cronología, bibliografía,
guion de 12 diapositivas, notas y prompt listo para usar. Es autocontenido:
no depende de que NotebookLM recorra enlaces relativos para conocer la historia.

**Opción ampliada:** añadir [referencias](05-references.md) y las
[dailies](daily/README.md) si necesitas más detalle histórico. No cargar plantillas
vacías ni usar notas antiguas como si describieran el estado actual.

## Material complementario

[Historia](00-project-story.md) · [Arquitectura](01-architecture-story.md) ·
[DAFO](02-evolving-swot.md) · [Cronología](03-delivery-timeline.md) ·
[Aceptación](04-final-acceptance.md) · [Manifest](manifest.md) ·
[Evidencia](evidence/README.md).

El paquete es una fuente textual para producir una presentación, no un deck ya
generado. Los gráficos propuestos tienen datos explícitos; no se inventan métricas
ni capturas. Frontend excluido. La matriz mide aceptación, no verificación técnica.

## Comprobación del resultado generado

Comprobar que diga «HRP-71 sintético», «pipeline continuo» y «aceptación del responsable»;
que muestre `app`, `etl` y `api` como procesos separados y conserve el resultado local histórico;
que no enseñe PII, credenciales o un frontend ficticio. No sumar resultados de tests
de fechas distintas. No presentar fuentes históricas como pruebas nuevas.

# Cierre documental — HRP-93

**Fecha:** 2026-09-08. **Responsable:** Miguel.
**Código revisado:** `f3a952b`. **Develop remoto comprobado:** `275131a`,
merge de PR #80 con la primera documentación de cierre.

## Decisión y alcance

Miguel ha aceptado el cierre documental del proyecto y autoriza actualizar todos
los documentos sin solicitar otra aprobación para editar. La aceptación comunicada
es 18/19 checks: entrega 5/5, esencial 6/6, medio 3/3, avanzado 3/3 y experto 1/2.
El frontend queda expresamente excluido.

La [matriz canónica](delivery-evidence.md) separa aceptación de evidencia técnica.
No afirma que todos los requisitos literales hayan sido demostrados por una prueba.
Miguel, responsable, autoriza el cambio y realiza el merge sin revisores adicionales.
Esta decisión no cierra Jira por sí sola.

## Qué se entrega

Documentación de la ingesta Kafka/MongoDB, clasificación y correlación exacta,
componentes Redis y SQL, API, observabilidad, operaciones, calidad, decisiones,
specs, historia diaria y fuentes para NotebookLM. [Índice completo](README.md).

El cierre HRP-93 registró históricamente que no existía un worker MongoDB → SQL.
La extensión posterior de HRP-87 incorpora `etl` y `api` en Compose: el worker
procesa RAW pendiente, usa Redis como estado temporal y actualiza PostgreSQL.
La limitación histórica no debe reutilizarse para describir el runtime actual.
No se declara throughput garantizado, identidad real, frontend ni despliegue cloud.

## Resultados conocidos y trabajo realizado ahora

La extensión superó Ruff, formato, mypy y 270 pruebas unitarias; además se validó
el recorrido real en Docker hasta SQL y API. Como referencia histórica, el último
intento de la suite completa registró 246 pasan, 21 fallan,
40 omitidos; 307 tests y 82,91 % de cobertura calculada, umbral 75 %.
El import nativo de confluent-kafka fue bloqueado por Control de aplicaciones en
Windows. No se convierte ese resultado en verde ni se presenta como ejecución nueva.
Ese resultado histórico no se presenta como verde. La evidencia actual combina
controles automáticos y comprobación de runtime; véase la
[auditoría](documentation-audit.md).

## Entrega al equipo

1. [README](../README.md): entrada y límites.
2. [Runbook](07-runbook.md): comandos separados por proceso, sin borrar volúmenes.
3. [Dailies](dailies/README.md): registros originales y reconstrucciones identificadas.
4. [Paquete NotebookLM](presentation-sources/NOTEBOOKLM-PACK.md): narrativa, guion,
   fuentes y cautelas para elaborar la presentación.
5. [Specs](specs/README.md): alcance original y evidencia de integración.

La versión del paquete es 0.1.0; no implica tag. Los cambios de esta revisión son
locales hasta su publicación. El merge de PR #80 no contiene automáticamente
las correcciones posteriores. El estado remoto debe comprobarse tras publicar.

## Riesgos que no se ocultan

Un único worker local sin HA, falta de benchmark, API sin auth,
Redis efímero, resultados locales no verdes y frontend excluido. Son límites
documentados; corregirlos requiere tareas funcionales distintas.
Además, el prefijo de acknowledgement es por lote, sin control de huecos entre lotes,
y el consumer interpola excepciones sin redacción universal. No se promete ausencia
global de pérdida ni seguridad de todo mensaje de log.
El generador educativo no se ha inspeccionado y no es una fuente de contrato.

## Reversión documental

Usar un revert del commit correspondiente, tras identificarlo con `git log`; no
resetear ramas ni borrar trabajo ajeno. La extensión añade servicios, código e
índice técnico MongoDB, pero no elimina datos ni incorpora frontend.

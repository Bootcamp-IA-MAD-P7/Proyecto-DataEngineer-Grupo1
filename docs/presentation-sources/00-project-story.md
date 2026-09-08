# Historia del proyecto — fuente ejecutiva

Corte: 2026-09-08. Proyecto educativo HR Pro, equipo Miguel, Anahí, Gaby y Johans.

## Problema y valor

Una persona no llega como un registro completo: llegan fragmentos personales,
de ubicación, profesionales, bancarios y de red. El reto es conservar su origen,
relacionarlos sin inventar identidad y hacer consultable la información resultante.
El valor demostrable es la trazabilidad y la separación de responsabilidades,
no una promesa de identidad perfecta ni una cifra de rendimiento no medida.

## Decisiones que construyen la historia

Primero observar el broker sin inspeccionar el generador. Después conservar raw
antes de interpretar, distinguir evento de persona y aprobar correlaciones exactas
con sus límites. Por último proporcionar almacenamiento curado, consultas y
visibilidad sobre ingesta. Specs y PRs documentan decisiones y cambios.

## Reparto

Miguel coordina plataforma, documentación y calidad; Anahí ingesta y MongoDB;
Gaby contrato, transformación, Redis y observabilidad; Johans PostgreSQL y API.
El trabajo por áreas no demuestra que cada persona validase todos los resultados.

## Resultado y límites

Aceptación comunicada por Miguel: 18/19 checks; frontend excluido.
Hay componentes de ingesta, transformación, Redis, SQL, API y monitorización.
El proceso app no orquesta continuamente toda la ruta hasta SQL.
Las fuentes permiten preparar una presentación; no acreditan un deck ya generado
ni una demo realizada durante esta revisión.

Fuentes: [cierre](../project-closeout.md), [matriz](../delivery-evidence.md),
[cronología](03-delivery-timeline.md) y [paquete completo](NOTEBOOKLM-PACK.md).

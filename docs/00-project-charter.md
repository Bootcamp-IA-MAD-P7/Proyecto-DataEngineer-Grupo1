# Project charter

## Problema y objetivo

Integrar fragmentos de información de RR. HH. recibidos desde Kafka, conservar su
procedencia y producir datos curados consultables. La propuesta combina raw MongoDB,
transformación, PostgreSQL, estado temporal Redis, API y observabilidad.

## Alcance de cierre — 2026-09-08

Miguel, responsable, acepta condiciones de entrega 5/5, esencial 6/6, medio 3/3,
avanzado 3/3 y experto 1/2. Frontend excluido. Esta es una decisión de aceptación;
la [matriz técnica](delivery-evidence.md) registra qué evidencia existe en Git.

La ejecución automática configurada cubre Kafka–MongoDB mediante `app` y el recorrido
MongoDB–Redis–PostgreSQL mediante `etl`; `api` expone las consultas curadas. Kafka
permanece como runtime educativo externo y el frontend queda excluido.

## Equipo

| Miembro | Responsabilidad |
|---|---|
| Miguel | Coordinación, plataforma, Git, calidad y documentación |
| Anahí | Kafka y MongoDB |
| Gaby | Contrato, ETL, Redis y monitorización |
| Johans | PostgreSQL y API |

## Restricciones

El productor educativo es una caja negra. Solo se emplean briefing/instrucciones
públicas y observaciones autorizadas; no su código. No publicar secretos ni datos
personales en artefactos de ingeniería o presentación.

## Entrega documental

[README](../README.md), guías operativas, diccionario, contratos, ADRs, specs,
dailies y [paquete NotebookLM](presentation-sources/NOTEBOOKLM-PACK.md).
Miguel autoriza las correcciones documentales sin nueva aprobación. No se infiere
autorización para alterar datos, implementar frontend o modificar estados externos.

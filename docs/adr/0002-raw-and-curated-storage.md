# ADR-0002: Separar datos raw y curados

## Estado

Aceptada.

## Decisión

MongoDB conservará cada evento recibido sin modificar. PostgreSQL almacenará los datos agrupados y mapeados para consultas, con idempotencia técnica según el
contrato del repositorio; no se presupone normalización semántica de negocio.

## Motivo

La separación permite auditoría, depuración y reproceso sin perder el mensaje original, a la vez que mantiene consultas analíticas eficientes en SQL.

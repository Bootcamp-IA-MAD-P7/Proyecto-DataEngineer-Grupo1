# ADR-0002: Separar datos raw y curados

## Estado

Aceptada.

## Decisión

MongoDB conservará cada evento recibido sin modificar. PostgreSQL almacenará los datos agrupados, normalizados e idempotentes para consultas.

## Motivo

La separación permite auditoría, depuración y reproceso sin perder el mensaje original, a la vez que mantiene consultas analíticas eficientes en SQL.


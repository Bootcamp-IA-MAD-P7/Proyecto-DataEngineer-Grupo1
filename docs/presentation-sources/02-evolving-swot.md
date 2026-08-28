# DAFO evolutivo para la presentación

Este resumen está preparado para diapositivas. La fuente técnica canónica es
`docs/09-evolving-swot.md` y debe actualizarse cuando cambie la evidencia.

## Fotografía actual — 2026-08-28

### Fortalezas

- Contrato Kafka derivado de observación real, no del generador.
- SDD, ADRs, CI, revisión humana y trazabilidad Jira desde el inicio.
- Consumer configurable, seguro en logs y validado en ejecución continua.
- Separación explícita entre raw, transformación y datos curados.

### Debilidades

- El pipeline esencial aún no persiste en MongoDB ni publica en PostgreSQL.
- Solo hay 7 tests y todavía no existen pruebas de integración de almacenamiento.
- HRP-43 todavía debe determinar si los candidatos observados aportan evidencia
  suficiente para una correlación segura. La clasificación de HRP-44 y la
  validación/limpieza de HRP-45 también siguen pendientes de aprobación.
- Parte del trabajo previo llegó en PRs con más de una historia y generó conflictos.

### Oportunidades

- Convertir la persistencia raw en el primer corte vertical demostrable.
- Elevar gradualmente la cobertura y añadir contrato, integración y E2E.
- Usar las fuentes versionadas para generar presentación y relato de evolución.
- Introducir métricas después de que exista un flujo esencial estable.

### Amenazas

- Pérdida de mensajes si se confirma Kafka antes de guardar raw.
- Corrupción lógica si se clasifica o correlaciona por intuición.
- Sobrearquitectura si Redis, Airflow, API o frontend se adelantan al MVP esencial.
- Diferencias entre documentación y código si se anuncian capacidades no demostradas.

## Evolución que queremos mostrar

| Momento | Debilidad que se reduce | Evidencia esperada |
|---|---|---|
| Próximo hito | Sin persistencia raw | Kafka -> MongoDB con idempotencia |
| Nivel esencial | Sin perfil curado | Persona agrupada y persistida en PostgreSQL |
| Nivel medio | Operación manual | Stack Docker, logs y tests de integración |
| Nivel avanzado | Sin visibilidad de rendimiento | Redis, Prometheus y API medidos |
| Nivel experto | Sin experiencia de consulta | Pipeline continuo y frontend demostrable |

# DAFO evolutivo para la presentación

Este resumen está preparado para diapositivas. La fuente técnica canónica es
`docs/09-evolving-swot.md` y debe actualizarse cuando cambie la evidencia.

## Fotografía actual — 2026-08-31

### Fortalezas

- Contrato Kafka derivado de observación real, no del generador.
- SDD, ADRs, CI, revisión humana y trazabilidad Jira desde el inicio.
- Consumer configurable, seguro en logs, con MongoDB inicial y duplicados técnicos
  controlados.
- Separación explícita entre raw, transformación y datos curados.

### Debilidades

- El pipeline esencial aún no agrupa personas ni publica en PostgreSQL.
- Hay 17 tests, pero todavía faltan pruebas de integración E2E del flujo completo.
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

- Pérdida de trazabilidad si el sobre raw mezcla metadatos Kafka y clasificación.
- Corrupción lógica si se clasifica o correlaciona por intuición.
- Sobrearquitectura si Redis, Airflow, API o frontend se adelantan al MVP esencial.
- Diferencias entre documentación y código si se anuncian capacidades no demostradas.

## Evolución que queremos mostrar

| Momento | Debilidad que se reduce | Evidencia esperada |
|---|---|---|
| Próximo hito | Raw aún no usado por ETL | Sobre raw alineado y preparado para transformación |
| Nivel esencial | Sin perfil curado | Persona agrupada y persistida en PostgreSQL |
| Nivel medio | Operación manual | Stack Docker, logs y tests de integración |
| Nivel avanzado | Sin visibilidad de rendimiento | Redis, Prometheus y API medidos |
| Nivel experto | Sin experiencia de consulta | Pipeline continuo y frontend demostrable |

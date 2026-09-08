# DAFO evolutivo para la presentación

Este resumen está preparado para diapositivas. La fuente técnica canónica es
`docs/09-evolving-swot.md` y debe actualizarse cuando cambie la evidencia.

## Fotografía de cierre — 2026-09-08

### Fortalezas

- Contrato Kafka derivado de observación real, no del generador.
- SDD, ADRs, CI, revisión humana y trazabilidad Jira desde el inicio.
- Consumer configurable, seguro en logs, con MongoDB raw, duplicados técnicos
  controlados y persistencia trazable.
- Separación explícita entre raw, transformación y datos curados.
- Redis, PostgreSQL, API, métricas, Prometheus, Grafana y Docker Compose versionados.

### Debilidades

- La validación E2E y de carga depende del entorno disponible para el release.
- El frontend queda fuera del cierre.
- La ejecución local en Windows está afectada por el bloqueo de la extensión nativa de
  `confluent-kafka`; se documenta como caveat de entorno.

### Oportunidades

- Ejecutar validación prolongada y de carga en un entorno Linux/CI preparado.
- Usar las fuentes versionadas para generar presentación y relato de evolución.
- Implementar el frontend como una futura tarea independiente.

### Amenazas

- Pérdida de trazabilidad si el sobre raw mezcla metadatos Kafka y clasificación.
- Corrupción lógica si se clasifica o correlaciona por intuición.
- Sobrearquitectura si Redis, Airflow, API o frontend se adelantan al MVP esencial.
- Diferencias entre documentación y código si se anuncian capacidades no demostradas.

## Evolución que queremos mostrar

| Momento | Debilidad que se reduce | Evidencia esperada |
|---|---|---|
| Fundaciones | Contrato y gobernanza iniciales | Observación Kafka, SDD, CI y raw storage |
| Nivel esencial | Fragmentos dispersos | Agrupación, consolidación y PostgreSQL |
| Nivel medio | Operación sin señales | Docker, logs y quality gates |
| Nivel avanzado | Sin visibilidad de rendimiento | Redis, Prometheus, Grafana y API |
| Nivel experto | Producto incompleto | Frontend explícitamente fuera de alcance |

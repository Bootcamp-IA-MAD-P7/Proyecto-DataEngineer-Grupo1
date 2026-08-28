# Evidencia — Contrato Kafka y línea base de calidad

**Fecha:** 2026-08-28  
**Alcance:** transición de descubrimiento a persistencia raw  
**Estado:** evidencia integrada para Kafka y consumer; persistencia raw pendiente

## Qué puede demostrarse

| Evidencia | Resultado | Límite |
|---|---|---|
| PR #12 / HRP-24 | Contrato inicial basado en cinco variantes observadas | No aprueba semántica ni correlación final |
| PR #14 / HRP-31 | Consumer continuo validado contra Kafka autorizado | No demuestra persistencia ni ETL |
| Suite local | 7 tests, 79 % de cobertura de línea | No incluye aún integración MongoDB |
| Compose de desarrollo | MongoDB local reproducible y aislado | Disponibilidad no equivale a persistencia correcta |
| PR #15 | Quality gate, ADR, benchmark, DAFO, daily y README renovado | Pendiente de aprobación y merge |

## Evolución de arquitectura

Se propone formalmente que la confirmación Kafka ocurra después de persistir raw. El
documento debe conservar payload original y metadatos técnicos, con índice único por
`topic + partition + offset`. La propuesta queda registrada en ADR-0005 y debe ser
implementada y revisada en las historias de persistencia.

## Aprendizaje comparativo

Se estudió otro proyecto educativo completo para identificar patrones, no para copiar
código. Se adopta la idea de pruebas de integración, métricas de flujo y una demo
orientada al recorrido del dato. Se descartan sus riesgos de dependencias duplicadas,
ausencia de CI visible, confirmación insegura de Kafka y mezcla de responsabilidades.

## Material seguro para presentación

- Diagrama del límite `Kafka -> MongoDB raw -> confirmación`.
- Matriz de niveles del briefing y estado real.
- Tendencia del DAFO y del nivel de madurez.
- Checks de CI y resultados agregados de tests.

No incluir payloads, valores de campos, secretos, `.env` ni código del generador.

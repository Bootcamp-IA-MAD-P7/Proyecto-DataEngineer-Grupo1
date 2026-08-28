# Daily — 2026-08-28

## Objetivo de la jornada

Consolidar el cierre del descubrimiento Kafka, mantener separados los límites entre
ingesta, transformación y persistencia, y preparar el siguiente corte vertical del
nivel esencial: `Kafka -> MongoDB raw`.

## Estado verificado al comenzar

- HRP-24 está integrada en `develop` mediante la PR #12: existe un contrato inicial
  basado en evidencia y las incógnitas siguen declaradas como tales.
- HRP-31 está integrada en `develop` mediante la PR #14: el consumer continuo fue
  validado contra el runtime Kafka autorizado.
- El entorno MongoDB local de HRP-33 está disponible mediante Compose.
- La persistencia raw, la agrupación ETL y PostgreSQL todavía no forman un pipeline
  funcional completo.

## Reparto equilibrado y real

El reparto equilibra responsabilidad y dependencia; no atribuye como terminado lo que
solo está iniciado.

### Miguel — plataforma, calidad y documentación

- Cerró la trazabilidad de HRP-31 tras revisión y merge de la PR #14.
- Comparó la arquitectura con un proyecto educativo de referencia para extraer patrones
  reutilizables sin copiar código ni convertirlo en dependencia.
- Preparó un umbral inicial de cobertura, validación de Compose en CI, ADR de
  confirmación Kafka y persistencia raw, DAFO evolutivo y renovación del README.
- Abrió la PR #15 de HRP-22 con los checks en verde y solicitó revisión humana a Gaby.
- Siguiente paso: revisar observaciones, integrar cuando exista aprobación y mantener
  HRP-22 abierta como responsabilidad continua de tablero y documentación.

### Anahí — ingesta y almacenamiento raw

- HRP-30 y HRP-31 están terminadas: existe un consumer configurable, con logs
  exclusivamente técnicos, cierre limpio y validación real de ejecución continua.
- HRP-34 está en curso y dispone ahora de un contrato técnico más claro para guardar
  payload y metadatos Kafka sin confirmar offsets antes de tiempo.
- Su PR de trabajo acumulado permanece separada y no se altera desde esta tarea.
- Siguiente paso: implementar el repositorio raw mínimo y demostrar idempotencia.

### Gaby — contrato y transformación

- HRP-24 está terminada y versionada con cinco variantes estructurales neutrales,
  campos observados y límites explícitos de la evidencia.
- Revisó el límite de HRP-31 para evitar que ingesta invada transformación o ETL.
- HRP-43 está en curso: debe convertir evidencia en una decisión de clasificación
  revisable, sin usar coincidencias parciales ambiguas como regla de negocio.
- Siguiente paso: proponer clasificación y casos de prueba a partir del contrato
  aprobado, manteniendo la correlación como incógnita si no hay evidencia suficiente.

### Johans — modelo relacional y capa de consulta

- HRP-25 está en curso sobre el contrato ya aprobado, por lo que puede separar el
  sobre raw del futuro modelo curado sin depender de nombres inventados.
- Debe contemplar que `salary` fue observado como string y que no existe aún una clave
  final de correlación de personas.
- Siguiente paso: presentar modelo lógico, restricciones, índices y decisiones
  pendientes para revisión de Gaby y Miguel.

## Decisiones de hoy

1. Kafka solo podrá confirmar un mensaje cuando MongoDB haya insertado el raw o
   demuestre que esas coordenadas ya existían.
2. El mínimo raw conserva `payload`, `topic`, `partition`, `offset`, `received_at` y
   un estado técnico; no renombra campos ni añade semántica de negocio.
3. La cobertura empieza con un suelo del 75 % y evolucionará al alza. No sustituye
   pruebas de contrato, integración o comportamiento.
4. El proyecto externo comparado queda documentado como referencia de aprendizaje,
   nunca como fuente del contrato, dependencia o código a copiar.
5. Redis, API, frontend y orquestación siguen fuera del corte actual hasta completar
   el flujo esencial.

## Riesgos y bloqueos

| Riesgo | Impacto | Responsable | Próxima acción |
|---|---|---|---|
| Confirmar Kafka antes de persistir | Pérdida silenciosa de eventos | Miguel + Anahí | Aplicar ADR-0005 en HRP-34/35/36 |
| Clasificar por coincidencia parcial | Mezcla incorrecta de fragmentos | Gaby | Definir reglas exactas y tests en HRP-43 |
| Diseñar SQL con correlación supuesta | Modelo curado difícil de corregir | Johans | Marcar clave final como pendiente en HRP-25 |
| PRs demasiado amplias | Conflictos y revisiones bloqueantes | Todo el equipo | Una historia y un objetivo principal por PR |
| Documentación adelantada al código | Presentación no demostrable | Miguel | Mantener matriz de capacidad y DAFO con evidencia |

## Indicadores de cierre de la jornada

| Indicador | Estado |
|---|---|
| Contrato observado revisado | Completado |
| Consumer configurable y continuo | Completado |
| MongoDB local reproducible | Completado |
| Persistencia raw integrada | Pendiente |
| Tests automatizados actuales | 7 |
| Cobertura de línea medida | 79 % |
| Umbral mínimo propuesto | 75 % |
| Pipeline esencial completo | Pendiente |

## Próxima sincronización

- Anahí presenta el cambio mínimo de HRP-34 con idempotencia y resultado de persistencia.
- Gaby presenta la propuesta de clasificación de HRP-43 con pruebas de casos ambiguos.
- Johans presenta el modelo lógico de HRP-25 y sus decisiones pendientes.
- Miguel revisa que los tres cambios respeten contrato, ADRs, checks y trazabilidad Jira.

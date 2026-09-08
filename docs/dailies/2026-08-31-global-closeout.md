# Daily — 2026-08-31 — Persistencia inicial e infraestructura

## Naturaleza del registro

Registro original conservado abajo, acompañado de una reconciliación retrospectiva del historial.
La fecha es la de integración en develop; puede diferir de la fecha de autoría.
No se atribuyen conversaciones, aprobaciones personales ni bloqueos sin evidencia.

## Resultado de la jornada

Modelo SQL, configuración, Dockerfile, logging y CI; MongoIngestionClient. Al final de la jornada se integran PostgreSQL local (PR #31) y esquema SQL (PR #32).

## Evidencia integrada

| Commit | Integración registrada |
|---|---|
| [9eef089](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/9eef089) | HRP-54 feat: create tables, primary keys, foreign keys and indexes (#32) |
| [58b6bbc](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/58b6bbc) | HRP-53 feat: create PostgreSQL via Docker (#31) |
| [a0d085d](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/a0d085d) | Merge pull request #30 from Bootcamp-IA-MAD-P7/docs/HRP-22-project-closeout-2026-08-31 |
| [0942230](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/0942230) | HRP-34 feat: integrate detect_topic and validate into consumer batch loop (#29) |
| [9373626](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/9373626) | HRP-33 feat: add MongoIngestionClient (#27) |
| [cb2855a](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/cb2855a) | HRP-52 docs: design PostgreSQL tables and relationships |
| [c6e325c](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/c6e325c) | Merge pull request #21 from Bootcamp-IA-MAD-P7/feature/HRP-62-application-dockerfile |
| [e9e379f](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/e9e379f) | Merge pull request #20 from Bootcamp-IA-MAD-P7/feature/HRP-64-environment-configuration |
| [71aa78d](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/71aa78d) | HRP-72 docs: record CI evidence (#24) |
| [cdefded](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/cdefded) | HRP-65 chore: add safe Kafka consumer logging (#23) |
| [0ec4fef](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/0ec4fef) | HRP-94 docs: define accessibility and sustainability policy (#26) |
| [a33c5fd](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/a33c5fd) | Merge pull request #22 from Bootcamp-IA-MAD-P7/feature/HRP-72-ci-test-automation |
| [ba774b8](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/ba774b8) | Merge pull request #19 from Bootcamp-IA-MAD-P7/docs/HRP-25-english-data-model |
| [d3986a2](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/commit/d3986a2) | Merge pull request #18 from Bootcamp-IA-MAD-P7/feature/HRP-25-modelo-datos |

## Límites y decisiones

El registro original era un corte intradía: sus frases «PostgreSQL pendiente» no representan el final de la jornada. La frontera raw inicial HRP-34 se corrige después en PR #33.

## Continuidad

Consultar la [siguiente jornada disponible y el índice](README.md).
Las tareas y estados actuales de Jira no se han consultado en esta revisión.
El historial acredita commits, no asistencia a una daily ni validación de cada criterio.


## Registro original de la jornada (histórico)

Las afirmaciones de estado que siguen pertenecen al momento original, no al cierre.

### Daily — 2026-08-31

## Trabajo realizado hasta ahora

El proyecto ya tiene una base profesional: repositorio en GitHub, rama `develop`,
reglas de PR, CODEOWNERS, CI, specs por tarea, ADRs, documentación viva y tablero
Jira. La forma de trabajo queda fijada como:

```text
Jira -> spec -> rama -> cambio mínimo -> validación -> PR -> revisión humana -> merge -> evidencia Jira
```

También se completó la observación segura de Kafka sin leer el generador educativo.
De esa observación nació el contrato inicial: un único topic observado, `probando`,
cinco estructuras de mensaje, diferencias reales frente al briefing y campos que
siguen sin semántica aprobada.

## Estado actual

`develop` está en verde tras la fusión de las PRs recientes de ingesta, MongoDB,
validación inicial, modelo PostgreSQL, CI, Dockerfile, configuración, logging,
accesibilidad y sostenibilidad.

La evidencia actual de CI en `develop` es:

| Indicador | Estado |
|---|---|
| Último commit revisado | `0942230` |
| Tests | 17 passed |
| Cobertura | 80.10 % |
| Umbral mínimo | 75 % |
| Specs | 16 validadas |
| Ruff / format / mypy | Pasan en GitHub Actions |
| Compose dev | Configuración validada |

La parte de Anahí deja ya una ingesta inicial Kafka -> consumer -> MongoDB con control
de errores, índices y duplicados técnicos. La parte de Johans deja el modelo de datos
SQL diseñado y revisado en inglés. La parte de Gaby deja el contrato observado y tiene
abiertas las siguientes piezas de transformación: correlación, clasificación y limpieza.

## Qué estamos haciendo

El equipo está entrando en el corte en el que hay que convertir la ingesta inicial en
un pipeline esencial demostrable. La prioridad inmediata es no perder la trazabilidad:
MongoDB debe conservar claramente payload original, topic Kafka, partición, offset,
fecha de recepción, estado técnico y cualquier clasificación como resultado derivado,
no como sustituto de metadatos Kafka.

En paralelo, Gaby puede avanzar HRP-43, HRP-44 y HRP-45. La secuencia correcta es:

| Tarea | Sentido |
|---|---|
| HRP-43 | Analizar candidatos de correlación y decidir si hay evidencia suficiente |
| HRP-44 | Clasificar las variantes con reglas explícitas y tests |
| HRP-45 | Definir validación y limpieza, por ejemplo `salary` y `sex` |

Johans puede seguir con PostgreSQL a partir del diseño aprobado, pero sin fijar una
clave única de persona hasta que HRP-43 lo permita.

## Qué nos bloquea

No hay PRs abiertas bloqueando `develop` en este momento. El bloqueo real es de
producto: todavía no existe el recorrido completo Kafka -> MongoDB -> ETL ->
PostgreSQL -> consulta.

Los riesgos actuales son:

| Riesgo | Efecto | Acción |
|---|---|---|
| Mezclar topic Kafka con tipo de fragmento | Se pierde trazabilidad raw | Revisar sobre raw antes de ETL |
| Correlacionar por intuición | Se pueden mezclar personas distintas | HRP-43 debe basarse en evidencia |
| Clasificar por coincidencias parciales | Fragmentos mal asignados | HRP-44 debe tener reglas exactas |
| Documentar objetivo como si fuera realidad | Demo poco defendible | README y daily distinguen completado/en curso/pendiente |

## Próximos pasos

1. Revisar el sobre raw que consume el ETL y separar metadatos Kafka de clasificación.
2. Avanzar HRP-43 con evidencia, no con una regla asumida.
3. Resolver HRP-44 y HRP-45 con fixtures sintéticos seguros.
4. Implementar PostgreSQL local y tablas cuando el diseño esté listo para ejecución.
5. Preparar una demo corta de lo que ya existe y otra del flujo completo cuando esté.

## Aprendizajes del equipo

La metodología está funcionando porque los tests y CI han detectado problemas reales:
imports, formato, tipos, cobertura y alcance de PRs. Esto a veces ralentiza, pero evita
que el proyecto avance con errores invisibles. La mejora para los próximos días es
mantener PRs pequeñas y que cada historia cierre una cosa concreta, con su evidencia.

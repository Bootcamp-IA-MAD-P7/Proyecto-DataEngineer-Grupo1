# HR Pro — paquete autocontenido de cierre para NotebookLM

**Corte:** 2026-09-08. **Equipo:** Miguel, Anahí, Gaby y Johans.
**Código:** f3a952b. **Primera documentación integrada:** 275131a / PR #80.
**Propósito:** generar una presentación técnica defendible de 12 diapositivas,
aproximadamente 12 minutos, para evaluación del proyecto educativo.
Este archivo aporta el contenido; no presupone que se lean sus enlaces.

## 1. Resumen ejecutivo

HR Pro recibe información de RR. HH. fragmentada en cinco dominios: Personal,
Location, Professional, Bank y Net. El proyecto conserva el dato original y su
procedencia, define correlaciones operacionales explícitas y proporciona componentes
para construir información curada y consultarla. Su valor es hacer trazable el
recorrido y visible la incertidumbre, no prometer identidad perfecta.

Miguel coordina plataforma, Git, calidad y documentación; Anahí ingesta Kafka y
MongoDB; Gaby contrato, transformación, Redis y observabilidad; Johans PostgreSQL
y API. Gaby y Johans fueron designados revisores de PR: no se afirma aquí que hayan
emitido una aprobación. Miguel autoriza el cierre documental.

## 2. Resultado aceptado frente a evidencia

| Bloque | Aceptados | Total | Porcentaje de aceptación |
|---|---:|---:|---:|
| Condiciones de entrega | 5 | 5 | 100 |
| Esencial | 6 | 6 | 100 |
| Medio | 3 | 3 | 100 |
| Avanzado | 3 | 3 | 100 |
| Experto | 1 | 2 | 50 |

Son **18 checks aceptados de 19**, según la decisión comunicada por el responsable.
El restante es el frontend, excluido del cierre. No son porcentajes de tests
pasados ni una certificación independiente del enunciado completo.

Entrega abarca GitHub documentado, programa Dockerizado, demo, presentación y Kanban.
Esencial abarca consumer, raw MongoDB, agrupación de cinco dominios, SQL y prácticas
Git/documentación. Medio: logs, unit tests y Compose. Avanzado: Redis, monitorización
y API. Experto: continuidad de actualización y frontend.

Límites que deben acompañar la aceptación: no hay benchmark que acredite miles de
mensajes/segundo; esta revisión no aporta grabación de demo ni deck terminado.
Tampoco hay worker productivo integrado que actualice automáticamente SQL desde
MongoDB. La aceptación del requisito de continuidad no demuestra por sí sola
continuidad SQL. Estos límites son independientes del problema Windows de tests.

## 3. Arquitectura: qué se conecta realmente

El contenedor app ejecuta el proceso Python de ingesta continua:

Kafka externo → app de ingesta → MongoDB raw/invalid_events.

El mismo proceso emite métricas de ingesta que consulta Prometheus y visualiza
Grafana. Kafka no forma parte del Compose del equipo.

Por otra parte, hay funciones de clasificación, validación, agrupación y consolidación,
adapter Redis de estado parcial, mapper y repositorio SQL. La prueba HRP-71 conecta
MongoDB → transformación → PostgreSQL explícitamente con eventos sintéticos equivalentes
a Kafka. No ejecuta un broker Kafka ni integra Redis en ese recorrido.

La API FastAPI consulta PostgreSQL y se inicia como proceso separado. El comando
storage.main crea el esquema y termina; no es un worker ETL.
Compose incluye app, mongo, postgres, redis, prometheus y grafana. No incluye API
ni frontend. Una API saludable puede consultar una base vacía.

Visual: separar en dos bandas «ingesta continua» y «componentes/prueba sintética»;
dibujar discontinuas las conexiones no orquestadas por el proceso productivo.
No presentar el objetivo original de arquitectura como runtime entregado completo.

## 4. Dato original, clasificación y calidad

El contrato inicial HRP-29 registra una muestra de 20 objetos JSON en una partición,
cinco estructuras, sin errores técnicos observados. Es una muestra acotada, no
una garantía global. No se inspeccionó el generador educativo ni se versionan payloads.

Cada documento raw conserva payload, topic, partition, offset, received_at y
processing_status. Los errores técnicos se separan como missing_value, invalid_utf8,
invalid_json o non_object_json. Un objeto desconocido se conserva antes de clasificar.

Identidad del evento: topic + partition + offset. El índice compuesto y la política
de acknowledgement tras persistencia sirven a la idempotencia técnica. Se confirma
el prefijo durable de cada lote por partición. El código no mantiene huecos sin
persistir entre lotes: un commit posterior puede sobrepasarlos. No afirmar una
garantía global de no pérdida a partir de esa protección local.
No se afirma exactly-once extremo a extremo ni deduplicación universal de personas.

El clasificador reconoce conjuntos exactos de claves:

| Dominio | Claves |
|---|---|
| Personal | name, last_name, sex, telfnumber, passport, email |
| Location | fullname, city, address |
| Professional | fullname, company, company address, company_telfnumber, company_email, job |
| Bank | passport, IBAN, salary |
| Net | address, IPv4 |

El clasificador no valida tipos/valores de negocio. Campos extra/ausentes producen
unknown. HRP-45 valida coherencia técnica, no normaliza formatos ni limpia salarios.
No confundir tipos aparentes de la observación inicial con reglas implementadas.

## 5. Correlación con incertidumbre explícita

ADR-0006, integrado por PR #42 el 2026-09-02, autoriza cuatro relaciones exactas:

1. Personal.passport = Bank.passport.
2. Personal.name + espacio + Personal.last_name = Location.fullname.
3. Location.fullname = Professional.fullname.
4. Location.address = Net.address.

La correlación puede ser transitiva. No aplica trim, normalización de mayúsculas,
acentos, fuzzy matching ni una clave alternativa escondida.
Los resultados conservan complete, incomplete o ambiguous y entradas no resueltas,
con procedencia y reglas utilizadas. La misma carga con distintas referencias de
origen no se elimina automáticamente como duplicado exacto.

La observación autorizada HRP-43 analizó 2.000 raw. La evidencia incorporada a ADR-0006
registra 397 candidatos Personal/Bank, 399 Location/Professional, 400 Location/Net,
251 puentes derivados Personal/Location y249 componentes con cinco dominios.
**No sumar esas cifras como personas únicas**: describen relaciones y componentes
solapados, no un censo ni ground truth de identidad. No observar colisiones en
esa muestra no garantiza ausencia de colisiones futuras.

## 6. Persistencia y estado temporal

MongoDB conserva evidencia; Redis guarda fragmentos temporales; PostgreSQL da salida
relacional. Redis utiliza Sets con JSON determinista y claves opacas, prefijo hrp:partial:.
El TTL por defecto es 3600 segundos, configurable por un entero positivo.
Guardar incluso un duplicado renueva el TTL; leer no. SADD y EXPIRE son llamadas
separadas, no operación atómica. Redis es efímero, no único sistema de registro.

SQL contiene employees, locations, professional_profiles, bank_accounts, network_data
y processing_audit. Las tablas de dominio enlazan employee_id con employees.
El audit puede conservarse con employee_id nulo tras borrado del padre.
La idempotencia por raw_event_ref es técnica; passport e IBAN no son claves de negocio
declaradas únicas. salary e IP son texto y sex es JSONB.
Crear esquema de forma idempotente no equivale a disponer de migraciones versionadas.

## 7. Consultas y protección del dato

FastAPI ofrece:

- GET /health: SELECT 1 contra SQL; error de dependencia503.
- GET /people/search: filtro por id, passport, first_name o last_name.
- GET /people/search/by-location-profession: city, address, job o company.
- GET /statistics: conteos de las seis tablas y faltantes de cuatro dominios.

Las búsquedas requieren al menos un filtro; varios filtros se combinan con AND y
comparación exacta. limit20 por defecto, máximo100, offset no negativo; orden por id.
Sin coincidencias se devuelve lista vacía. Validaciones manuales pueden devolver400
y tipos inválidos422; una dependencia SQL no disponible puede responder503 antes.
Las búsquedas no devuelven IBAN/salario, pero sí pueden devolver PII como pasaporte,
contacto o ubicación. No hay autenticación/autorización: uso local controlado.
Las estadísticas son agregadas; no enseñar registros personales en las slides.

## 8. Observabilidad sin métricas inventadas

Tres familias de métricas propias:

- hr_pro_platform_ingestion_messages_consumed_total.
- hr_pro_platform_ingestion_processing_duration_seconds.
- hr_pro_platform_ingestion_persistence_duration_seconds.

La persistencia medida es MongoDB, no SQL. Un rate del contador representa consumo
por segundo; su existencia no prueba miles de mensajes/segundo sostenidos.
Los histogramas exponen +Inf, sum y count: permiten duración media por ventana,
pero no percentiles p95/p99 significativos con buckets finitos inexistentes.
No se han implementado aquí métricas equivalentes de API, Redis, SQL, lag o errores.

Prometheus scrapea app:9464; interfaz local 9090. Grafana local 3000 aprovisiona el
dashboard HR Pro Ingestion Overview con lectura anónima de desarrollo.
Los logs son técnicos; mensajes JSON de helpers ETL no implican que todo el flujo
de logging sea JSON. LOG_LEVEL en la plantilla no controla el logger INFO actual.
No se promete un filtro global de redacción que no esté implementado. El consumer
interpola excepciones genéricas; revisar logs antes de compartirlos por posible
contenido sensible en mensajes externos.

## 9. Calidad y reproducibilidad

Último intento local reportado en esta conversación sobre el código revisado:

| Resultado | Cantidad |
|---|---:|
| Pasan | 246 |
| Fallan | 21 |
| Omitidos | 40 |
| Total | 307 |

Cobertura calculada 82,91 %, umbral75 %. No llamar «100 % de éxito» a esta ejecución.
Windows bloqueó la extensión nativa de confluent-kafka por Control de aplicaciones;
el import aislado lo evidenció. Errores posteriores de mocks no demuestran21 bugs
independientes. Esto tampoco demuestra que todos los tests fallidos pasarían en Linux.
Omisiones por bases de integración no disponibles y Redis sin configurar.

CI versiona validación de specs, pre-commit, Ruff, mypy, pytest y sintaxis de Compose,
con MongoDB y PostgreSQL; no añade broker Kafka ni Redis.
En esta revisión documental no se repitió la suite, no se aporta log completo del
intento anterior ni se consultó el resultado actual de todos los checks remotos.

La configuración Compose usa Mongo 7.0, PostgreSQL 16, Redis 7.2, Prometheus v2.55.1 y
Grafana 11.3.0; Dockerfile usa Python3.11-slim. Son referencias del checkout, no
recomendaciones de versiones más recientes. restart:unless-stopped no garantiza HA.

## 10. Evolución por jornadas

### 2026-08-27: Fundación y primeras integraciones

SDD, guías de equipo, consumer y entorno MongoDB. La PR #2 incorporó una plantilla; por sí sola no acredita la observación real de Kafka.

Límite: Las notas originales conservan los resultados locales reportados en su fecha; no se reejecutaron en septiembre.

### 2026-08-28: Contrato y consumo continuo

Integración HRP-24 y HRP-31; el contrato conserva las cinco formas observadas sin deducir identidad. README, DAFO y gobierno de la evidencia evolucionan.

Límite: No se había demostrado un pipeline completo hasta SQL ni rendimiento de miles de mensajes por segundo.

### 2026-08-31: Persistencia inicial e infraestructura

Modelo SQL, configuración, Dockerfile, logging y CI; MongoIngestionClient. Al final de la jornada se integran PostgreSQL local (PR #31) y esquema SQL (PR #32).

Límite: El registro original era un corte intradía: sus frases «PostgreSQL pendiente» no representan el final de la jornada. La frontera raw inicial HRP-34 se corrige después en PR #33.

### 2026-09-01: Frontera raw y clasificación

HRP-34 corrige raw antes de clasificar. HRP-43 analiza 2.000 eventos autorizados. HRP-44 incorpora clasificación por conjuntos exactos de claves.

Límite: La observación no demuestra identidad real. La decisión operacional global ADR-0006 se integra al día siguiente, no se retrodata.

### 2026-09-02: Validación técnica y consolidación

HRP-45 añade validación técnica; groupers de cinco dominios, ADR-0006 PR #42, consolidación HRP-50, endurecimiento HRP-96 y resiliencia inicial HRP-51.

Límite: Correlación exacta y transitiva, sin fuzzy matching; coincidencia no prueba identidad. Las evidencias finales HRP-51 se integran el 3 de septiembre.

### 2026-09-03: Persistencia SQL y pruebas

Conexión, inserción, actualización e idempotencia por referencia de origen; consultas de validación SQL y pruebas ETL. Evidencia final HRP-51.

Límite: No confundir acceso/repositorio SQL con API HTTP: la API se integra el día 4. La existencia de pruebas no acredita una ejecución nueva.

### 2026-09-04: API, Redis e integración sintética

Compose de app y bases; logs ETL/SQL, CI con PostgreSQL, tests consumer, adapter Redis y endpoints FastAPI, incluidas estadísticas.

Límite: HRP-71 conecta MongoDB, transformación y PostgreSQL con eventos sintéticos equivalentes a Kafka; no broker real ni Redis. El TTL configurable se incorpora el día 7.

### 2026-09-07: TTL y observabilidad de ingesta

TTL Redis, contador de consumo y duraciones de procesamiento/persistencia MongoDB; endpoint Prometheus, scraper y dashboard Grafana. HRP-87/88 documentan ingesta continua y reinicios.

Límite: No hay worker productivo continuo hasta SQL, métricas SQL/Redis/API ni benchmark. Los histogramas tienen solo bucket +Inf; no ofrecen p95/p99 útiles.

### 2026-09-08: Cierre y reconciliación documental

PR #80 integra la primera documentación. La revisión posterior reconcilia README, contrato, runtime, specs, dailies y fuentes NotebookLM con el código; mantiene 18/19 aceptados y frontend excluido.

Límite: Resultados locales anteriores: 246 pasan, 21 fallan, 40 omitidos, cobertura 82,91 %. No son una suite verde ni una prueba ejecutada en esta revisión.


Fechas basadas en integraciones Git; las reconstrucciones no son actas de reuniones.
Sin integraciones observadas29–30 de agosto y5–6 de septiembre; no implica ausencia
de trabajo. Las dailies originales27/28/31 se conservan con alcance histórico.

## 11. DAFO y siguientes pasos

Fortalezas: procedencia preservada, separación raw/temporal/curado, reglas explícitas,
pruebas y decisiones trazables.
Debilidades: orquestación productiva completa ausente, resultados locales no verdes,
API sin auth, falta de benchmark y frontend excluido.
Oportunidades: conectar componentes, medir carga/recovery en entorno autorizado,
añadir auth y una interfaz sobre la API.
Amenazas: colisiones de claves aparentes, cambios de formatos, dependencia del broker,
pérdida de estado temporal y documentación que exagere lo realizado.

Siguiente trabajo funcional posible, no realizado en este cierre: worker Mongo→ETL→SQL,
prueba con broker real, mediciones de carga, auth, telemetría ampliada y frontend.
No asignar fechas/promesas ni abrir tareas automáticamente.

## 12. Guion de 12 diapositivas y notas del orador

| Nº / tiempo | Título-mensaje | Visual y evidencia | Nota del orador |
|---|---|---|---|
| 1 / 0:40 | De fragmentos a información trazable | Cinco tarjetas de dominio; P1/P9 | El problema es relacionar fragmentos manteniendo origen e incertidumbre. |
| 2 / 0:50 | Alcance aceptado, límites visibles | Barras de aceptación 5/5, 6/6, 3/3, 3/3, 1/2; P7 | La aceptación del responsable no es un benchmark; frontend excluido. |
| 3 / 1:15 | Arquitectura real, no arquitectura prometida | Dos bandas runtime/componentes; P1/R7 | App ingiere; SQL necesita orquestación fuera del proceso principal; API separada. |
| 4 / 1:00 | Conservar antes de interpretar | Envelope sin valores y secuencia persistir→ack; P2/P9/R1/R2 | Evento técnico y persona no son la misma identidad. |
| 5 / 1:10 | Correlacionar sin ocultar incertidumbre | Cuatro relaciones y tres resultados; P3/P10 | Las coincidencias exactas no prueban identidad real ni unicidad universal. |
| 6 / 1:00 | Tres almacenes, tres responsabilidades | Mongo/Redis/SQL y mini ERD; P1/R3/R4 | TTL efímero y SQL curado; no confundir caché con fuente de verdad. |
| 7 / 0:55 | De SQL a consultas controladas | Cuatro rutas y límites de privacidad; P1/R6 | Sin IBAN/salario en búsquedas, pero aún hay PII y falta auth. |
| 8 / 0:55 | Medir lo que realmente se emite | Tres métricas; no curvas inventadas; P1/R5/R8 | Persistencia Mongo, no SQL; medias sí, p95 no acreditado. |
| 9 / 1:10 | Calidad con resultados transparentes | Barras 246/21/40 y cobertura separada; P4/P8/R9 | HRP-71 es sintético; resultado Windows no verde y no reejecutado ahora. |
| 10 / 1:00 | Evolución por evidencia | Timeline de nueve jornadas; P6 | Fechas de integración, no reuniones reconstruidas ficticiamente. |
| 11 / 0:55 | Decisiones, riesgos y aprendizaje | DAFO 2×2; P1/P7 | La madurez incluye reconocer orquestación y mediciones que faltan. |
| 12 / 1:10 | Qué entregamos y cómo continuarlo | README/runbook/NotebookLM y bibliografía; P5/P7 | Cierre documental autorizado; nuevas funciones pertenecen a trabajo posterior. |

Total orientativo12 minutos. Mantener una idea por slide y no más de 4 bullets.
Añadir las fuentes correspondientes en nota o pie. La bibliografía puede ser anexo
fuera de las 12 slides si el formato lo permite. No dedicar una slide a cada herramienta.

## 13. Demo y plan alternativo (propuesta, no ejecutada)

Mostrar Compose saludable y explicar qué servicio ejecuta cada proceso.
Mostrar metadatos técnicos de ingesta, nunca payloads. Enseñar esquema y rutas OpenAPI;
un health200 no implica datos cargados. Para transformación, explicar la prueba
sintética versionada HRP-71 y sus assertions, sin llamarla prueba Kafka real.
Mostrar configuración del dashboard; solo enseñar series reales si están disponibles,
con hora/ventana. Si no hay entorno operativo, usar código, pruebas y diagramas
rotulados como explicación; no fabricar capturas de ejecución.

No ejecutar pruebas de integración contra bases con datos útiles: las fixtures
sintéticas realizan limpieza. No eliminar volúmenes para preparar una demo.

## 14. Preguntas difíciles: respuestas defendibles

**¿Está conectado todo en un único proceso?** No. La ingesta está orquestada;
transformación y SQL se unen en la prueba sintética. Falta worker productivo completo.

**¿Son personas reales identificadas de forma única?** No se demuestra; hay correlación
operacional exacta con ambigüedad explícita.

**¿Cuántos mensajes/segundo soporta?** Hay instrumentación de consumo, pero no un
benchmark de capacidad sostenida en este paquete.

**¿Está todo en verde?** La aceptación comunicada es 18/19. El último resultado local
fue 246/21/40 y no se está presentando como suite verde.

**¿Por qué no hay frontend?** Se excluyó del cierre por decisión de alcance. La API
es una base para trabajo posterior, no una interfaz entregada.

**¿Qué aporta Redis aquí?** Un adapter temporal con TTL; su disponibilidad no significa
que esté integrado en el loop principal o en HRP-71.

## 15. Fuentes propias y bibliografía

Fuentes propias (repositorio https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1):

- P1: código del corte [f3a952b](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/tree/f3a952b).
- P2: frontera raw [PR33](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/33), commit d1a2393.
- P3: correlación [PR42](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/42), commit 0512612.
- P4: HRP-71 [PR65](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/65), commit fa156b9.
- P5: primer cierre documental [PR80](https://github.com/Bootcamp-IA-MAD-P7/Proyecto-DataEngineer-Grupo1/pull/80), commit 275131a.
- P6: dailies e historial; cronología reproducida en sección 10.
- P7: matriz de aceptación comunicada; alcance y límites reproducidos en sección 2.
- P8: test harness y resultado local reportado en la conversación; sección 9.
  No se adjunta log íntegro ni se afirma ejecución nueva.
- P9: observación HRP-29, 20 objetos y cinco formas; sección 4.
- P10: observación HRP-43 y evaluación ADR-0006, muestra 2000; sección 5.

Referencias externas primarias consultadas el 2026-09-08:

- R1. Confluent. [Python client API](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html). Consultar poll, commit y configuración del cliente; no demuestra el throughput del proyecto.
- R2. MongoDB. [Unique indexes](https://www.mongodb.com/docs/manual/core/index-unique/). Fundamenta la restricción compuesta de coordenadas dentro de una colección.
- R3. PostgreSQL Global Development Group. [PostgreSQL 16: constraints](https://www.postgresql.org/docs/16/ddl-constraints.html). PK, FK y unicidad; no convierte passport en clave única de negocio.
- R4. Redis. [EXPIRE](https://redis.io/docs/latest/commands/expire/). Expiración y renovación de TTL; la política de 3600 s procede del código propio.
- R5. Prometheus. [Histograms and summaries](https://prometheus.io/docs/practices/histograms/). Distinguir sum/count y distribución por buckets al interpretar duraciones.
- R6. FastAPI. [Tutorial / User Guide](https://fastapi.tiangolo.com/tutorial/). Contexto de API, validación y OpenAPI; rutas y errores propios están en el repositorio.
- R7. Docker. [Compose services reference](https://docs.docker.com/reference/compose-file/services/). Interpretar profiles, healthchecks y restart; no certifica disponibilidad productiva.
- R8. Grafana Labs. [Provision Grafana](https://grafana.com/docs/grafana/latest/administration/provisioning/). Explicar configuración versionada de datasource/dashboard.
- R9. GitHub. [Understanding GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions). Contexto de workflows/jobs/checks; no demuestra que el último run esté verde.

La bibliografía explica conceptos, no certifica capacidades del proyecto.
Versiones del software proceden de configuración propia. El generador nunca es
fuente autorizada de contrato. No introducir fuentes externas adicionales sin
identificarlas y distinguirlas de resultados propios.

## 16. Prompt para generar la presentación

```text
Usa este paquete como fuente autocontenida de HR Pro al 8 de septiembre de 2026.
Genera una presentación técnica profesional en español de 12 diapositivas,
aproximadamente12 minutos, siguiendo el guion de la sección 12. Incluye notas
del orador y referencias P/R por diapositiva. Si la herramienta no puede producir
un archivo de presentación, devuelve el contenido estructurado listo para maquetar.

Narrativa: problema → decisiones → implementación real → evidencia → aprendizaje
y cierre. Diseño sobrio, legible, alto contraste; una idea por slide, hasta4 bullets,
diagramas pequeños y tablas cortas. Añade una tabla alternativa para cada gráfica.
Usa los datos explícitos para barras de aceptación y resultados de tests.
No dibujes series temporales de rendimiento sin muestras reales.

Distingue siempre aceptación del responsable, implementación en código, prueba
sintética, resultado local reportado y trabajo futuro. Mantén el frontend excluido,
la ausencia de worker productivo Mongo→ETL→SQL, HRP-71 sin broker real ni Redis,
y el resultado 246/21/40 no verde. No conviertas cobertura en porcentaje de éxito.

No inventes demo, interfaz, CI verde, benchmark, auth, p95/p99, métricas SQL,
exactly-once ni identidad universal. No incluyas PII, secretos, payloads reales
ni contenido del generador. Utiliza ejemplos abstractos claramente sintéticos.
Termina con entregables documentales, límites y próximos pasos sin promesas nuevas.
```

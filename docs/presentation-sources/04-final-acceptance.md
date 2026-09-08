# Aceptación final — fuente para exposición

Miguel, responsable, comunica aceptación de 18/19 checks: entrega 5/5, esencial 6/6,
medio 3/3, avanzado 3/3, experto 1/2. Frontend excluido del cierre.
Mostrar barras etiquetadas **aceptación**, no «tests pasados» ni «rendimiento».

[Detalle de los 19 requisitos y evidencia](../delivery-evidence.md).

La demo de runtime verificó Kafka → MongoDB → Redis → PostgreSQL → API y la
monitorización de ingesta. Esto no acredita miles de mensajes/segundo sostenidos,
alta disponibilidad ni recuperación ante desastres.
El último intento local conocido es 246 pasan, 21 fallan, 40 omitidos, cobertura 82,91 %;
no se repitió para este cambio documental.

El frontend sigue excluido. La extensión posterior al cierre incorpora el worker
ETL y los servicios API/ETL al Compose local; no modifica Jira ni publica un release.

# Observaciones autorizadas de Kafka

Esta carpeta almacena evidencia estructural obtenida al consumir mensajes reales del
broker. Su propósito es desbloquear el contrato de datos y las pruebas sin inspeccionar
el generador educativo.

## Qué se registra

- Topic, fecha, entorno y método de observación, sin secretos.
- Partición, offset y timestamp como metadatos de trazabilidad.
- Categorías de evento, nombres de campos, tipos, presencia de nulos y repetición.
- Posibles claves de correlación, siempre marcadas como candidatas hasta validación.
- Comportamientos relevantes: mensajes fuera de orden, duplicados o información
  incompleta.

## Qué no se registra

- Código, repositorio o lógica del generador educativo.
- Credenciales, URIs con contraseña, archivos `.env` o tokens.
- Mensajes completos ni valores personales, bancarios o identificativos reales.

## Flujo

1. Crear una copia de `_template.md` con formato `YYYY-MM-DD-HRP-29-kafka.md`.
2. Rellenar una tabla estructural con observaciones reales.
3. Ejecutar los checks de calidad y abrir una PR o hacer un commit trazable.
4. Enlazar el documento y commit/PR en HRP-29.
5. Gaby usa solo ese documento como base para actualizar HRP-24.

# Paquetes de tarea

Cada paquete reúne el contexto que puede entregarse a un asistente sin obligarle a navegar por Jira ni a inferir requisitos. Es un artefacto temporal de trabajo, pero si el resultado condiciona una decisión se conserva junto con la spec.

Crear uno desde la raíz del repositorio:

```powershell
.\scripts\new-task-packet.ps1 -JiraKey HRP-24 -Slug contrato-datos
```

Completa primero el contexto autorizado y pide una única salida concreta. No añadas mensajes Kafka completos, secretos ni material del generador educativo.

## Lectura al cierre — 2026-09-08

Los paquetes HRP son registros de contexto de su tarea, no fichas de estado actuales.
Sus specs enlazan ahora evidencia de integración. No se deben usar sus campos Draft
ni casillas históricas para calcular el progreso del proyecto. Para trabajo nuevo
usar la plantilla y la [documentación vigente](../../README.md).

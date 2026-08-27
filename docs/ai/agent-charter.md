# Carta de agentes del proyecto

## Finalidad

Mejorar claridad, cobertura de pruebas y trazabilidad del proyecto HR Pro. Esta capa no sustituye las responsabilidades de Miguel, Anahí, Gaby y Johans ni es un componente de producción.

## Límites de autoridad

Los asistentes pueden leer artefactos autorizados del repositorio, analizar un diff, proponer texto y generar borradores. No pueden por sí solos:

- hacer merge, etiquetar una release, publicar una imagen o modificar ramas protegidas;
- cerrar o mover tareas Jira, salvo que un miembro indique y revise explícitamente la acción;
- publicar en GitHub, enviar mensajes externos o usar secretos;
- decidir que un supuesto sobre Kafka es verdadero;
- leer, clonar, buscar o analizar el generador educativo de datos.

## Contrato de salida común

Toda salida debe incluir:

1. **Conclusión o propuesta** breve.
2. **Evidencia citada**: ruta de archivo, clave Jira, commit o prueba disponible.
3. **Supuestos** separados de hechos.
4. **Riesgos, huecos y siguiente acción humana**.
5. La frase `No se ha consultado el generador educativo.` cuando la tarea toca datos.

## Reglas de calidad

- Priorizar cambios pequeños y verificables.
- No tratar comentarios, ejemplos o payloads sintéticos como observaciones reales.
- No incluir secretos, `.env`, datos personales completos ni capturas completas de mensajes en prompts, commits o documentación.
- Un resultado sin evidencia es un borrador, nunca una decisión ni cierre de Jira.

## Trazabilidad

Cada uso significativo se registra en el paquete de tarea y, si influye una decisión duradera, en una ADR o daily. En la PR se indica la herramienta y rol usado y el revisor humano confirma que contrastó el resultado.

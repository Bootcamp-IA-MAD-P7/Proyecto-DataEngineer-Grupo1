# Flujo SDD — Specification-Driven Development

SDD no significa escribir documentos largos antes de trabajar. Significa eliminar
ambigüedad antes de programar y convertir cada requisito en evidencia comprobable.

## Cadena de trazabilidad obligatoria

```text
Jira HRP-XX
  -> docs/specs/HRP-XX-*.md
  -> rama con HRP-XX
  -> commits con HRP-XX
  -> pruebas nombradas por comportamiento
  -> PR hacia develop
  -> comentario de cierre con evidencia
```

Si falta un eslabón, la tarea no está terminada aunque el código funcione localmente.

## Ciclo por tarea

1. **Refinar en Jira.** Objetivo, responsable, dependencia, tamaño y criterio de
   aceptación.
2. **Escribir la spec.** Parte de `docs/specs/template.md`; establece alcance,
   exclusiones, riesgos, pruebas y evidencia esperada.
3. **Comprobar el Definition of Ready.** Si falta un dato o decisión, se crea una
   tarea de descubrimiento o ADR; no se adivina.
4. **Crear rama.** `feature/HRP-XX-resumen` desde `develop`.
5. **Implementar en vertical.** Cambio mínimo + prueba + documentación juntos.
6. **Ejecutar el arnés.** Pre-commit, pruebas unitarias y las integraciones que
   afecte la tarea.
7. **Abrir PR.** Enlaza spec, evidencia, riesgos y tarea Jira.
8. **Revisión de pares.** Otra persona revisa diseño, pruebas y operación; no solo
   sintaxis.
9. **Cerrar.** Tras merge y evidencia verificable, actualiza Jira con la plantilla
   de HRP-22.

## Definition of Ready

Una tarea puede pasar a **En curso** únicamente si:

- Tiene responsable y resultado esperado.
- Sus dependencias están resueltas o explícitamente aceptadas.
- Tiene criterios de aceptación observables.
- Tiene spec vinculada si afecta código, infraestructura, datos u operación.
- Indica qué prueba confirma el resultado.
- No requiere consultar el generador educativo.

## Definition of Done

Una tarea pasa a **Finalizada** únicamente si:

- El resultado de la spec existe en `develop` o está documentado si es una tarea de
  diseño.
- Pruebas relevantes en verde o justificación explícita de por qué no aplican.
- Lint, formato y tipos en verde cuando hay código Python.
- PR revisada y evidencia enlazada.
- Documentación, ADR, runbook o fixture actualizados cuando cambie su ámbito.
- Jira contiene el comentario de cierre verificable.

## Tipos de decisión

| Situación | Artefacto requerido |
|---|---|
| Cambio pequeño y reversible | Spec + PR |
| Cambio de contrato, modelo o límite | Spec + ADR + pruebas |
| Hallazgo de mensajes Kafka | Documento de observación + actualización de contrato |
| Incidencia operativa | Runbook + prueba de regresión |
| Decisión diaria sin impacto duradero | Daily |

## Revisión de pull request

El revisor responde explícitamente:

1. ¿La solución cumple la spec y no añade alcance oculto?
2. ¿Los fallos esperables están tratados y probados?
3. ¿Los datos raw, curados y temporales permanecen en sus límites?
4. ¿Se evita la exposición de secretos, payloads o acceso al generador?
5. ¿La evidencia de cierre permite repetir la verificación?

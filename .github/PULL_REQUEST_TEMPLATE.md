<!-- Título obligatorio: HRP-XX tipo: resumen breve. Ej.: HRP-30 feat: add Kafka consumer -->

## Contexto y trazabilidad

- **Jira:** HRP-XX
- **Spec:** `docs/specs/HRP-XX-*.md`
- **Responsable:**
- **Revisor propuesto:**
- **Asistencia IA:** ninguna / nombre de la herramienta y rol usado

## Qué cambia y por qué

<!-- Explica el resultado y el límite. No describas solo archivos modificados. -->

## Criterios de aceptación

- [ ] Criterio 1 cumplido.
- [ ] Caso de error o límite cubierto.
- [ ] No se ha ampliado el alcance sin actualizar la spec.

## Validación ejecutada

- [ ] `pre-commit run --all-files`
- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `mypy src`
- [ ] `pytest`
- [ ] Integración / E2E (si aplica; enlazar resultado):

## Datos, seguridad y operación

- [ ] No incluye secretos, `.env`, volúmenes Docker ni capturas completas de mensajes.
- [ ] No se ha leído, clonado ni analizado el generador educativo.
- [ ] Logs, métricas, migraciones o runbook actualizados si aplican.

## Riesgos, decisiones y reversión

- ADR relacionada / decisión tomada:
- Riesgo conocido:
- Cómo revertir este cambio:

## Checklist de revisión

- [ ] Una persona distinta de quien propone la PR ha revisado el cambio.
- [ ] La spec, documentación y evidencia de Jira están actualizadas.
- [ ] La tarea solo se moverá a Finalizada después de merge y evidencia verificable.
- [ ] Si se utilizó IA, su resultado se ha contrastado con la spec, el diff y las pruebas.

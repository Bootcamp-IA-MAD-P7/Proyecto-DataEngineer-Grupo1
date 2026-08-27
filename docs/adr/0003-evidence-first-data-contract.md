# ADR-0003: Contrato de datos basado en evidencia observada

## Estado

Aceptada.

## Contexto

El proyecto educativo prohíbe explícitamente examinar el código generador de datos.
El README público ofrece expectativas útiles, pero no es garantía del payload real,
las claves de correlación ni el orden de llegada.

## Decisión

El contrato de Kafka se divide en dos partes:

- **Conocimiento publicado:** contenido del README autorizado, marcado como
  provisional.
- **Conocimiento observado:** solo lo que HRP-29 haya visto desde el broker y haya
  documentado con ejemplos minimizados.

Ningún nombre de campo, tipo, regla de unión o comportamiento de orden pasa a código
productivo hasta estar en la segunda categoría. Las incertidumbres permanecen visibles
y cubiertas por pruebas de error o fixtures pendientes.

## Consecuencias

- Se evita el sesgo de conocer el generador.
- La primera versión requiere una tarea explícita de descubrimiento.
- Las specs pueden avanzar con supuestos marcados, pero no darse por finalizadas.
- Cada cambio de contrato deberá actualizar fixtures y pruebas.

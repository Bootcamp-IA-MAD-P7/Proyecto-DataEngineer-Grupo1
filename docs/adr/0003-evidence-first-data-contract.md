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
- **Conocimiento observado:** solo lo que HRP-29 u otra observación autorizada haya visto desde el broker y haya
  documentado con ejemplos minimizados.

Los hechos sobre nombres, tipos y orden requieren evidencia observada. Las reglas
operacionales requieren una decisión explícita fundamentada en esa evidencia, no
se presentan como hechos empíricos universales. ADR-0006 registra esta distinción
para correlación: una estrategia aceptada no prueba identidad real.
Las incertidumbres permanecen visibles y cubiertas por casos límite.

## Consecuencias

- Se evita el sesgo de conocer el generador.
- La primera versión requiere una tarea explícita de descubrimiento.
- Las specs pueden avanzar con supuestos marcados, pero no darse por finalizadas.
- Cada cambio de contrato deberá actualizar fixtures y pruebas.

## Aplicación al cierre

HRP-29 describe formas; HRP-43 amplía la observación; HRP-44 define clasificación
por claves y ADR-0006 correlación operacional. El
[contrato vigente](../02-data-contract.md) separa esos niveles de conocimiento.

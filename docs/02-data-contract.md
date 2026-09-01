# Contrato de datos

## Fuente autorizada

Este documento se fundamenta en el README público autorizado del repositorio educativo
y en la observación estructural aprobada de HRP-29, registrada en
`docs/observations/2026-08-27-HRP-29-kafka.md`. No se ha consultado código generador.

El README es contexto publicado y provisional. La observación HRP-29 es la fuente de
los hechos estructurales descritos como observados. Una incógnita no demostrada por
esa evidencia permanece pendiente.

## Tipos de información publicados

Estos grupos proceden del contexto público autorizado. No existe todavía un mapping
aprobado entre ellos y las variantes estructurales observadas A–E.

The mapping from exact observed shapes to business domains is defined by HRP-44:
[`docs/specs/HRP-44-domain-classification.md`](specs/HRP-44-domain-classification.md).
Technical A–E labels remain neutral observation references.

| Tipo | Campos documentados |
|---|---|
| Personal data | Name, Lastname, Sex, Telfnumber, Passport, E-Mail |
| Location | Fullname, City, Address |
| Professional data | Fullname, Company, Company Address, Company Telfnumber, Company E-Mail, Job |
| Bank Data | Passport, IBAN, Salary |
| Net Data | Address, IPv4 |

## Alcance Kafka observado

HRP-29 registró una muestra acotada de 20 objetos JSON del topic `probando` y la
partición `0`. El nombre del topic pertenece únicamente al alcance de esa muestra y no
es una configuración universal. HRP-29 no establece garantías de ordering entre
variantes, entre particiones o de negocio, ni una secuencia de persona completa.

Se observaron cinco conjuntos de campos de nivel superior. A–E son etiquetas técnicas
neutrales y no categorías de negocio.

| Variante | Frecuencia | Campos raw observados | Tipos aparentes/observados |
|---|---:|---|---|
| A | 7/20 | `IPv4`, `address` | Ambos campos: string |
| B | 4/20 | `company`, `company address`, `company_email`, `company_telfnumber`, `fullname`, `job` | Todos los campos: string |
| C | 4/20 | `IBAN`, `passport`, `salary` | Todos los campos: string |
| D | 3/20 | `address`, `city`, `fullname` | Todos los campos: string |
| E | 2/20 | `email`, `last_name`, `name`, `passport`, `sex`, `telfnumber` | `sex`: array; los demás campos: string |

Los nombres raw se conservan exactamente como fueron observados. Los tipos aparentes
describen únicamente la estructura JSON y no demuestran formato, dominio, rango o
semántica. En particular, no se interpreta el contenido de `sex`, `salary` ni ningún
otro valor.

La evidencia no demuestra si los campos son requeridos, opcionales o nullable. Que un
campo no aparezca en otras variantes no lo convierte en opcional, y que no se haya
observado JSON `null` no demuestra que esté prohibido.

## Conformidad estructural provisional

Un objeto puede clasificarse técnicamente y de forma provisional como A, B, C, D o E
solo si su conjunto de campos y sus tipos aparentes coinciden exactamente con la
estructura observada correspondiente.

Esta clasificación no es una taxonomía de negocio, un esquema canónico, un mapping a
Personal, Location, Professional, Bank o Net Data, ni una garantía de que las cinco
variantes sean exhaustivas o permanezcan estables.

Una estructura con campos adicionales o ausentes, tipos diferentes o JSON `null`
donde no fue observado se considera `non-conforming/unknown` respecto a este contrato
observado. No debe forzarse a A–E ni utilizarse para inventar semántica. Este resultado
no significa automáticamente que los datos sean inválidos para el negocio; su
tratamiento downstream definitivo permanece pendiente cuando la arquitectura vigente
no lo haya definido.

## Correlación, agrupación y duplicados

`passport`, `fullname` y `address` son únicamente candidatos de correlación porque
sus nombres raw aparecen en más de una variante. HRP-29 no comparó valores ni demostró
igualdad, unicidad, normalización, prioridad o significado de negocio.

No existe una clave de correlación definitiva ni reglas aprobadas de resolución de
conflictos, completitud o agrupación de personas. La ausencia de coordenadas Kafka
repetidas en la muestra no establece detección de duplicados de negocio.

## Reglas arquitectónicas vigentes

- Un mensaje se conserva en MongoDB raw antes de transformarse, dentro de los límites
  de seguridad y privacidad del proyecto.
- Un mensaje técnicamente no procesable no detiene el consumer.
- Una estructura `non-conforming/unknown` no se equipara automáticamente a un dato de
  negocio inválido.
- La idempotencia raw usa `topic + partition + offset`; no es una regla de agrupación
  ni de deduplicación de personas.

## Riesgo de integración

La muestra de HRP-29 es evidencia real pero acotada. No demuestra exhaustividad,
estabilidad futura, semántica, orden de negocio ni capacidad para formar personas
completas. Cualquier decisión duradera de correlación o cambio del límite contractual
requiere evidencia adicional y revisión humana, además de la documentación y las
pruebas correspondientes. También requiere una ADR cuando resulte apropiada por el
alcance y la relevancia de la decisión.

## Incógnitas y decisiones pendientes

- Mapping entre A–E y los grupos de información publicados.
- Semántica, formatos, rangos y nombres canónicos de los campos.
- Propiedades required, optional y nullable.
- Evolución y versionado ante nuevas estructuras.
- Clave de correlación, normalización, unicidad y resolución de conflictos.
- Condiciones de completitud y agrupación de una persona.
- Ordering entre variantes, particiones o entidades de negocio.
- Detección de duplicados de negocio.
- Tratamiento downstream definitivo de estructuras `non-conforming/unknown`.
- Configuración operativa de topics fuera de la muestra observada en `probando`.

# Contrato de datos

## Fuente autorizada

Este documento se fundamenta en el README público autorizado del repositorio educativo
y en la observación estructural aprobada de HRP-29, registrada en
`docs/observations/2026-08-27-HRP-29-kafka.md`. No se ha consultado código generador.

El README es contexto publicado y provisional. La observación HRP-29 es la fuente de
los hechos estructurales descritos como observados. Una incógnita no demostrada por
esa evidencia permanece pendiente.

## Tipos de información publicados

Estos grupos proceden del contexto público autorizado. El mapping runtime fue
incorporado en HRP-44 (PR #35, 2026-09-01); A–E se conservan como etiquetas históricas.

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

## Conformidad de la observación histórica (no algoritmo runtime)

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

HRP-29 no estableció una clave definitiva. Posteriormente ADR-0006 fue integrado
mediante PR #42 el 2026-09-02: admite cuatro relaciones exactas para correlación
operacional, sin probar identidad real. HRP-50/51/96 definen consolidación,
incertidumbre y duplicados. No hay una clave de negocio universal. La ausencia de coordenadas Kafka
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

## Incógnitas que la observación HRP-29 no resolvió

- Mapping: resuelto operacionalmente por HRP-44; no inferido de HRP-29 por sí solo.
- Semántica, formatos, rangos y nombres canónicos de los campos.
- Propiedades required, optional y nullable.
- Evolución y versionado ante nuevas estructuras.
- Identidad real y unicidad universal siguen sin demostrarse; las reglas operativas
  exactas y la ausencia de normalización están decididas en ADR-0006.
- Completitud operacional implementada en HRP-50/51/96; no prueba completitud real.
- Ordering entre variantes, particiones o entidades de negocio.
- Detección de duplicados de negocio.
- Tratamiento downstream definitivo de estructuras `non-conforming/unknown`.
- Configuración operativa de topics fuera de la muestra observada en `probando`.

## Contrato runtime vigente — 2026-09-08

La clasificación HRP-44 usa **conjunto exacto de claves**, no los tipos observados
en la muestra. Campos extra o ausentes producen `unknown`; cambiar el valor a null
o a otro tipo no cambia por sí solo la clasificación. HRP-45 comprueba coherencia
técnica de la entrada y clasificación, no sanea semánticamente todos los campos.

| Etiqueta histórica | Dominio runtime | Claves exactas |
|---|---|---|
| E | Personal | name, last_name, sex, telfnumber, passport, email |
| D | Location | fullname, city, address |
| B | Professional | fullname, company, company address, company_telfnumber, company_email, job |
| C | Bank | passport, IBAN, salary |
| A | Net | address, IPv4 |

No confundir la regla descriptiva de conformidad observada (claves y tipos aparentes)
con el clasificador implementado (solo claves). Un objeto reconocido no implica
que todos sus valores sean utilizables para correlación o persistencia.

Todo objeto JSON se conserva raw antes de clasificar. Ausencia de valor, UTF-8
inválido, JSON inválido y JSON no objeto se guardan como inválidos técnicos con
su razón. Un error de persistencia no autoriza confirmar el offset.
Ver [arquitectura](01-architecture.md), [modelo](03-data-model.md) y
[ADR-0006](adr/0006-person-correlation-key.md).

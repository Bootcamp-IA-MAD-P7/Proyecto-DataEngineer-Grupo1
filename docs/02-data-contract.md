# Contrato de datos

## Fuente autorizada

Este documento se fundamenta en el README público autorizado del repositorio educativo y en la futura observación de eventos recibidos. No se ha consultado código generador.

## Tipos de información esperados

| Tipo | Campos documentados |
|---|---|
| Personal data | Name, Lastname, Sex, Telfnumber, Passport, E-Mail |
| Location | Fullname, City, Address |
| Professional data | Fullname, Company, Company Address, Company Telfnumber, Company E-Mail, Job |
| Bank Data | Passport, IBAN, Salary |
| Net Data | Address, IPv4 |

## Riesgo de integración

El README advierte que los datos pueden ser inconsistentes. Las claves potenciales de unión son Passport, Fullname y Address, pero la estrategia definitiva se decidirá tras observar eventos reales. Toda decisión debe quedar registrada en una ADR y cubierta por fixtures de prueba.

## Reglas provisionales

- Un mensaje se conserva íntegro en MongoDB antes de transformarse.
- Un evento inválido nunca detiene el consumer.
- La clasificación de un evento debe ser explícita y trazable.
- La agrupación debe ser idempotente: reprocesar un evento no puede duplicar una persona.

## Pendiente de descubrimiento

- Topic y formato exacto del evento.
- Identificador técnico del evento.
- Orden de llegada de tipos de datos.
- Reglas de resolución cuando una clave no coincide.


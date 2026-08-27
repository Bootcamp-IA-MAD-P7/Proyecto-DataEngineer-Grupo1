# Project Charter

## Problema

HR Pro necesita integrar eventos de recursos humanos emitidos continuamente a través de Kafka, preservarlos y convertirlos en información preparada para consulta.

## Objetivo

Implementar un pipeline Dockerizado que consuma Kafka, persista eventos crudos en MongoDB, agrupe la información de cada persona y la cargue en PostgreSQL. El proyecto alcanzará los niveles esencial, medio, avanzado y experto definidos en el briefing.

## Alcance

- Kafka como fuente de eventos.
- MongoDB como zona raw y de auditoría.
- PostgreSQL como almacén relacional final.
- Redis como estado temporal de agrupación.
- Logs, pruebas, Docker Compose, Prometheus, API y Streamlit.

## Restricción no negociable

No se accede, clona, lee, analiza ni intenta inferir el código que genera los datos. Solo se usan el README autorizado, los mensajes recibidos desde Kafka y los requisitos del briefing.

## Equipo

| Persona | Miembro | Responsabilidad principal |
|---|---|
| Persona 1 | Miguel | Coordinación, Git, Docker, calidad, documentación y demo |
| Persona 2 | Anahí | Kafka y MongoDB |
| Persona 3 | Gaby | ETL, Redis y monitorización |
| Persona 4 | Johans | PostgreSQL, API y frontend |

## Criterio de éxito

El sistema se puede iniciar de forma reproducible, procesa datos de Kafka de forma continua, permite demostrar trazabilidad del evento crudo al registro SQL final y ofrece consultas desde una API y un frontend sencillo.

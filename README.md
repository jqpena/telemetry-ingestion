<main style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
    <h1>Telemetry Event Driven</h1>
    <article style="display: flex; gap: 10px; justify-content: center;">
        <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="pre-commit" style="max-width:100%;"></a>
        <a href="./LICENSE"><img  alt="GitHub License" src="https://img.shields.io/github/license/jqpena/telemetry-ingestion"></a>
        <div><img alt="Python Version from PEP 621 TOML" src="https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fjqpena%2Ftelemetry-ingestion%2Frefs%2Fheads%2Fmain%2Fpyproject.toml">
        </div>
    </article>
</main>

**A cloud-ready, event-driven telemetry ingestion API** built with FastAPI, and PostgreSQL designed to simulate a production-grade data ingestion layer for high volumen ingestion data

## Overview

This project implements the first step of a telemetry data ingestion platform. Focusing on, reliable ingestion of structured events coming from a telemetry capture; schema versioning for a evolving database with the usa of modern tools (Alembic); clean API architecture with separation of concerns, and finally scalable data storage/retrieval for high throughput systems. The system is designed with a **Data Engineering mindset**, modeling how real world platforms handle ingestion before introducing asynchronous processing and analytics layers.

## Architecture design

Tech stack

* Backend: FastAPI
* Database: PostgreSQL

### Schema management

Database schema evolution is the natural state of real world applications thats why for real world application have the database schemas under version control its crucial, to handle the evolution of database *Alembic* held us to ensure.

* Version controlled schema changes
* Easy upgrade and rollback from versions
* Reproducibility across environments
* Safe interaction in production like systems

The current schema includes:

Single table `raw.events` for telemetry ingestion, the table is isolated in `raw` logical schema to allow a fine grain permission access across object of database, and indexes to optimize query performance on high-volume data

> [!Note]
> Database roles and administrative queries like schemas creations are intentionally excluded from migrations, as they belong to **DBA responsibilities rather than application schema definitions.**

### Data Modeling

The ingestion layer follows a raw data approach, storing events as received, with minimal transformation, keep everything in its own domain, this design enables:
Future enrichment pipelines, aggregations or postprocessing data curation, drawing a clear line between *Ingestion* and *Processing* concerns. There's always space to evolving the schema toward time-series optimization (e.g. **TimeScaleDB**).

#### Models

`raw.events` table

| Column      | Description                      |
| ----------- | -------------------------------- |
| id          | Unique event identifier (UUID7)  |
| event_type  | Type of telemetry event          |
| service     | Source service                   |
| value       | Measured value                   |
| host        | FQFN if apply of the source host |
| timestamp   | Event occurrence time            |
| received_at | Ingestion time                   |

### API Design

The API is structured to reflect production grade backend practices, separation of layers for a layered structured API, extensibility for future features (async processing, validation layers), and clean boundary between API, business logic, and persistence. As an add-on and given the nature of telemetry systems (high volume of data), the API includes an opinionated pagination approach to reduce network overhead, prevent large payload transfer and reduce database processing chunking by a limited size the total of events to fetch at once.

### Running locally

```bash
git clone https://github.com/jqpena/telemetry-ingestion.git
cd telemetry-ingestion
```

```bash
# Start stack services using docker
docker compose up -d --build
```

```bash
# To apply the almebic migrations you have to be able to connect to database service
# if you deployed the database using the docker-compose.yaml file edit it and add the
# followed lines in db service and then restart using docker compose restart
#   ports:
#     - 5432:5432
alembic upgrade head
```

### Roadmap

This repo can be use as a baseline of a real world full event-driven data platform and the planned improvements tackle

* Asynchronous processing with Celery + Redis
* Data enrichment pipelines
* Aggregation and analytics layer
* AWS deployment (cloud-native architecture)
* Time-series optimization (TimescaleDB postgreSQL extension)

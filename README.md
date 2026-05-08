# Real-Time Session Ingestion & Monitoring

## Prerequisites

- Docker & Docker Compose

## Start everything

```bash
docker compose up --build
```

This starts PostgreSQL, the backend API, and the simulator in order. The simulator waits for the backend to be healthy before running.

Default scenario is `happy_path`. Change it with `SCENARIO`:

```bash
SCENARIO=rejected docker compose up --build
SCENARIO=pipeline_failure docker compose up --build
SCENARIO=all docker compose up --build
```

Simulation speed defaults to 10× real-time (a 60s session finishes in ~6s). Adjust with `SPEED`:

```bash
SPEED=1 docker compose up --build    # real-time
SPEED=20 docker compose up --build   # very fast
```

## API

- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

# Real-Time Session Ingestion & Monitoring

## Prerequisites

- Docker Desktop

## Start the stack

```bash
docker compose up --build
```

This starts PostgreSQL, the backend API, and the Next.js dashboard. Open the dashboard at `http://localhost:3000`.

You can also hit the **Play** button next to the project in Docker Desktop — it does the same thing. The simulator is not included so it won't run automatically.

## Run the simulator

Run it any time after the stack is up. Each run creates new sessions in the dashboard — you can run it as many times as you want.

```bash
docker compose --profile simulator run --rm client
```

**In Docker Desktop:** expand the project, find the **client** container, and click the **Play (▶)** button. Each click runs a new simulation.

**Scenarios** (default: `all`):

| Scenario | What happens |
|---|---|
| `all` | Runs all three scenarios back-to-back |
| `happy_path` | Uploading → processing → review → approved |
| `rejected` | Degraded streams → quality fails → rejected |
| `pipeline_failure` | Transcode fails at 45% → failed |

```bash
SCENARIO=happy_path docker compose --profile simulator run --rm client
SCENARIO=rejected docker compose --profile simulator run --rm client
SCENARIO=pipeline_failure docker compose --profile simulator run --rm client
```


## API

- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

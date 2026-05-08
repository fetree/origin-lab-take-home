# Real-Time Session Ingestion & Monitoring

## Prerequisites

- Docker & Docker Compose

## Start the backend

```bash
docker-compose up --build
```

This starts PostgreSQL and the backend API at `http://localhost:8000`. Migrations run automatically on startup.

## Run the simulator

In a separate terminal, pick a scenario:

```bash
# Happy path — all streams succeed, session approved
docker-compose --profile simulator run --rm client --scenario happy_path

# Rejected — low FPS, audio clipping, high inactivity
docker-compose --profile simulator run --rm client --scenario rejected

# Pipeline failure — transcode fails mid-way
docker-compose --profile simulator run --rm client --scenario pipeline_failure

# Run all three sequentially
docker-compose --profile simulator run --rm client --scenario all
```

### Speed

By default the simulator runs at 10× real-time (a 60s session finishes in ~6s). Adjust with `SPEED`:

```bash
SPEED=1 docker-compose --profile simulator run --rm client --scenario happy_path   # real-time
SPEED=20 docker-compose --profile simulator run --rm client --scenario all         # very fast
```

## API

- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

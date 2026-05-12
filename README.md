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

---

## Architecture

```
┌─────────────┐    NDJSON stream     ┌─────────────┐    SSE     ┌─────────────┐
│   Simulator │ ──────────────────▶  │   Backend   │ ────────▶  │  Dashboard  │
│  (Python)   │   POST /sessions/    │  (FastAPI)  │            │  (Next.js)  │
│             │   {id}/stream        │             │            │             │
└─────────────┘                      └──────┬──────┘            └─────────────┘
                                            │
                                     ┌──────▼──────┐
                                     │ PostgreSQL  │
                                     │  sessions   │
                                     │stream_events│
                                     │stream_health│
                                     └─────────────┘
```

**Client → Backend:** The simulator opens a single long-lived `POST /sessions/{id}/stream` and writes newline-delimited JSON events as they're produced — all streams multiplexed over one connection. The backend reads the body chunk-by-chunk via `async for chunk in request.stream()`, processing each event as it arrives.

**Backend → Dashboard:** SSE (Server-Sent Events) on `GET /sessions/stream` (list updates) and `GET /sessions/{id}/stream` (per-session detail). An in-memory `asyncio.Queue` per subscriber fans out events from ingestion to all connected dashboard clients without blocking writes.

**Streams** — 9 stream types multiplexed over a single POST:

| Stream | Frequency | What it carries |
|---|---|---|
| `lifecycle` | sparse | session state changes |
| `telemetry` | 2–5s | CPU/GPU/FPS system health |
| `upload` | per file | upload progress % |
| `input` | 30–60 Hz | keyboard/mouse events |
| `camera` | 15–30 Hz | 3D position and rotation |
| `audio_levels` | periodic | RMS/peak dB, clipping flag |
| `transcode` | periodic | HLS rendition progress, failure |
| `quality` | sparse | per-metric pass/fail scores |
| `review` | once | reviewer decision + reason |

**Idempotency:** Sequenced streams (`input`, `camera`, `telemetry`) use `ON CONFLICT DO NOTHING` on `UNIQUE(session_id, stream, seq)`. Sparse streams are naturally idempotent via UUID event IDs.

**Status transitions** are validated server-side against an explicit allowlist (`created → uploading → processing → review → approved/rejected`, with `failed` reachable from any non-terminal state).

# Real-Time Session Ingestion & Monitoring

## Prerequisites

- Docker Desktop

## Start the stack

```bash
docker compose up --build
```

This starts PostgreSQL, the backend API, the Next.js dashboard, and the simulator. Open the dashboard at `http://localhost:3000`.

The simulator runs all three scenarios by default. To re-run it or run a specific scenario, click the **Play (▶)** button on the **client** container in Docker Desktop, or:

```bash
docker compose run --rm client
```

**Scenarios** (default: `all`):

| Scenario | What happens |
|---|---|
| `all` | Runs all three scenarios back-to-back |
| `happy_path` | Uploading → processing → review → approved |
| `rejected` | Degraded streams → quality fails → rejected |
| `pipeline_failure` | Transcode fails at 45% → failed |

```bash
SCENARIO=happy_path docker compose run --rm client
SCENARIO=rejected docker compose run --rm client
SCENARIO=pipeline_failure docker compose run --rm client
```

## API

- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Tests

Integration tests run against a real PostgreSQL database (`sessions_test`), which is created automatically on first `docker compose up --build`.

Start the stack, then in a separate terminal:

```bash
docker compose exec backend pytest
```

To run a specific test file:

```bash
docker compose exec backend pytest tests/test_ingestion.py
docker compose exec backend pytest tests/test_status_transitions.py
docker compose exec backend pytest tests/test_sessions.py
```

To run with verbose output:

```bash
docker compose exec backend pytest -v
```

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

---

## Failure Handling

**Client disconnection:** The simulator uses exponential backoff (up to 8 retries) to reconnect and resume the stream. `seq` numbers let the backend detect and silently drop any events the client re-sends after reconnecting.

**Duplicate events:** `INSERT ... ON CONFLICT DO NOTHING` on `UNIQUE(session_id, stream, seq)` makes sequenced stream writes fully idempotent. The backend uses `RETURNING` to distinguish a real insert from a conflict without a second round-trip.

**Malformed events:** Each line in the NDJSON stream is parsed independently. A `json.JSONDecodeError` on one line is caught and skipped — the connection stays open and subsequent events are processed normally.

**DB errors mid-stream:** Any exception from `ingest_event` triggers a `db.rollback()` for that event only. The streaming connection continues; no events are lost from other lines in the buffer.

**Buffer overflow:** If a client sends a body with no newlines, the buffer is capped at 10 MB before the connection is dropped with a 400.

**Unknown session:** The backend validates session existence before reading the stream body, returning 404 immediately rather than failing on the first INSERT.

**Backend restart:** The simulator's retry loop reconnects automatically. The browser's `EventSource` reconnects to SSE endpoints on its own. No session state is lost since everything is persisted to PostgreSQL before broadcasting.

**Stream stalls:** The dashboard marks a stream as `Stalled` if its `last_seen_at` exceeds 30 seconds. For terminal sessions (`approved`, `rejected`, `failed`) streams are shown as `Completed` instead.

---

## Stretch Goals Completed

- **Pipeline stage visualization** — session status badge acts as a live stage indicator (`uploading → processing → review → approved/rejected/failed`), updating in real time via SSE.
- **Stream health heatmap** — per-stream health cards on the detail page show event count, last-seen time, stall detection, and error count with color-coded borders.
- **Activity rolling window** — the stats bar shows a live sparkline of events/sec over the last 60 seconds, updated on every SSE event.

---

## What I'd Do Differently With More Time

**Message queue for high-frequency streams.** `input` at 60 Hz and `camera` at 30 Hz each produce thousands of events per session. Right now every event is a synchronous DB write. At 500 concurrent sessions that becomes ~135k writes/sec — beyond what a single Postgres instance handles comfortably. I'd route high-frequency streams through Kafka or Redis Streams and batch-insert from workers, while sparse streams (lifecycle, quality, review) continue writing directly.

**Redis for stream health counters.** The `stream_health` upsert on every event is expensive. Moving `event_count` and `bytes_received` to Redis `HINCRBY` and syncing to Postgres every few seconds would cut DB writes roughly in half.

**Cursor-based pagination.** The session list uses offset pagination which degrades at scale. Keyset pagination on `(created_at, id)` stays O(1) regardless of table size.

**Proper TypeScript types.** Several places in the dashboard use `as Record<string, unknown>` casts to access event payloads. A discriminated union on `stream` type would give full type safety across all stream shapes.

**More test coverage.** Current integration tests cover the critical paths. I'd add: SSE event delivery assertions, stream stall detection timing, concurrent ingestion with duplicate races, and pagination edge cases.

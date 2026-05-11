import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stream_event import StreamEvent
from app.models.stream_health import StreamHealth


async def ingest_event(db: AsyncSession, session_id: uuid.UUID, raw: dict) -> StreamEvent | None:
    # SCALE: at 500 concurrent sessions with 10 streams each, this function becomes
    # the main bottleneck. Each call is 2 sequential DB round-trips (~1-2ms each on
    # a local network), so at 60 Hz input + 30 Hz camera we're already at ~270
    # writes/sec per session. At 500 sessions that's 135,000 writes/sec — well
    # beyond what a single Postgres instance handles comfortably (~10-20k writes/sec).
    #
    # To scale:
    # 1. MESSAGE QUEUE: Put high-frequency streams (input, camera) onto a queue
    #    (Kafka, SQS, Redis Streams) instead of writing directly to Postgres.
    #    A pool of workers drains the queue and bulk-inserts in batches.
    #    Sparse streams (lifecycle, quality, review) can still write directly.
    #
    # 2. BATCH WRITES: Instead of one INSERT per event, accumulate N events in an
    #    in-memory buffer per (session, stream) and flush every 100ms with a single
    #    executemany(). Drops DB round-trips by ~100x for high-frequency streams.
    #
    # 3. STREAM HEALTH: The health upsert on every event is expensive. Move it to
    #    an in-memory counter (Redis HINCRBY) and sync to Postgres every few seconds.
    #    This alone cuts DB writes in half.
    #
    # 4. PARTITIONING: Partition stream_events by session_id or received_at so
    #    Postgres can prune old data efficiently and parallelize writes across shards.
    #
    # 5. READ REPLICAS: Separate the dashboard query path (GET /events, GET /sessions)
    #    onto read replicas so ingestion writes don't compete with dashboard reads.

    stream = raw.get("stream")
    if not stream:
        return None

    seq = raw.get("seq")
    print(f"[{session_id}] {stream} seq={seq} {raw}", flush=True)

    # Insert event, returning the row so we avoid a second SELECT round-trip.
    # ON CONFLICT DO NOTHING handles duplicate retries — RETURNING gives back
    # nothing on a conflict, so scalar_one_or_none() returning None means duplicate.
    stmt = (
        insert(StreamEvent)
        .values(
            session_id=session_id,
            stream=stream,
            seq=seq,
            payload=raw,
            received_at=datetime.now(timezone.utc),
        )
    )
    if seq is not None:
        stmt = stmt.on_conflict_do_nothing(constraint="uq_stream_event_seq")

    result = await db.execute(stmt.returning(StreamEvent))
    await db.commit()

    event = result.scalar_one_or_none()
    if event is None:
        return None  # duplicate

    # Upsert stream health in the same round-trip as a single SQL statement.
    # SCALE: replace with Redis HINCRBY and sync to Postgres periodically.
    health_stmt = (
        insert(StreamHealth)
        .values(
            session_id=session_id,
            stream=stream,
            last_seen_at=datetime.now(timezone.utc),
            event_count=1,
            error_count=0,
            bytes_received=len(str(raw)),
        )
        .on_conflict_do_update(
            index_elements=["session_id", "stream"],
            set_={
                "last_seen_at": datetime.now(timezone.utc),
                "event_count": StreamHealth.event_count + 1,
                "bytes_received": StreamHealth.bytes_received + len(str(raw)),
            },
        )
    )
    await db.execute(health_stmt)
    await db.commit()

    return event


async def get_stream_health(db: AsyncSession, session_id: uuid.UUID) -> list[StreamHealth]:
    result = await db.execute(
        select(StreamHealth).where(StreamHealth.session_id == session_id)
    )
    return list(result.scalars().all())


async def list_events(
    db: AsyncSession,
    session_id: uuid.UUID,
    stream: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[StreamEvent]:
    q = (
        select(StreamEvent)
        .where(StreamEvent.session_id == session_id)
        .order_by(StreamEvent.received_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if stream:
        q = q.where(StreamEvent.stream == stream)
    result = await db.execute(q)
    return list(result.scalars().all())

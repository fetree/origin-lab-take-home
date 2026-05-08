import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stream_event import StreamEvent
from app.models.stream_health import StreamHealth


async def ingest_event(db: AsyncSession, session_id: uuid.UUID, raw: dict) -> StreamEvent | None:
    stream = raw.get("stream")
    if not stream:
        return None

    seq = raw.get("seq")

    # Insert event; skip on duplicate (session_id, stream, seq) when seq is present
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

    result = await db.execute(stmt)
    await db.commit()

    if seq is not None and result.rowcount == 0:
        return None  # duplicate

    # Upsert stream health
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

    # Return the inserted event (fetch by session+stream+received_at for simplicity)
    row = await db.execute(
        select(StreamEvent)
        .where(StreamEvent.session_id == session_id, StreamEvent.stream == stream)
        .order_by(StreamEvent.received_at.desc())
        .limit(1)
    )
    return row.scalar_one_or_none()


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

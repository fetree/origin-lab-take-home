import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stream_event import StreamEvent
from app.models.stream_health import StreamHealth


async def ingest_event(db: AsyncSession, session_id: uuid.UUID, raw: dict) -> StreamEvent | None:
    """
    Parse a raw NDJSON event, persist it, and update stream health.
    Returns None if the event was a duplicate (seq conflict).
    """
    raise NotImplementedError


async def get_stream_health(db: AsyncSession, session_id: uuid.UUID) -> list[StreamHealth]:
    raise NotImplementedError


async def list_events(
    db: AsyncSession,
    session_id: uuid.UUID,
    stream: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[StreamEvent]:
    raise NotImplementedError

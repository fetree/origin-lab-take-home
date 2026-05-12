import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session, SessionStatus
from app.models.stream_event import StreamEvent
from app.models.stream_health import StreamHealth
from app.schemas.session import SessionCreate, StatsOut


async def create_session(db: AsyncSession, data: SessionCreate) -> Session:
    session = Session(
        game_title=data.game_title,
        operator_name=data.operator_name,
        resolution=data.resolution,
        fps=data.fps,
        has_depth=data.has_depth,
        streams=data.streams,
        system_metadata=data.system_metadata,
        status=SessionStatus.created,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> Session | None:
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    status: SessionStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Session]:
    q = select(Session).order_by(Session.created_at.desc()).limit(limit).offset(offset)
    if status is not None:
        q = q.where(Session.status == status)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_status(db: AsyncSession, session_id: uuid.UUID, status: SessionStatus) -> Session | None:
    session = await get_session(db, session_id)
    if not session:
        return None
    session.status = status
    session.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session


async def get_stats(db: AsyncSession) -> StatsOut:
    total = await db.scalar(select(func.count()).select_from(Session))

    rows = await db.execute(select(Session.status, func.count()).group_by(Session.status))
    by_status = {row[0].value: row[1] for row in rows}

    # Events received in the last 10 seconds → events/sec
    window_start = datetime.now(timezone.utc) - timedelta(seconds=10)
    recent = await db.scalar(
        select(func.count()).select_from(StreamEvent)
        .where(StreamEvent.received_at >= window_start)
    )
    events_per_second = round((recent or 0) / 10.0, 2)

    # Error rate: total errors across all streams / total events
    total_events = await db.scalar(select(func.count()).select_from(StreamEvent)) or 1
    total_errors = await db.scalar(select(func.sum(StreamHealth.error_count)).select_from(StreamHealth)) or 0
    error_rate = round(total_errors / total_events, 4)

    return StatsOut(
        total_sessions=total or 0,
        by_status=by_status,
        events_per_second=events_per_second,
        error_rate=error_rate,
    )

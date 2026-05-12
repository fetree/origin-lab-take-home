import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.session import SessionStatus
from app.models.stream_health import StreamHealth
from app.schemas.session import SessionCreate, SessionListOut, SessionOut, SessionStatusUpdate, StatsOut
from app.services import ingestion_service, session_service
from app.services.realtime_service import realtime

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _session_out(session, db: AsyncSession) -> SessionOut:
    health = await ingestion_service.get_stream_health(db, session.id)
    return SessionOut.model_validate({**session.__dict__, "stream_health": health})


def _session_global_payload(session) -> dict:
    return {
        "type": "session_updated",
        "session_id": str(session.id),
        "status": session.status.value,
        "game_title": session.game_title,
        "operator_name": session.operator_name,
        "updated_at": session.updated_at.isoformat(),
    }


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = await session_service.create_session(db, body)
    await realtime.publish_global({
        "type": "session_created",
        "session_id": str(session.id),
        "status": session.status.value,
        "game_title": session.game_title,
        "operator_name": session.operator_name,
        "created_at": session.created_at.isoformat(),
    })
    return await _session_out(session, db)


@router.get("/stats", response_model=StatsOut)
async def get_stats(db: AsyncSession = Depends(get_db)):
    return await session_service.get_stats(db)


@router.get("", response_model=list[SessionListOut])
async def list_sessions(
    status: SessionStatus | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    sessions = await session_service.list_sessions(db, status=status, limit=limit, offset=offset)
    if not sessions:
        return []

    # Batch-fetch stream health for all sessions in one query
    session_ids = [s.id for s in sessions]
    health_rows = await db.execute(
        select(StreamHealth).where(StreamHealth.session_id.in_(session_ids))
    )
    health_map: dict[str, list] = {}
    for h in health_rows.scalars():
        key = str(h.session_id)
        health_map.setdefault(key, []).append(h)

    return [
        SessionListOut.model_validate({**s.__dict__, "stream_health": health_map.get(str(s.id), [])})
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    session = await session_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await _session_out(session, db)


@router.patch("/{session_id}/status", response_model=SessionOut)
async def update_status(session_id: uuid.UUID, body: SessionStatusUpdate, db: AsyncSession = Depends(get_db)):
    session = await session_service.update_status(db, session_id, body.status)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await realtime.publish_global(_session_global_payload(session))
    await realtime.publish(session_id, {"type": "status_updated", "status": session.status.value})
    return await _session_out(session, db)

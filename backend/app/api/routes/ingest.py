import json
import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.events import StreamEventOut
from app.services import ingestion_service
from app.services.realtime_service import realtime

router = APIRouter(prefix="/sessions", tags=["ingest"])


@router.post("/{session_id}/stream", status_code=status.HTTP_204_NO_CONTENT)
async def ingest_stream(session_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)):
    buffer = b""
    async for chunk in request.stream():
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except Exception:
                continue

            event = await ingestion_service.ingest_event(db, session_id, raw)
            if not event:
                continue

            # Fetch updated health for this stream and broadcast both together.
            # Dashboard detail view uses "event" to append to timeline and
            # "health" to refresh the per-stream health card.
            health = await ingestion_service.get_stream_health(db, session_id)
            health_payload = [
                {
                    "stream": h.stream,
                    "last_seen_at": h.last_seen_at.isoformat() if h.last_seen_at else None,
                    "event_count": h.event_count,
                    "error_count": h.error_count,
                    "bytes_received": h.bytes_received,
                }
                for h in health
            ]

            await realtime.publish(session_id, {
                "type": "event",
                "stream": event.stream,
                "seq": event.seq,
                "received_at": event.received_at.isoformat(),
                "data": raw,
                "health": health_payload,
            })


@router.get("/{session_id}/events", response_model=list[StreamEventOut])
async def list_events(
    session_id: uuid.UUID,
    stream: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await ingestion_service.list_events(db, session_id, stream=stream, limit=limit, offset=offset)

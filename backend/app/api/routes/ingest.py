import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.events import StreamEventOut
from app.services import ingestion_service
from app.services.realtime_service import realtime

router = APIRouter(prefix="/sessions", tags=["ingest"])


@router.post("/{session_id}/stream", status_code=status.HTTP_204_NO_CONTENT)
async def ingest_stream(session_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Long-lived streaming ingest endpoint.
    Client sends newline-delimited JSON (NDJSON) over the request body.
    Each line is parsed and persisted as a stream event.
    """
    buffer = b""
    async for chunk in request.stream():
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                import json
                raw = json.loads(line)
            except Exception:
                continue  # malformed line; skip
            event = await ingestion_service.ingest_event(db, session_id, raw)
            if event:
                await realtime.publish(session_id, {"type": "event", "data": raw})


@router.get("/{session_id}/events", response_model=list[StreamEventOut])
async def list_events(
    session_id: uuid.UUID,
    stream: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await ingestion_service.list_events(db, session_id, stream=stream, limit=limit, offset=offset)

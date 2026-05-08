import asyncio
import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.realtime_service import realtime

router = APIRouter(tags=["realtime"])


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _session_event_generator(session_id: uuid.UUID):
    async for event in realtime.stream(session_id):
        yield _sse(event)
        await asyncio.sleep(0)  # yield control


async def _global_event_generator():
    async for event in realtime.stream_global():
        yield _sse(event)
        await asyncio.sleep(0)


@router.get("/sessions/stream")
async def sessions_stream():
    """SSE: broadcasts new sessions and status changes to dashboard list view."""
    return StreamingResponse(
        _global_event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions/{session_id}/stream")
async def session_detail_stream(session_id: uuid.UUID):
    """SSE: broadcasts stream events and health updates for a specific session."""
    return StreamingResponse(
        _session_event_generator(session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

import asyncio
import uuid
from collections import defaultdict
from typing import AsyncGenerator


class RealtimeService:
    """
    In-process pub/sub for SSE fan-out.
    Subscribers register a queue; ingestion publishes events to all queues for a session.
    """

    def __init__(self) -> None:
        # session_id -> set of queues (one per connected SSE client)
        self._queues: dict[str, set[asyncio.Queue]] = defaultdict(set)
        # global queue for session-list updates
        self._global_queues: set[asyncio.Queue] = set()

    def subscribe(self, session_id: uuid.UUID) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._queues[str(session_id)].add(q)
        return q

    def unsubscribe(self, session_id: uuid.UUID, q: asyncio.Queue) -> None:
        self._queues[str(session_id)].discard(q)

    def subscribe_global(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._global_queues.add(q)
        return q

    def unsubscribe_global(self, q: asyncio.Queue) -> None:
        self._global_queues.discard(q)

    async def publish(self, session_id: uuid.UUID, event: dict) -> None:
        for q in list(self._queues.get(str(session_id), [])):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # slow client; drop event rather than block ingestion

    async def publish_global(self, event: dict) -> None:
        for q in list(self._global_queues):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def stream(self, session_id: uuid.UUID) -> AsyncGenerator[dict, None]:
        q = self.subscribe(session_id)
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            self.unsubscribe(session_id, q)

    async def stream_global(self) -> AsyncGenerator[dict, None]:
        q = self.subscribe_global()
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            self.unsubscribe_global(q)


realtime = RealtimeService()

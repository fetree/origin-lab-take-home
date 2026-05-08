"""
HTTP transport for the simulator.
- create_session: POST /sessions → returns session_id
- stream_events: long-lived streaming POST /sessions/{id}/stream (NDJSON body)
  Reconnects automatically on failure with exponential backoff.
"""

import asyncio
import json
import logging
import uuid
from asyncio import Queue
from collections.abc import AsyncGenerator
from typing import Any

import httpx

logger = logging.getLogger(__name__)

MAX_RETRIES = 8
BASE_BACKOFF = 1.0


async def create_session(api_url: str, payload: dict) -> uuid.UUID:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{api_url}/sessions", json=payload)
        resp.raise_for_status()
        return uuid.UUID(resp.json()["id"])


async def update_status(api_url: str, session_id: uuid.UUID, status: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.patch(
            f"{api_url}/sessions/{session_id}/status",
            json={"status": status},
        )
        resp.raise_for_status()


async def stream_events(
    api_url: str,
    session_id: uuid.UUID,
    events: AsyncGenerator[dict, None],
) -> None:
    """
    Consume `events` and write each as a newline-terminated JSON line to a
    streaming POST.  Reconnects on network failure; the backend deduplicates
    by (stream, seq) so replaying events on reconnect is safe.
    """
    # Buffer events from the generator into a queue so we can reconnect
    # without losing events that were produced but not yet sent.
    send_queue: Queue[dict | None] = Queue(maxsize=1024)

    async def _produce() -> None:
        async for event in events:
            await send_queue.put(event)
        await send_queue.put(None)  # sentinel

    async def _body() -> AsyncGenerator[bytes, None]:
        while True:
            event = await send_queue.get()
            if event is None:
                return
            yield (json.dumps(event) + "\n").encode()

    producer_task = asyncio.create_task(_produce())

    attempt = 0
    while True:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{api_url}/sessions/{session_id}/stream",
                    content=_body(),
                    headers={"Content-Type": "application/x-ndjson"},
                ) as resp:
                    resp.raise_for_status()
                    # Drain response (204 No Content, nothing to read)
                    async for _ in resp.aiter_bytes():
                        pass
            break  # clean finish
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            attempt += 1
            if attempt > MAX_RETRIES:
                logger.error("Giving up after %d retries: %s", MAX_RETRIES, exc)
                producer_task.cancel()
                raise
            wait = BASE_BACKOFF * (2 ** (attempt - 1))
            logger.warning("Connection lost (%s), reconnecting in %.1fs …", exc, wait)
            await asyncio.sleep(wait)

    await producer_task

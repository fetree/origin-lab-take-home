"""Merge multiple async generators into one, interleaved by arrival order."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

_DONE = object()


async def merge(*generators: AsyncGenerator[Any, None]) -> AsyncGenerator[Any, None]:
    queue: asyncio.Queue = asyncio.Queue()

    async def drain(gen: AsyncGenerator) -> None:
        async for item in gen:
            await queue.put(item)
        await queue.put(_DONE)

    tasks = [asyncio.create_task(drain(g)) for g in generators]
    remaining = len(tasks)

    while remaining > 0:
        item = await queue.get()
        if item is _DONE:
            remaining -= 1
        else:
            yield item

    for t in tasks:
        await t

import asyncio
from collections.abc import AsyncGenerator


async def lifecycle_stream(duration_s: float, speed: float = 1.0) -> AsyncGenerator[dict, None]:
    yield {"stream": "lifecycle", "type": "session_start", "elapsed_ms": 0}
    await asyncio.sleep(duration_s * 0.5 / speed)
    yield {"stream": "lifecycle", "type": "upload_start", "elapsed_ms": int(duration_s * 500)}

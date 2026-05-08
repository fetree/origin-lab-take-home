import asyncio
import random
from collections.abc import AsyncGenerator


async def audio_stream(
    duration_s: float,
    speed: float = 1.0,
    clipping_ratio: float = 0.0,
) -> AsyncGenerator[dict, None]:
    interval = 1.0 / speed
    seq = 0
    elapsed_ms = 0
    end = duration_s / speed
    t = 0.0

    while t < end:
        await asyncio.sleep(interval)
        t += interval
        seq += 1
        elapsed_ms += 1000

        clipping = random.random() < clipping_ratio
        peak_db = random.uniform(-1.0, 0.5) if clipping else random.uniform(-18, -6)

        yield {
            "stream": "audio_levels",
            "seq": seq,
            "elapsed_ms": elapsed_ms,
            "rms_db": round(peak_db - random.uniform(8, 14), 1),
            "peak_db": round(peak_db, 1),
            "clipping": clipping,
            "noise_floor_db": round(random.uniform(-50, -45), 1),
        }

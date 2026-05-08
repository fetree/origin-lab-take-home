import asyncio
import random
from collections.abc import AsyncGenerator


async def telemetry_stream(
    duration_s: float,
    speed: float = 1.0,
    fps: float = 59.5,
    drop_frames: bool = False,
) -> AsyncGenerator[dict, None]:
    interval = 3.0 / speed
    seq = 0
    elapsed_ms = 0
    end = duration_s / speed

    t = 0.0
    while t < end:
        await asyncio.sleep(interval)
        t += interval
        seq += 1
        elapsed_ms += 3000
        yield {
            "stream": "telemetry",
            "seq": seq,
            "elapsed_ms": elapsed_ms,
            "recording_fps": round(fps + random.uniform(-1, 1), 1),
            "gpu_usage_percent": random.randint(60, 90),
            "cpu_usage_percent": random.randint(30, 55),
            "ram_used_bytes": random.randint(16_000_000_000, 20_000_000_000),
            "dropped_frames": random.randint(5, 30) if drop_frames else 0,
            "bitrate_kbps": random.randint(40_000, 50_000),
            "encoder_lag_ms": round(random.uniform(1.0, 4.0), 1),
        }

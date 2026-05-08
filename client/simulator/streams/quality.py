import asyncio
from collections.abc import AsyncGenerator


async def quality_stream(
    avg_fps: float = 59.2,
    inactivity_ratio: float = 0.05,
    audio_clipping_ratio: float = 0.04,
    depth_coverage: float = 0.97,
    speed: float = 1.0,
) -> AsyncGenerator[dict, None]:
    await asyncio.sleep(1.0 / speed)

    metrics = [
        {
            "stream": "quality",
            "metric": "avg_fps",
            "value": avg_fps,
            "threshold": 30,
            "pass": avg_fps >= 30,
        },
        {
            "stream": "quality",
            "metric": "inactivity_ratio",
            "value": inactivity_ratio,
            "threshold": 0.15,
            "pass": inactivity_ratio <= 0.15,
            "detail": "3 gaps: 2:10-3:45, 7:00-8:12, 14:30-15:00" if inactivity_ratio > 0.15 else None,
        },
        {
            "stream": "quality",
            "metric": "audio_clipping_ratio",
            "value": audio_clipping_ratio,
            "threshold": 0.10,
            "pass": audio_clipping_ratio <= 0.10,
        },
        {
            "stream": "quality",
            "metric": "depth_coverage",
            "value": depth_coverage,
            "threshold": 0.80,
            "pass": depth_coverage >= 0.80,
        },
    ]
    for m in metrics:
        yield {k: v for k, v in m.items() if v is not None}
        await asyncio.sleep(0.1 / speed)

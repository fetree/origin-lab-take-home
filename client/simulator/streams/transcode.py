import asyncio
import random
from collections.abc import AsyncGenerator


async def transcode_stream(
    duration_s: float,
    speed: float = 1.0,
    fail_at: float | None = None,  # fail when progress reaches this percent (0-100)
) -> AsyncGenerator[dict, None]:
    interval = 3.0 / speed
    pct = 0.0
    output_mb = 0.0
    end = duration_s / speed
    t = 0.0

    for rendition in ("360p", "720p"):
        pct = 0.0
        while pct < 100:
            await asyncio.sleep(interval)
            t += interval
            pct = min(100.0, pct + random.uniform(8, 15))
            output_mb += random.uniform(30, 60)

            if fail_at is not None and pct >= fail_at:
                yield {
                    "stream": "transcode",
                    "stage": "failed",
                    "error": "FFmpeg exit code 1: moov atom not found",
                    "failed_at": "mp4_remux",
                    "input_file": "screen.mkv",
                    "retry_count": 2,
                }
                return

            yield {
                "stream": "transcode",
                "stage": "hls_rendition",
                "rendition": rendition,
                "percent": round(pct, 1),
                "output_size_mb": round(output_mb, 1),
                "processing_speed": f"{round(random.uniform(2.0, 3.0), 1)}x",
            }

    yield {
        "stream": "transcode",
        "stage": "complete",
        "duration_seconds": duration_s,
        "output_size_mb": round(output_mb, 1),
        "processing_time_seconds": round(t * speed, 1),
        "hls_renditions_completed": ["360p", "720p"],
        "depth_frames_extracted": 110838,
    }

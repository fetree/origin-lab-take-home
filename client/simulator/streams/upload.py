import asyncio
import random
from collections.abc import AsyncGenerator

FILES = [
    ("screen.mp4", 2048.0),
    ("webcam.mp4", 340.0),
    ("audio.wav", 120.0),
    ("input_log.msgpack", 2.0),
    ("depth.oldpblob", 1690.0),
]


async def upload_stream(
    duration_s: float,
    speed: float = 1.0,
    fail_file: str | None = None,
) -> AsyncGenerator[dict, None]:
    interval = 2.0 / speed
    chunk_size_mb = 100.0

    for filename, total_mb in FILES:
        uploaded = 0.0
        chunk_index = 0
        total_chunks = int(total_mb / chunk_size_mb) + 1

        while uploaded < total_mb:
            await asyncio.sleep(interval)
            chunk = min(chunk_size_mb, total_mb - uploaded)
            uploaded += chunk
            chunk_index += 1
            pct = round(uploaded / total_mb * 100, 1)

            payload: dict = {
                "stream": "upload",
                "file": filename,
                "bytes_uploaded": int(uploaded * 1024 * 1024),
                "total_bytes": int(total_mb * 1024 * 1024),
                "percent": pct,
                "upload_speed_mbps": round(random.uniform(40, 55), 1),
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
            }

            if uploaded >= total_mb:
                if filename == fail_file:
                    payload["error"] = "upload failed: connection reset"
                    yield payload
                    return
                payload["completed"] = True
                payload["checksum"] = f"sha256:{'a1b2c3d4e5f6'[:6]}{chunk_index:04x}"
            yield payload

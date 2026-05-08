import asyncio
import random
from collections.abc import AsyncGenerator


async def camera_stream(
    duration_s: float,
    speed: float = 1.0,
    hz: int = 30,
) -> AsyncGenerator[dict, None]:
    interval = (1.0 / hz) / speed
    seq = 0
    px, py, pz = 1500.0, 2000.0, 500.0
    yaw = 90.0
    end = duration_s / speed
    t = 0.0

    while t < end:
        await asyncio.sleep(interval)
        t += interval
        seq += 1

        px += random.uniform(-2, 2)
        py += random.uniform(-2, 2)
        yaw = (yaw + random.uniform(-5, 5)) % 360

        yield {
            "stream": "camera",
            "seq": seq,
            "t": round(t * speed, 2),
            "frame": seq,
            "px": round(px, 2),
            "py": round(py, 2),
            "pz": round(pz, 2),
            "pitch": round(random.uniform(30, 60), 1),
            "yaw": round(yaw, 1),
            "roll": 0.0,
            "fov": 90.0,
            "vx": round(random.uniform(-15, 15), 2),
            "vy": round(random.uniform(-15, 15), 2),
            "vz": 0.0,
            "map_name": "Gorodok",
        }

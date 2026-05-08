import asyncio
import random
from collections.abc import AsyncGenerator

KEYS = ["w", "a", "s", "d", "space", "shift", "r", "f"]
EVENT_TYPES = ["key_down", "key_up", "mouse_move", "scroll"]


async def input_stream(
    duration_s: float,
    speed: float = 1.0,
    hz: int = 60,
    inactivity_ratio: float = 0.0,
) -> AsyncGenerator[dict, None]:
    interval = (1.0 / hz) / speed
    seq = 0
    t_us = 0
    end = duration_s / speed
    t = 0.0

    while t < end:
        await asyncio.sleep(interval)
        t += interval
        seq += 1
        t_us += int(1_000_000 / hz)

        # simulate inactivity gaps
        if random.random() < inactivity_ratio:
            continue

        event_type = random.choice(EVENT_TYPES)
        event: dict = {"stream": "input", "seq": seq, "t_us": t_us, "type": event_type}

        if event_type in ("key_down", "key_up"):
            event["key"] = random.choice(KEYS)
        elif event_type == "mouse_move":
            event.update({"x": random.randint(0, 2560), "y": random.randint(0, 1440),
                           "dx": random.randint(-20, 20), "dy": random.randint(-20, 20)})
        else:
            event.update({"x": 960, "y": 540, "dx": 0, "dy": random.choice([-3, 3])})

        yield event

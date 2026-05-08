"""
Happy path: all streams active, upload succeeds, transcode completes,
quality passes, reviewer approves.
"""

import asyncio

from simulator.streams.audio import audio_stream
from simulator.streams.camera import camera_stream
from simulator.streams.input_events import input_stream
from simulator.streams.lifecycle import lifecycle_stream
from simulator.streams.merge import merge
from simulator.streams.quality import quality_stream
from simulator.streams.review import review_stream
from simulator.streams.telemetry import telemetry_stream
from simulator.streams.transcode import transcode_stream
from simulator.streams.upload import upload_stream
from simulator import transport

SESSION_PAYLOAD = {
    "game_title": "Squad",
    "operator_name": "jake_m",
    "resolution": "2560x1440",
    "fps": 60,
    "has_depth": True,
    "streams": ["screen_video", "webcam_video", "audio", "input_log", "depth_frames"],
    "system_metadata": {
        "obs": {"output_width": 2560, "output_height": 1440, "fps_numerator": 60000,
                "fps_denominator": 1001, "obs_version": "31.0.0"},
        "hardware": {"cpu_model": "Intel Core i9-13900K", "cpu_cores_physical": 24,
                     "ram_total_bytes": 34359738368, "gpu": "RTX 4080", "os_version": "Windows 11 26100"},
        "game_name": "Squad", "map": "Gorodok",
        "encoder": "NVENC HEVC", "recorder_version": "2.4.1",
    },
}


async def run(api_url: str, speed: float = 10.0) -> None:
    print("[happy_path] Creating session …")
    session_id = await transport.create_session(api_url, SESSION_PAYLOAD)
    print(f"[happy_path] Session created: {session_id}")

    duration = 60.0  # simulated seconds of capture

    streams = merge(
        lifecycle_stream(duration, speed),
        telemetry_stream(duration, speed),
        upload_stream(duration, speed),
        input_stream(duration, speed, hz=60),
        camera_stream(duration, speed, hz=30),
        audio_stream(duration, speed),
        transcode_stream(duration, speed),
        quality_stream(speed=speed),
        review_stream("approved", speed=speed),
    )

    print("[happy_path] Streaming events …")
    await transport.stream_events(api_url, session_id, streams)
    await transport.update_status(api_url, session_id, "approved")
    print("[happy_path] Done — session approved.")

"""
Rejected session: low FPS (frequent dropped frames), high inactivity,
audio clipping — quality metrics fail, reviewer rejects.
"""

from simulator.streams.audio import audio_stream
from simulator.streams.camera import camera_stream
from simulator.streams.input_events import input_stream
from simulator.streams.lifecycle import lifecycle_stream
from simulator.streams.merge import merge
from simulator.streams.quality import quality_stream
from simulator.streams.review import review_stream
from simulator.streams.telemetry import telemetry_stream
from simulator.streams.upload import upload_stream
from simulator import transport

SESSION_PAYLOAD = {
    "game_title": "Squad",
    "operator_name": "degraded_op",
    "resolution": "1920x1080",
    "fps": 60,
    "has_depth": False,
    "streams": ["screen_video", "audio", "input_log"],
    "system_metadata": {
        "hardware": {"cpu_model": "Intel Core i5-8600K", "gpu": "GTX 1060",
                     "ram_total_bytes": 17179869184, "os_version": "Windows 10"},
        "game_name": "Squad", "encoder": "x264", "recorder_version": "2.3.0",
    },
}


async def run(api_url: str, speed: float = 10.0) -> None:
    print("[rejected] Creating session …")
    session_id = await transport.create_session(api_url, SESSION_PAYLOAD)
    print(f"[rejected] Session created: {session_id}")

    duration = 60.0

    streams = merge(
        lifecycle_stream(duration, speed),
        telemetry_stream(duration, speed, fps=18.0, drop_frames=True),
        upload_stream(duration, speed),
        input_stream(duration, speed, hz=30, inactivity_ratio=0.25),
        camera_stream(duration, speed, hz=15),
        audio_stream(duration, speed, clipping_ratio=0.15),
        quality_stream(avg_fps=18.0, inactivity_ratio=0.22, audio_clipping_ratio=0.15,
                       depth_coverage=0.0, speed=speed),
        review_stream(
            "rejected",
            rejection_reason="Frame drops below 20fps for 4+ minutes, excessive inactivity (22%). Not suitable for training data.",
            speed=speed,
        ),
    )

    print("[rejected] Streaming events …")
    await transport.stream_events(api_url, session_id, streams)
    await transport.update_status(api_url, session_id, "rejected")
    print("[rejected] Done — session rejected.")

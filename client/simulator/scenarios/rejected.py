"""
Rejected: uploading → processing → review → rejected (quality fails)
"""
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
    print(f"[rejected] Session: {session_id}")

    # Phase 1: uploading (degraded streams)
    print("[rejected] uploading …")
    await transport.update_status(api_url, session_id, "uploading")
    await transport.stream_events(api_url, session_id, merge(
        lifecycle_stream(60.0, speed),
        telemetry_stream(60.0, speed, fps=18.0, drop_frames=True),
        upload_stream(60.0, speed),
        input_stream(60.0, speed, hz=30, inactivity_ratio=0.25),
        camera_stream(60.0, speed, hz=15),
        audio_stream(60.0, speed, clipping_ratio=0.15),
    ))

    # Phase 2: processing
    print("[rejected] processing …")
    await transport.update_status(api_url, session_id, "processing")
    await transport.stream_events(api_url, session_id, transcode_stream(30.0, speed))

    # Phase 3: review (quality fails → rejected)
    print("[rejected] review …")
    await transport.update_status(api_url, session_id, "review")
    await transport.stream_events(api_url, session_id, merge(
        quality_stream(avg_fps=18.0, inactivity_ratio=0.22, audio_clipping_ratio=0.15,
                       depth_coverage=0.0, speed=speed),
        review_stream(
            "rejected",
            rejection_reason="Frame drops below 20fps for 4+ minutes, excessive inactivity (22%). Not suitable for training data.",
            speed=speed,
        ),
    ))

    await transport.update_status(api_url, session_id, "rejected")
    print("[rejected] Done — session rejected.")

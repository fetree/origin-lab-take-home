"""
Pipeline failure: uploading → processing → failed (transcode error at 45%)
"""
from simulator.streams.audio import audio_stream
from simulator.streams.camera import camera_stream
from simulator.streams.input_events import input_stream
from simulator.streams.lifecycle import lifecycle_stream
from simulator.streams.merge import merge
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
    "streams": ["screen_video", "webcam_video", "audio", "input_log"],
    "system_metadata": {
        "hardware": {"cpu_model": "Intel Core i9-13900K", "gpu": "RTX 4080",
                     "ram_total_bytes": 34359738368, "os_version": "Windows 11"},
        "game_name": "Squad", "encoder": "NVENC HEVC", "recorder_version": "2.4.1",
    },
}


async def run(api_url: str, speed: float = 10.0) -> None:
    print("[pipeline_failure] Creating session …")
    session_id = await transport.create_session(api_url, SESSION_PAYLOAD)
    print(f"[pipeline_failure] Session: {session_id}")

    # Phase 1: uploading
    print("[pipeline_failure] uploading …")
    await transport.update_status(api_url, session_id, "uploading")
    await transport.stream_events(api_url, session_id, merge(
        lifecycle_stream(60.0, speed),
        telemetry_stream(60.0, speed),
        upload_stream(60.0, speed),
        input_stream(60.0, speed, hz=60),
        camera_stream(60.0, speed, hz=30),
        audio_stream(60.0, speed),
    ))

    # Phase 2: processing — transcode fails at 45%
    print("[pipeline_failure] processing …")
    await transport.update_status(api_url, session_id, "processing")
    await transport.stream_events(api_url, session_id, transcode_stream(30.0, speed, fail_at=45.0))

    await transport.update_status(api_url, session_id, "failed")
    print("[pipeline_failure] Done — session failed (transcode error).")

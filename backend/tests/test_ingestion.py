import json
import pytest
from tests.conftest import SESSION_PAYLOAD


def ndjson(*events: dict) -> bytes:
    return b"".join(json.dumps(e).encode() + b"\n" for e in events)


@pytest.mark.asyncio
async def test_ingest_single_event(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    event = {"stream": "telemetry", "seq": 1, "recording_fps": 59.2, "gpu_usage_percent": 78}
    res = await client.post(
        f"/sessions/{session_id}/stream",
        content=ndjson(event),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_ingest_multiple_streams(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    events = [
        {"stream": "telemetry", "seq": 1, "recording_fps": 59.2, "gpu_usage_percent": 78},
        {"stream": "input", "seq": 1, "type": "key_down", "key": "w"},
        {"stream": "input", "seq": 2, "type": "mouse_move", "x": 960, "y": 540},
        {"stream": "camera", "seq": 1, "px": 1500.5, "py": 2000.3, "pz": 500.1, "yaw": 90.0},
        {"stream": "lifecycle", "type": "upload_complete"},
    ]
    res = await client.post(
        f"/sessions/{session_id}/stream",
        content=ndjson(*events),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert res.status_code == 204

    # verify all streams were recorded
    res = await client.get(f"/sessions/{session_id}/events")
    streams_seen = {e["stream"] for e in res.json()}
    assert streams_seen == {"telemetry", "input", "camera", "lifecycle"}


@pytest.mark.asyncio
async def test_ingest_duplicate_events_are_deduplicated(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    event = {"stream": "input", "seq": 42, "type": "key_down", "key": "w"}

    # send the same event twice (simulates client retry)
    for _ in range(3):
        await client.post(
            f"/sessions/{session_id}/stream",
            content=ndjson(event),
            headers={"Content-Type": "application/octet-stream"},
        )

    res = await client.get(f"/sessions/{session_id}/events?stream=input")
    assert len(res.json()) == 1, "duplicate events should be deduplicated"


@pytest.mark.asyncio
async def test_ingest_updates_stream_health(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    events = [
        {"stream": "telemetry", "seq": i, "recording_fps": 59.2}
        for i in range(5)
    ]
    await client.post(
        f"/sessions/{session_id}/stream",
        content=ndjson(*events),
        headers={"Content-Type": "application/octet-stream"},
    )

    res = await client.get(f"/sessions/{session_id}")
    health = {h["stream"]: h for h in res.json()["stream_health"]}
    assert "telemetry" in health
    assert health["telemetry"]["event_count"] == 5


@pytest.mark.asyncio
async def test_ingest_unknown_session_returns_404(client):
    event = {"stream": "telemetry", "seq": 1, "recording_fps": 59.2}
    res = await client.post(
        "/sessions/00000000-0000-0000-0000-000000000000/stream",
        content=ndjson(event),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_ingest_malformed_json_is_skipped(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    # mix of malformed and valid lines
    body = b"not valid json\n" + json.dumps({"stream": "lifecycle", "type": "start"}).encode() + b"\n"
    res = await client.post(
        f"/sessions/{session_id}/stream",
        content=body,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert res.status_code == 204

    res = await client.get(f"/sessions/{session_id}/events")
    assert len(res.json()) == 1  # only the valid event was stored


@pytest.mark.asyncio
async def test_ingest_events_queryable_by_stream(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    events = [
        {"stream": "input", "seq": 1, "type": "key_down", "key": "w"},
        {"stream": "input", "seq": 2, "type": "key_up", "key": "w"},
        {"stream": "telemetry", "seq": 1, "recording_fps": 59.2},
    ]
    await client.post(
        f"/sessions/{session_id}/stream",
        content=ndjson(*events),
        headers={"Content-Type": "application/octet-stream"},
    )

    res = await client.get(f"/sessions/{session_id}/events?stream=input")
    data = res.json()
    assert len(data) == 2
    assert all(e["stream"] == "input" for e in data)

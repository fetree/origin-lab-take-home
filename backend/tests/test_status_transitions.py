import pytest
from tests.conftest import SESSION_PAYLOAD


@pytest.mark.asyncio
async def test_valid_transition_created_to_uploading(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    res = await client.patch(f"/sessions/{session_id}/status", json={"status": "uploading"})
    assert res.status_code == 200
    assert res.json()["status"] == "uploading"


@pytest.mark.asyncio
async def test_full_happy_path_transitions(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    for status in ("uploading", "processing", "review", "approved"):
        res = await client.patch(f"/sessions/{session_id}/status", json={"status": status})
        assert res.status_code == 200, f"transition to {status} failed: {res.text}"
        assert res.json()["status"] == status


@pytest.mark.asyncio
async def test_full_rejected_path_transitions(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    for status in ("uploading", "processing", "review", "rejected"):
        res = await client.patch(f"/sessions/{session_id}/status", json={"status": status})
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_failed_from_uploading(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    await client.patch(f"/sessions/{session_id}/status", json={"status": "uploading"})
    res = await client.patch(f"/sessions/{session_id}/status", json={"status": "failed"})
    assert res.status_code == 200
    assert res.json()["status"] == "failed"


@pytest.mark.asyncio
async def test_invalid_transition_is_rejected(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    # created → approved is not a valid transition
    res = await client.patch(f"/sessions/{session_id}/status", json={"status": "approved"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_terminal_state_cannot_transition(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    for status in ("uploading", "processing", "review", "approved"):
        await client.patch(f"/sessions/{session_id}/status", json={"status": status})

    # approved → uploading is not allowed
    res = await client.patch(f"/sessions/{session_id}/status", json={"status": "uploading"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_status_update_not_found(client):
    res = await client.patch(
        "/sessions/00000000-0000-0000-0000-000000000000/status",
        json={"status": "uploading"},
    )
    assert res.status_code == 404

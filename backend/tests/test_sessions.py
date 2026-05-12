import pytest
from tests.conftest import SESSION_PAYLOAD


@pytest.mark.asyncio
async def test_create_session(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    assert res.status_code == 201
    body = res.json()
    assert body["game_title"] == "CS:GO"
    assert body["operator_name"] == "jake_m"
    assert body["status"] == "created"
    assert "id" in body


@pytest.mark.asyncio
async def test_get_session(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]

    res = await client.get(f"/sessions/{session_id}")
    assert res.status_code == 200
    assert res.json()["id"] == session_id


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    res = await client.get("/sessions/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_list_sessions(client):
    await client.post("/sessions", json=SESSION_PAYLOAD)
    await client.post("/sessions", json={**SESSION_PAYLOAD, "operator_name": "other_op"})

    res = await client.get("/sessions")
    assert res.status_code == 200
    assert len(res.json()) == 2


@pytest.mark.asyncio
async def test_list_sessions_filter_by_status(client):
    res = await client.post("/sessions", json=SESSION_PAYLOAD)
    session_id = res.json()["id"]
    await client.patch(f"/sessions/{session_id}/status", json={"status": "uploading"})

    await client.post("/sessions", json={**SESSION_PAYLOAD, "operator_name": "other_op"})

    res = await client.get("/sessions?status=uploading")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["status"] == "uploading"


@pytest.mark.asyncio
async def test_stats(client):
    await client.post("/sessions", json=SESSION_PAYLOAD)

    res = await client.get("/sessions/stats")
    assert res.status_code == 200
    body = res.json()
    assert body["total_sessions"] == 1
    assert "created" in body["by_status"]
    assert "events_per_second" in body
    assert "error_rate" in body

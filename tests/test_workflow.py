import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest_asyncio.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.asyncio
async def test_submit_and_get_workflow(client):
    payload = {
        "nodes": [
            {
            "id": "fetch",
            "agent": { "type": "tool.agent", "config": {}, "timeout_sec": 15, "retries": 1 },
            "params": {
                "tool": "http.get",
                "args": { "url": "https://dummyjson.com/quotes" }
            }
            },
            {
            "id": "extract",
            "agent": { "type": "tool.agent", "config": {}, "timeout_sec": 15, "retries": 2 },
            "params": {
                "tool": "json.pick",
                "args": { "data": {"$from": "fetch", "$field": "json"}, "paths": ["title", "id"] },
                "input_from": "fetch"
            }
            }
        ],
        "edges": [
            { "source": "fetch", "target": "extract" }
        ]
    }
    response = await client.post("/workflows/", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert "run_id" in result
    assert result["status"] == "PENDING"
    
    workflow_id = result["run_id"]
    
    # Retrieve the workflow by ID
    response = await client.get(f"/workflows/{workflow_id}")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "PENDING"
    assert result["nodes"]["fetch"]["status"] == "PENDING"

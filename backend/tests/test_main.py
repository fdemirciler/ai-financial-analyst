import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import respx
from unittest.mock import patch, MagicMock

from backend.main import app

client = TestClient(app)


@pytest.fixture
def mock_llm():
    with patch("backend.llm.factory.llm_factory.create_provider") as mock_create:
        mock_provider = MagicMock()
        mock_create.return_value = mock_provider
        yield mock_provider


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "message": "Analysis Agent is running",
    }


@pytest.mark.asyncio
async def test_upload_file(mock_llm):
    session_id = "test-session"
    file_content = b"col1,col2\n1,2\n3,4"

    with respx.mock:
        # Mock the LLM response for metadata analysis
        mock_llm.generate_structured_response.return_value = {
            "tool_name": "metadata_analyzer",
            "parameters": {},
        }

        response = client.post(
            "/api/upload",
            data={"session_id": session_id},
            files={"file": ("test.csv", file_content, "text/csv")},
        )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["success"]
    assert json_response["data_shape"] == [2, 2]
    assert json_response["columns"] == ["col1", "col2"]


@pytest.mark.asyncio
async def test_chat_endpoint(mock_llm):
    session_id = "test-chat-session"

    # First, upload a file to create a session with data
    file_content = b"col1,col2\n1,2\n3,4"
    client.post(
        "/api/upload",
        data={"session_id": session_id},
        files={"file": ("test.csv", file_content, "text/csv")},
    )

    # Mock the LLM responses for planning and final response
    mock_llm.generate_structured_response.return_value = {
        "tool_name": "trend_analyzer",
        "parameters": {},
    }
    mock_llm.generate_response.return_value = "Both col1 and col2 show an increasing trend.  Col1 increased by 200%, while col2 increased by 100%."

    response = client.post(
        "/api/chat", json={"session_id": session_id, "message": "What is the trend?"}
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "increasing trend" in json_response["response"]
    assert json_response["tool_used"] == "trend_analyzer"

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


# Simple test without pandas dependency
def test_health_check():
    """Test the health check endpoint works without requiring pandas"""
    from backend.main import app

    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "message": "Analysis Agent is running",
    }


def test_config_loading():
    """Test that configuration loads properly"""
    from backend.config import settings

    # These should be loaded from the .env file
    assert settings.LLM_MODEL is not None
    assert settings.LLM_TEMPERATURE is not None
    assert settings.LLM_MAX_TOKENS is not None


def test_session_manager():
    """Test session manager basic functionality"""
    from backend.session import session_manager

    # Test creating a session
    session_id = "test-session-123"
    session_manager.create_session(session_id)

    # Test getting the session
    session = session_manager.get_session(session_id)
    assert session is not None
    assert session["data"] is None
    assert session["metadata"] is None
    assert session["conversation_history"] == []


def test_logger():
    """Test that the logger can be imported and used"""
    from backend.logger import get_logger

    logger = get_logger("test")
    assert logger is not None

    # This should not raise an exception
    logger.info("Test log message")

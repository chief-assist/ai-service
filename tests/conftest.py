"""
Pytest configuration and fixtures
"""
import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock

# Set test environment variables
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("API_KEY", "test-api-key-123")  # Match test API key
os.environ.setdefault("OLLAMA_URL", "http://localhost:11434")
os.environ.setdefault("OLLAMA_MODEL", "llava")


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response"""
    return {
        "response": '{"ingredients": [{"name": "test", "confidence": 0.9}]}',
        "done": True
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for Ollama"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llava:latest"}]}
        mock_response.raise_for_status = MagicMock()
        mock_instance.get.return_value = mock_response
        mock_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__.return_value = None
        yield mock_instance

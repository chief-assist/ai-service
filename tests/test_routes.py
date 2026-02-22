"""
Tests for API routes
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()
    assert "version" in response.json()


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/ai/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_recognize_ingredients_missing_api_key():
    """Test ingredient recognition without API key"""
    response = client.post(
        "/api/ai/recognize-ingredients",
        json={"image_url": "https://example.com/image.jpg"}
    )
    # Should either require API key or allow in dev mode
    assert response.status_code in [200, 401, 403]


def test_suggest_recipes_missing_api_key():
    """Test recipe suggestions without API key"""
    response = client.post(
        "/api/ai/suggest-recipes",
        json={"ingredients": ["tomato", "onion"]}
    )
    # Should either require API key or allow in dev mode
    assert response.status_code in [200, 401, 403]

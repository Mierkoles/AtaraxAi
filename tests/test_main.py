"""
Test main application endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "AtaraxAi" in data["message"]
    assert "version" in data


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "AtaraxAi"


def test_openapi_docs():
    """Test that OpenAPI docs are accessible."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

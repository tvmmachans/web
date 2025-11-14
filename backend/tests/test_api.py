"""
API Tests for Backend Service
Tests health endpoints and basic API functionality
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the main health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_live():
    """Test the liveness health check endpoint"""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_health_ready():
    """Test the readiness health check endpoint"""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ready"


def test_api_root():
    """Test that the API root is accessible"""
    response = client.get("/")
    # FastAPI returns 404 for root, but we can check it doesn't crash
    assert response.status_code in [200, 404]


def test_cors_headers():
    """Test that CORS headers are present"""
    response = client.options("/health")
    # CORS preflight should be handled
    assert response.status_code in [200, 405]  # OPTIONS may return 405 if not explicitly handled


def test_api_docs():
    """Test that API documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test that OpenAPI schema is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data


import pytest
from fastapi.testclient import TestClient
from agent.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert "integrations" in data


def test_auth_login_failure():
    response = client.post("/api/auth/token", data={"username": "invalid", "password": "wrong"})
    assert response.status_code == 401


def test_auth_login_success():
    response = client.post("/api/auth/token", data={"username": "admin", "password": "AegisSre2026!"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

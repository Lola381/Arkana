import pytest
from fastapi.testclient import TestClient
from ai.backend.main import app

client = TestClient(app)

def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "version": "1.0.0"}

def test_chat_validation_error():
    # Missing required query field
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"map_context": {}})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "Validation Error"
        assert "details" in data

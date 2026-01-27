from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_create_task_validation():
    # Test without files
    headers = {"X-API-Key": settings.API_KEY}
    response = client.post("/api/v1/tasks", headers=headers)
    assert response.status_code == 422  # Validation Error

def test_get_non_existent_task():
    # Only create is protected? No, the whole router is protected.
    headers = {"X-API-Key": settings.API_KEY}
    response = client.get("/api/v1/tasks/non-existent-task-id", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "unknown"

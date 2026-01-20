from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_auth_success():
    headers = {"X-API-Key": settings.API_KEY}
    # Using a non-protected endpoint to check global or specific?
    # Our dependency is only on /api/v1/tasks/
    # Let's try to access a protected route like create task (mocked) or just verify protection.
    # Since create task requires files, getting a 422 with a key is success (passed auth), gets 401 without key.
    
    # Authenticated request -> 422 (Validation Error), NOT 401
    response = client.post("/api/v1/tasks/", headers=headers)
    assert response.status_code == 422 

def test_auth_failure_no_key():
    response = client.post("/api/v1/tasks/")
    # Missing Header raises 422 Validation Error in FastAPI default
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Field required" # Standard Pydantic error

def test_auth_failure_invalid_key():
    headers = {"X-API-Key": "wrong-key"}
    response = client.post("/api/v1/tasks/", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API Key"

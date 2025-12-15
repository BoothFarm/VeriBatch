"""
Basic tests for VeriBatch API
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "OpenOriginJSON"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "VeriBatch API"
    assert "open-origin-json" in data["schema"]


def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_actor_lifecycle():
    """Test creating and retrieving an actor"""
    # Create actor
    actor_data = {
        "id": "test-farm",
        "name": "Test Farm",
        "kind": "producer"
    }
    
    response = client.post("/actors", json=actor_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-farm"
    assert data["name"] == "Test Farm"
    assert data["schema"] == "open-origin-json/0.5"
    assert data["type"] == "actor"
    assert "created_at" in data
    
    # Get actor
    response = client.get("/actors/test-farm")
    assert response.status_code == 200
    assert response.json()["id"] == "test-farm"
    
    # List actors
    response = client.get("/actors")
    assert response.status_code == 200
    actors = response.json()
    assert len(actors) >= 1
    assert any(a["id"] == "test-farm" for a in actors)

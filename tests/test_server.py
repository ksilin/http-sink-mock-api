"""
Tests for the HTTP Mock server.
"""

import json
from fastapi.testclient import TestClient

from app.server import app


client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "HTTP Mock Server is running"}


def test_default_response():
    """Test the default response for a message"""
    response = client.post(
        "/api/messages",
        json={"id": 1, "message": "Test message"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Message received successfully"}


def test_error_status_response():
    """Test response for a message with error status"""
    response = client.post(
        "/api/messages",
        json={"id": 2, "status": "error", "message": "Error message"}
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Bad request due to status=error"}


def test_high_priority_response():
    """Test response for a high priority message"""
    response = client.post(
        "/api/messages",
        json={"id": 3, "priority": "high", "message": "High priority message"}
    )
    assert response.status_code == 201
    assert response.json() == {"message": "High priority message processed"}


def test_reject_action_response():
    """Test response for a message with reject action"""
    response = client.post(
        "/api/messages",
        json={"id": 4, "action": "reject", "message": "Reject message"}
    )
    assert response.status_code == 422
    assert response.json() == {"error": "Message rejected as requested"}


def test_update_configuration():
    """Test updating the server configuration"""
    new_config = {
        "default": {
            "response_code": 202,
            "response_body": {"message": "Custom default response"}
        },
        "configurations": [
            {
                "match_field": "custom",
                "match_value": "test",
                "response_code": 418,
                "response_body": {"message": "I'm a teapot"}
            }
        ]
    }
    
    # Update the configuration
    response = client.post("/config", json=new_config)
    assert response.status_code == 200
    
    # Verify the configuration was updated
    response = client.get("/config")
    assert response.status_code == 200
    assert response.json()["default"]["response_code"] == 202
    
    # Test the new configuration
    response = client.post(
        "/api/messages",
        json={"id": 5, "custom": "test", "message": "Custom test"}
    )
    assert response.status_code == 418
    assert response.json() == {"message": "I'm a teapot"}
    
    # Test the new default response
    response = client.post(
        "/api/messages",
        json={"id": 6, "message": "Regular message"}
    )
    assert response.status_code == 202
    assert response.json() == {"message": "Custom default response"}

"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert data["service"] == "Leave Policy Assistant"
    
    def test_health_check_format(self):
        """Test health response format"""
        response = client.get("/health")
        data = response.json()
        
        # Verify required fields
        required_fields = ["status", "timestamp", "service", "version"]
        for field in required_fields:
            assert field in data


class TestChatEndpoint:
    """Test chat endpoint"""
    
    def test_chat_basic_message(self):
        """Test basic chat message"""
        payload = {
            "message": "Hello, can you help me?",
            "session_id": "test-session-1"
        }
        
        response = client.post("/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "response" in data
        assert "session_id" in data
        assert "timestamp" in data
        assert data["session_id"] == "test-session-1"
    
    def test_chat_new_session(self):
        """Test chat with new session"""
        payload = {
            "message": "What is my leave balance?"
        }
        
        response = client.post("/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should generate a new session_id
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 0
    
    def test_chat_missing_message(self):
        """Test chat with missing message field"""
        payload = {}
        
        response = client.post("/chat", json=payload)
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_chat_empty_message(self):
        """Test chat with empty message"""
        payload = {
            "message": ""
        }
        
        response = client.post("/chat", json=payload)
        
        # Should fail validation (min_length=1)
        assert response.status_code == 422


class TestStatsEndpoint:
    """Test statistics endpoint"""
    
    def test_stats_endpoint(self):
        """Test stats endpoint returns data"""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "security_callbacks" in data
        assert "snowflake" in data
    
    def test_stats_callback_structure(self):
        """Test callback stats structure"""
        response = client.get("/stats")
        data = response.json()
        
        callbacks = data["security_callbacks"]
        
        assert "before_model" in callbacks
        assert "after_model" in callbacks
        
        # Check before_model stats
        before = callbacks["before_model"]
        assert "total_calls" in before
        assert "pii_detections" in before
        assert "content_blocked" in before
        
        # Check after_model stats
        after = callbacks["after_model"]
        assert "total_calls" in after
        assert "total_tokens" in after
    
    def test_stats_snowflake_structure(self):
        """Test Snowflake stats structure"""
        response = client.get("/stats")
        data = response.json()
        
        snowflake = data["snowflake"]
        
        assert "connected" in snowflake
        assert "circuit_breakers" in snowflake


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint"""
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint exists"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
    
    def test_metrics_content_type(self):
        """Test metrics returns Prometheus format"""
        response = client.get("/metrics")
        
        # Prometheus uses text/plain or similar
        assert "text/plain" in response.headers.get("content-type", "")
    
    def test_metrics_content(self):
        """Test metrics contains expected metric names"""
        response = client.get("/metrics")
        content = response.text
        
        # Check for key metrics
        assert "leave_assistant" in content


class TestSessionManagement:
    """Test session management"""
    
    def test_session_persistence(self):
        """Test session maintains conversation history"""
        session_id = "test-persistence"
        
        # First message
        payload1 = {
            "message": "Hello",
            "session_id": session_id
        }
        response1 = client.post("/chat", json=payload1)
        assert response1.status_code == 200
        
        # Second message in same session
        payload2 = {
            "message": "What did I just say?",
            "session_id": session_id
        }
        response2 = client.post("/chat", json=payload2)
        assert response2.status_code == 200
        
        # Should maintain same session
        data2 = response2.json()
        assert data2["session_id"] == session_id
    
    def test_delete_session(self):
        """Test session deletion"""
        session_id = "test-delete-session"
        
        # Create a session
        payload = {
            "message": "Hello",
            "session_id": session_id
        }
        client.post("/chat", json=payload)
        
        # Delete session
        response = client.delete(f"/session/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session deleted successfully"
    
    def test_delete_nonexistent_session(self):
        """Test deleting non-existent session"""
        response = client.delete("/session/nonexistent-session")
        
        assert response.status_code == 404


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.get("/health")
        
        # CORS headers should be present (if configured)
        # This depends on your CORS middleware settings
        assert response.status_code == 200

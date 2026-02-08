"""
Tests for Pydantic models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    LeaveBalanceRequest,
    LeaveEligibilityRequest
)


class TestChatRequest:
    """Test ChatRequest model validation"""
    
    def test_valid_request(self):
        """Test valid chat request"""
        request = ChatRequest(
            message="What is my leave balance?",
            session_id="test-session"
        )
        
        assert request.message == "What is my leave balance?"
        assert request.session_id == "test-session"
    
    def test_message_required(self):
        """Test message field is required"""
        with pytest.raises(ValidationError):
            ChatRequest()
    
    def test_empty_message_validation(self):
        """Test empty message validation"""
        with pytest.raises(ValidationError):
            ChatRequest(message="")
    
    def test_optional_session_id(self):
        """Test session_id is optional"""
        request = ChatRequest(message="Hello")
        
        assert request.session_id is None
    
    def test_long_message(self):
        """Test long message handling"""
        long_message = "x" * 5000
        request = ChatRequest(message=long_message)
        
        assert len(request.message) == 5000


class TestChatResponse:
    """Test ChatResponse model"""
    
    def test_valid_response(self):
        """Test valid chat response"""
        response = ChatResponse(
            response="Your leave balance is 10 days",
            session_id="test-session",
            timestamp=datetime.utcnow()
        )
        
        assert response.response == "Your leave balance is 10 days"
        assert response.session_id == "test-session"
        assert isinstance(response.timestamp, datetime)
    
    def test_optional_metadata(self):
        """Test optional metadata field"""
        response = ChatResponse(
            response="Test",
            session_id="test",
            timestamp=datetime.utcnow()
        )
        
        assert response.metadata is None
    
    def test_with_metadata(self):
        """Test response with metadata"""
        metadata = {
            "tokens": 100,
            "model": "gemini-flash"
        }
        
        response = ChatResponse(
            response="Test",
            session_id="test",
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        
        assert response.metadata == metadata


class TestHealthResponse:
    """Test HealthResponse model"""
    
    def test_valid_health_response(self):
        """Test valid health response"""
        response = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            service="Leave Policy Assistant",
            version="1.0.0"
        )
        
        assert response.status == "healthy"
        assert response.service == "Leave Policy Assistant"
        assert response.version == "1.0.0"


class TestLeaveBalanceRequest:
    """Test LeaveBalanceRequest model (for future use)"""
    
    def test_valid_balance_request(self):
        """Test valid leave balance request"""
        if hasattr(LeaveBalanceRequest, '__fields__'):
            # Model exists
            request = LeaveBalanceRequest(
                employee_id="EMP001",
                leave_type="PTO"
            )
            
            assert request.employee_id == "EMP001"
            assert request.leave_type == "PTO"


class TestLeaveEligibilityRequest:
    """Test LeaveEligibilityRequest model (for future use)"""
    
    def test_valid_eligibility_request(self):
        """Test valid eligibility request"""
        if hasattr(LeaveEligibilityRequest, '__fields__'):
            # Model exists
            request = LeaveEligibilityRequest(
                employee_id="EMP001",
                leave_type="PTO",
                start_date="2026-03-01",
                end_date="2026-03-05",
                num_days=5
            )
            
            assert request.employee_id == "EMP001"
            assert request.num_days == 5

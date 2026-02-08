"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User's message to the agent")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    employee_id: Optional[str] = Field(None, description="Employee ID for personalized responses")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "How many PTO days do I have left?",
                "session_id": "session-123",
                "employee_id": "EMP001"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="Agent's response")
    session_id: str = Field(..., description="Session ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "You have 12 PTO days remaining out of your 20-day annual allowance.",
                "session_id": "session-123",
                "timestamp": "2024-01-15T10:30:00",
                "metadata": {"employee_id": "EMP001", "leave_type": "PTO"}
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")


class LeaveBalanceRequest(BaseModel):
    """Request for checking leave balance"""
    employee_id: str
    leave_type: Optional[str] = None


class LeaveEligibilityRequest(BaseModel):
    """Request for checking leave eligibility"""
    employee_id: str
    leave_type: str
    start_date: str
    end_date: str
    num_days: int
"""
FastAPI application for Leave Policy Assistant Agent
Provides REST API endpoints for agent interaction
"""

import os
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.models import ChatRequest, ChatResponse, HealthResponse
from app.agent import get_agent
from app.snowflake_client import get_snowflake_client
from app.callbacks import before_model_callback, after_model_callback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Leave Policy Assistant API")
    
    # Initialize connections
    try:
        # Initialize Snowflake client
        snowflake_client = get_snowflake_client()
        logger.info("✅ Snowflake client initialized")
        
        # Initialize agent
        agent = get_agent()
        logger.info("✅ Leave Assistant Agent initialized")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Leave Policy Assistant API")
    
    # Cleanup connections
    try:
        snowflake_client.close()
        logger.info("✅ Snowflake connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Initialize FastAPI app
app = FastAPI(
    title="Leave Policy Assistant API",
    description="AI-powered assistant for employee leave policy queries",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns service status and component health
    """
    try:
        # Check Snowflake connection
        snowflake_client = get_snowflake_client()
        snowflake_status = snowflake_client.get_connection_status()
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for interacting with the Leave Policy Assistant
    
    Args:
        request: ChatRequest with message, session_id, and employee_id
        
    Returns:
        ChatResponse with agent's response
    """
    try:
        logger.info(f"Received chat request from session: {request.session_id}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get agent instance
        agent = get_agent()
        
        # Process message
        result = agent.chat(
            message=request.message,
            session_id=session_id,
            employee_id=request.employee_id
        )
        
        # Check for errors
        if "error" in result and not result.get("blocked"):
            logger.error(f"Agent error: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing your request"
            )
        
        # Return response
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            timestamp=datetime.utcnow(),
            metadata=result.get("metadata")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear conversation history for a session
    
    Args:
        session_id: Session ID to clear
        
    Returns:
        Success message
    """
    try:
        agent = get_agent()
        agent.clear_session(session_id)
        
        return {
            "message": f"Session {session_id} cleared successfully",
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing session"
        )


@app.get("/stats")
async def get_stats():
    """
    Get callback statistics and system metrics
    
    Returns:
        Statistics dictionary
    """
    try:
        before_stats = before_model_callback.get_stats()
        after_stats = after_model_callback.get_stats()
        
        # Get Snowflake status
        snowflake_client = get_snowflake_client()
        snowflake_status = snowflake_client.get_connection_status()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "security_callbacks": {
                "before_model": before_stats,
                "after_model": after_stats
            },
            "snowflake": snowflake_status
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving statistics"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

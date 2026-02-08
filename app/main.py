import os
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from dotenv import load_dotenv

from app.models import ChatRequest, ChatResponse, HealthResponse
from app.agent import get_agent
from app.snowflake_client import get_snowflake_client
from app.callbacks import before_model_callback, after_model_callback
from app.metrics import get_metrics, record_agent_response, record_circuit_breaker_state

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    snowflake_client = get_snowflake_client()
    agent = get_agent()
    yield
    snowflake_client.close()


app = FastAPI(
    title="Leave Policy Assistant API",
    description="AI-powered assistant for employee leave policy queries",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(status="healthy", timestamp=datetime.utcnow(), version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", timestamp=datetime.utcnow(), version="1.0.0")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    agent = get_agent()
    
    result = agent.chat(
        message=request.message,
        session_id=session_id,
        employee_id=request.employee_id
    )
    
    record_agent_response("error" not in result or result.get("blocked"))
    
    return ChatResponse(
        response=result["response"],
        session_id=result["session_id"],
        timestamp=datetime.utcnow(),
        metadata=result.get("metadata")
    )


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    agent = get_agent()
    
    if session_id not in agent.sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    agent.clear_session(session_id)
    return {"message": "Session deleted successfully", "session_id": session_id}


@app.get("/stats")
async def get_stats():
    snowflake_client = get_snowflake_client()
    snowflake_status = snowflake_client.get_connection_status()
    
    for cb_name, cb_data in snowflake_status.get("circuit_breakers", {}).items():
        if cb_data:
            record_circuit_breaker_state(cb_name, cb_data.get("state", "closed"))
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "security_callbacks": {
            "before_model": before_model_callback.get_stats(),
            "after_model": after_model_callback.get_stats()
        },
        "snowflake": snowflake_status
    }


@app.get("/metrics")
async def metrics():
    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)), reload=True)

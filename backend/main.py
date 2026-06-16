import time
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from backend.database.db import db_instance
from backend.utils.ai_engine import ai_instance
from backend.models.schema import (
    DrowsinessStatusResponse,
    AlertEventResponse,
    SessionSummaryResponse,
    StatusMsgResponse
)

app = FastAPI(title="NeuralWatch - Driver Drowsiness AI Telemetry API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API Routes (Compatible with both /api and root paths)
# ---------------------------------------------------------------------------

@app.get("/status", response_model=DrowsinessStatusResponse)
@app.get("/api/status", response_model=DrowsinessStatusResponse)
async def get_status():
    """Get the current live driver drowsiness status and telemetry."""
    return ai_instance.get_status()


@app.get("/alerts", response_model=List[AlertEventResponse])
@app.get("/api/alerts", response_model=List[AlertEventResponse])
async def get_alerts():
    """Retrieve recent driver drowsiness warning events."""
    raw_alerts = db_instance.get_recent_alerts(limit=20)
    formatted_alerts = []
    for a in raw_alerts:
        # Pydantic schema validation preparation
        formatted_alerts.append(AlertEventResponse(
            id=str(a.get("id", a.get("_id", ""))),
            level=a.get("level", "normal"),
            message=a.get("message", ""),
            timestamp=a.get("timestamp", "")
        ))
    return formatted_alerts


@app.post("/start-camera", response_model=StatusMsgResponse)
@app.post("/api/start-camera", response_model=StatusMsgResponse)
async def start_camera():
    """Initiate webcam stream and launch AI computer vision engine."""
    success = ai_instance.start_camera()
    if success:
        return StatusMsgResponse(status="success", message="AI processing engine and camera started.")
    raise HTTPException(status_code=500, detail="Failed to start AI processing engine.")


@app.post("/stop-camera", response_model=StatusMsgResponse)
@app.post("/api/stop-camera", response_model=StatusMsgResponse)
async def stop_camera():
    """Stop the webcam stream and close the background AI engine."""
    success = ai_instance.stop_camera()
    if success:
        return StatusMsgResponse(status="success", message="AI processing engine and camera stopped.")
    return StatusMsgResponse(status="ignored", message="AI processing engine is not active.")


@app.get("/sessions", response_model=List[SessionSummaryResponse])
@app.get("/api/sessions", response_model=List[SessionSummaryResponse])
async def get_sessions():
    """Retrieve historical driver monitoring sessions."""
    raw_sessions = db_instance.get_sessions(limit=10)
    formatted_sessions = []
    for s in raw_sessions:
        formatted_sessions.append(SessionSummaryResponse(
            id=str(s.get("id", s.get("_id", ""))),
            session_duration=round(s.get("session_duration", 0.0), 1),
            total_blinks=s.get("total_blinks", 0),
            total_yawns=s.get("total_yawns", 0),
            max_drowsiness_score=round(s.get("max_drowsiness_score", 0.0), 1),
            camera_used=s.get("camera_used", False),
            timestamp=s.get("timestamp", "")
        ))
    return formatted_sessions


@app.get("/health")
@app.get("/api/health")
async def health():
    """API Health indicator check."""
    db_status = "connected" if db_instance.is_mongodb_active else "fallback_active"
    return {
        "status": "ok",
        "database": db_status,
        "ai_engine_running": ai_instance.is_running,
        "camera_active": ai_instance.camera_active
    }

# Start the app directly if executed
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

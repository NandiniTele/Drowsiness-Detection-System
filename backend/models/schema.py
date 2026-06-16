from pydantic import BaseModel
from typing import List, Optional

class DrowsinessStatusResponse(BaseModel):
    alert: bool
    alert_level: str
    confidence: float
    eye_aspect_ratio: float
    mouth_aspect_ratio: float
    left_ear: float
    right_ear: float
    head_pitch: float
    head_yaw: float
    blink_rate: float
    yawn_count: int
    drowsiness_score: float
    session_duration: float
    timestamp: str

class AlertEventResponse(BaseModel):
    id: str
    level: str
    message: str
    timestamp: str

class SessionSummaryResponse(BaseModel):
    id: str
    session_duration: float
    total_blinks: int
    total_yawns: int
    max_drowsiness_score: float
    camera_used: bool
    timestamp: str

class StatusMsgResponse(BaseModel):
    status: str
    message: str

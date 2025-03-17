from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

router = APIRouter()

# In-memory storage for logs (for demo purposes; use a persistent database in production)
logs = []

# Pydantic models for request and response bodies
class Alert(BaseModel):
    message: str
    video_url: Optional[str] = None
    event_timestamp: Optional[datetime] = None
    channels: Optional[List[str]] = None  # e.g., ["sms", "email"]

class LogEntry(BaseModel):
    id: int
    event_type: str  # e.g., "access", "intrusion", "video_record", "manual_alert"
    timestamp: datetime
    details: Optional[str] = None

@router.get("/status")
async def get_status():
    """
    GET /status endpoint returns the current status of the server room.
    For demo purposes, it returns a dummy "normal" status with a timestamp.
    """
    return {"status": "normal", "timestamp": datetime.now()}

@router.get("/logs", response_model=List[LogEntry])
async def get_logs():
    """
    GET /logs endpoint returns a list of log entries for access attempts,
    intrusion events, and video recordings.
    """
    return logs

@router.post("/alert", status_code=status.HTTP_201_CREATED)
async def post_alert(alert: Alert):
    """
    POST /alert endpoint for manual alert triggering.
    Accepts a JSON payload containing an alert message, optional video URL,
    event timestamp, and the desired channels (e.g., SMS, email).
    """
    # In a production scenario, you would call the notifications module here.
    # For demo purposes, we log the alert as a new log entry.
    log_entry = LogEntry(
        id=len(logs) + 1,
        event_type="manual_alert",
        timestamp=alert.event_timestamp if alert.event_timestamp else datetime.now(),
        details=alert.message
    )
    logs.append(log_entry)
    return {"message": "Alert processed", "log_id": log_entry.id}

@router.post("/control")
async def post_control(command: str):
    """
    POST /control endpoint to manually control server room functions,
    such as locking or unlocking the door.
    
    Args:
        command (str): The control command (e.g., "lock" or "unlock").

    Returns:
        JSON response with command execution result.
    """
    if command not in ["lock", "unlock"]:
        raise HTTPException(status_code=400, detail="Invalid command")
    # Here, implement the actual control logic (e.g., sending a command to the door lock)
    return {"message": f"Command '{command}' executed successfully", "timestamp": datetime.now()}

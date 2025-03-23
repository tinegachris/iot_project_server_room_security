from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class Alert(BaseModel):
    message: str = Field(..., description="Alert message content")
    video_url: Optional[str] = Field(None, description="URL to video footage if available")
    event_timestamp: Optional[datetime] = Field(None, description="Timestamp of the event")
    channels: Optional[List[str]] = Field(None, description="Notification channels to use")

class LogEntry(BaseModel):
    id: int
    event_type: str
    timestamp: datetime
    details: Optional[str] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True

class ControlCommand(BaseModel):
    action: str = Field(..., description="Control command to execute")
    parameters: Optional[dict] = Field(None, description="Additional parameters for the command")

class SystemHealth(BaseModel):
    sensors: dict
    storage: dict
    uptime: str
    last_maintenance: str
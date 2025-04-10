from pydantic import BaseModel, Field, EmailStr, HttpUrl
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class Severity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class UserRole(str, Enum):
    ADMIN = "Admin"
    SECURITY = "Security"
    STAFF = "Staff"
    USER = "User"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.USER
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    is_admin: bool = False

# --- Add Schema for Public Registration ---
class PublicUserCreate(BaseModel):
    username: str 
    email: EmailStr
    password: str
    # Add name if you want it during registration
    # name: Optional[str] = None 

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True

class SensorType(str, Enum):
    MOTION = "motion"
    DOOR = "door"
    WINDOW = "window"
    RFID = "rfid"
    CAMERA = "camera"

class SensorStatus(BaseModel):
    name: str
    is_active: bool
    last_check: datetime
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    type: Optional[str] = None  # motion, door, window, rfid, camera
    firmware_version: Optional[str] = None
    last_event: Optional[datetime] = None
    event_count: Optional[int] = 0

    class Config:
        from_attributes = True

# NOTE: The following schemas (CameraStatus, RFIDStatus, SensorData) appear unused
# based on current routes and controllers. Consider removing if confirmed.
class CameraStatus(BaseModel):
    is_active: bool

class RFIDStatus(BaseModel):
    is_active: bool
    last_read: Optional[datetime] = None
    last_card: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    authorized_cards: Optional[List[Dict[str, Any]]] = None

class SensorData(BaseModel):
    type: SensorType
    status: SensorStatus
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    firmware_version: Optional[str] = None
    last_event: Optional[datetime] = None
    event_count: Optional[int] = 0

    class Config:
        from_attributes = True

class Alert(BaseModel):
    id: Optional[int] = None
    message: str
    video_url: Optional[str] = None
    event_timestamp: datetime = Field(default_factory=datetime.now)
    channels: List[str] = ["email"]
    created_by: Optional[int] = None
    status: str = "pending"
    sent_at: Optional[datetime] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    sensor_data: Optional[Dict[str, Any]] = None
    acknowledged: bool = False
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AlertResponse(Alert):
    id: int
    event_timestamp: datetime
    created_by: int
    status: str
    sent_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ControlCommand(BaseModel):
    action: str
    parameters: Optional[Dict[str, Any]] = None

# Schema for events coming from Raspberry Pi
class RaspberryPiEvent(BaseModel):
    event_type: str
    message: str
    timestamp: datetime # Ensure datetime is parsed correctly
    media_url: Optional[str] = None
    sensor_data: Optional[Dict[str, Any]] = None
    severity: Severity = Severity.INFO # Default severity
    source: str = "raspberry_pi" # Source identifier

    class Config:
        from_attributes = True # Allow mapping from ORM models if needed
        # Add custom JSON encoders if necessary, e.g., for datetime
        # json_encoders = {
        #     datetime: lambda v: v.isoformat(),
        # }

class LogEntryBase(BaseModel):
    event_type: str
    timestamp: datetime
    details: Dict[str, Any]
    user_id: Optional[int] = None
    video_url: Optional[str] = None
    severity: Severity = Severity.INFO
    source: str

    class Config:
        from_attributes = True

class LogEntry(LogEntryBase):
    id: Optional[int] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True

class SystemHealth(BaseModel):
    status: str
    sensors: Dict[str, SensorStatus]
    storage: Dict[str, Any]
    uptime: str
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    errors: Optional[List[str]] = None
    raspberry_pi: Dict[str, Any]

class AccessLog(BaseModel):
    id: int
    user_id: str
    access_time: datetime
    status: str
    details: Dict[str, Any]
    location: str
    card_uid: Optional[str] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True

class SensorEvent(BaseModel):
    id: int
    event_type: str
    event_time: datetime
    description: str
    sensor_data: Dict[str, Any]
    location: str
    severity: Severity = Severity.INFO
    processed: bool = False
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class VideoRecord(BaseModel):
    id: int
    file_path: str
    record_time: datetime
    event_type: str
    duration: int
    size: int
    cloud_url: Optional[HttpUrl] = None
    sensor_event_id: Optional[int] = None
    processed: bool = False
    retention_days: int = 7

    class Config:
        from_attributes = True

class MaintenanceLog(BaseModel):
    id: int
    timestamp: datetime
    type: str
    description: str
    performed_by: int
    status: str
    next_maintenance: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

# --- Add Token schema --- 
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Add LogResponse model for pagination ---
class LogResponse(BaseModel):
    logs: List[LogEntry]
    total: int
    skip: int
    limit: int
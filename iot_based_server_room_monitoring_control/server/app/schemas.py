from pydantic import BaseModel, Field, EmailStr, HttpUrl
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class Severity(str, Enum):
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
    ADMIN = "admin"
    IT_STAFF = "IT staff"
    MAINTENANCE = "maintenance"
    USER = "user"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.USER
    is_active: bool = True

class UserCreate(UserBase):
    password: str

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
        orm_mode = True

class Alert(BaseModel):
    message: str
    video_url: Optional[HttpUrl] = None
    severity: AlertSeverity = AlertSeverity.HIGH
    sensor_data: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    acknowledged: bool = False

class AlertResponse(Alert):
    id: int
    event_timestamp: datetime
    created_by: int
    status: str
    sent_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ControlCommand(BaseModel):
    action: str = Field(..., description="Action to execute (lock, unlock, restart_system, test_sensors, capture_image, record_video)")
    parameters: Optional[Dict[str, Any]] = None

class LogEntry(BaseModel):
    id: int
    event_type: str
    timestamp: datetime
    details: Dict[str, Any]
    user_id: int
    video_url: Optional[HttpUrl] = None
    severity: Severity = Severity.INFO
    source: str

    class Config:
        orm_mode = True

class SensorStatus(BaseModel):
    name: str
    is_active: bool
    last_check: datetime
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    location: Optional[str] = None

class SystemHealth(BaseModel):
    status: str
    timestamp: datetime
    user: str
    sensors: Dict[str, SensorStatus]
    storage: Dict[str, Any]
    uptime: str
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    errors: Optional[List[str]] = None

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
        orm_mode = True

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
        orm_mode = True

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
        orm_mode = True

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
        orm_mode = True

class RaspberryPiStatus(BaseModel):
    hostname: str
    ip_address: str
    uptime: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    temperature: float
    last_reboot: datetime
    firmware_version: str
    is_online: bool = True
    last_heartbeat: datetime
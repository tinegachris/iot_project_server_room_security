from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_url = Column(String(255))

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text)
    video_url = Column(String(255))
    event_timestamp = Column(DateTime, default=datetime.utcnow)
    channels = Column(String(100))  # Stored as comma-separated values
    created_by = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending")  # pending, sent, failed
    sent_at = Column(DateTime)

class AccessLog(Base):
    """
    Data model for logging access attempts (e.g., RFID-based authentication).
    """
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)          # Identifier for the user (e.g., RFID tag)
    access_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String)                         # e.g., "granted", "denied"
    details = Column(Text, nullable=True)           # Additional details (e.g., role, location)

class SensorEvent(Base):
    """
    Data model for logging sensor events such as motion, door/window triggers,
    and unauthorized RFID access.
    """
    __tablename__ = "sensor_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)         # e.g., "motion", "door", "window", "rfid"
    event_time = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)

class VideoRecord(Base):
    """
    Data model for logging video recordings that are triggered by events.
    """
    __tablename__ = "video_records"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, index=True)  # Local file path or cloud URL
    record_time = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String, index=True)              # e.g., "intrusion", "unauthorized_rfid"

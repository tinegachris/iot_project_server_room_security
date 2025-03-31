from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, DeclarativeMeta
from datetime import datetime
from typing import Any

Base: DeclarativeMeta = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    role = Column(String(20), default="user")  # admin, IT staff, maintenance
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime)

    logs = relationship("LogEntry", back_populates="user")
    alerts = relationship("Alert", back_populates="user")

class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)  # Changed from Text to JSON for structured data
    user_id = Column(Integer, ForeignKey("users.id"))
    video_url = Column(String(255))
    severity = Column(String(20), default="info")  # info, warning, error, critical
    source = Column(String(50))  # system, user, sensor, camera, rfid

    user = relationship("User", back_populates="logs")

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
    severity = Column(String(20), default="high")  # low, medium, high, critical
    sensor_data = Column(JSON)  # Store sensor data as JSON
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)

    user = relationship("User", back_populates="alerts")

class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    access_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20))  # granted, denied
    details = Column(JSON)  # Changed from Text to JSON
    location = Column(String(50))  # door, window, etc.
    card_uid = Column(String(50))  # RFID card UID
    role = Column(String(20))  # role of the card holder

class SensorEvent(Base):
    __tablename__ = "sensor_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), index=True)
    event_time = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
    sensor_data = Column(JSON)  # Store sensor data as JSON
    location = Column(String(50))
    severity = Column(String(20), default="info")
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)

class VideoRecord(Base):
    __tablename__ = "video_records"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(255), unique=True, index=True)
    record_time = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(50), index=True)
    duration = Column(Integer)  # Duration in seconds
    size = Column(Integer)  # File size in bytes
    cloud_url = Column(String(255))
    sensor_event_id = Column(Integer, ForeignKey("sensor_events.id"))
    processed = Column(Boolean, default=False)
    retention_days = Column(Integer, default=7)

class SystemHealth(Base):
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20))  # healthy, degraded, error
    uptime = Column(String(50))
    storage = Column(JSON)  # Storage metrics
    sensors = Column(JSON)  # Sensor status
    errors = Column(JSON)  # List of errors
    last_maintenance = Column(DateTime)
    next_maintenance = Column(DateTime)

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(String(50))  # routine, emergency, upgrade
    description = Column(Text)
    performed_by = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20))  # completed, scheduled, in_progress
    next_maintenance = Column(DateTime)
    notes = Column(Text)

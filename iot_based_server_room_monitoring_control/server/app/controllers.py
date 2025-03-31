import logging
import os
import json
import shutil
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from .models import (
    AccessLog, SensorEvent, VideoRecord, LogEntry,
    SystemHealth, MaintenanceLog, Alert, User
)
from ..config.config import config
from .schemas import Severity, AlertSeverity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RaspberryPiClient:
    """Client for communicating with Raspberry Pi."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_status(self) -> Dict[str, Any]:
        """Get Raspberry Pi status."""
        if not self.session:
            raise RuntimeError("Client session not initialized")

        try:
            async with self.session.get(f"{self.base_url}/status") as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error getting Raspberry Pi status: {e}")
            raise

    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a command on the Raspberry Pi."""
        if not self.session:
            raise RuntimeError("Client session not initialized")

        try:
            async with self.session.post(
                f"{self.base_url}/control",
                json={"action": command, "parameters": params}
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
            raise

async def process_alert_and_event(
    db: Session,
    event_type: str,
    message: str,
    video_url: Optional[str] = None,
    username: str = "system",
    severity: Severity = Severity.INFO,
    sensor_data: Optional[Dict[str, Any]] = None
) -> LogEntry:
    """Process an alert or event and create a log entry."""
    try:
        # Create log entry
        log_entry = LogEntry(
            event_type=event_type,
            timestamp=datetime.now(),
            details={
                "message": message,
                "video_url": video_url,
                "user": username,
                "sensor_data": sensor_data
            },
            severity=severity,
            source="system"
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        # Create alert if severity is high enough
        if severity in [Severity.WARNING, Severity.ERROR, Severity.CRITICAL]:
            alert = Alert(
                message=message,
                video_url=video_url,
                severity=AlertSeverity.HIGH if severity == Severity.CRITICAL else AlertSeverity.MEDIUM,
                sensor_data=sensor_data,
                channels=["email", "sms"] if severity == Severity.CRITICAL else ["email"]
            )
            db.add(alert)
            db.commit()

        return log_entry
    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        raise

async def get_sensor_status(db: Session) -> Dict[str, Any]:
    """Get the current status of all sensors and system health."""
    try:
        # Get storage information
        total, used, free = shutil.disk_usage("/")
        storage = {
            "total_gb": total // (2**30),
            "used_gb": used // (2**30),
            "free_gb": free // (2**30),
            "low_space": free // (2**30) < config["monitoring"]["storage_threshold_gb"]
        }

        # Get system uptime
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        uptime = str(timedelta(seconds=int(uptime_seconds)))

        # Get Raspberry Pi status
        async with RaspberryPiClient(config["raspberry_pi"]["api_url"]) as client:
            pi_status = await client.get_status()

            # Process sensor status
            sensors = {}
            for sensor_name, sensor_data in pi_status.get("sensors", {}).items():
                sensors[sensor_name] = {
                    "name": sensor_data.get("name", sensor_name),
                    "is_active": sensor_data.get("is_active", False),
                    "last_check": datetime.fromisoformat(sensor_data.get("last_check", datetime.now().isoformat())),
                    "error": sensor_data.get("error"),
                    "data": sensor_data.get("data"),
                    "location": sensor_data.get("location")
                }

            # Check for errors
            errors = []
            for sensor_name, status in sensors.items():
                if not status["is_active"]:
                    errors.append(f"{sensor_name} sensor is inactive")
                if status.get("error"):
                    errors.append(f"{sensor_name} sensor error: {status['error']}")

            # Get maintenance information
            maintenance = await get_maintenance_status(db)

            return {
                "status": "healthy" if not errors else "degraded",
                "sensors": sensors,
                "storage": storage,
                "uptime": uptime,
                "last_maintenance": maintenance.get("last_maintenance"),
                "next_maintenance": maintenance.get("next_maintenance"),
                "errors": errors if errors else None,
                "raspberry_pi": {
                    "is_online": True,
                    "last_heartbeat": datetime.now(),
                    "firmware_version": pi_status.get("firmware_version", "unknown")
                }
            }
    except Exception as e:
        logger.error(f"Error getting sensor status: {e}")
        return {
            "status": "error",
            "sensors": {},
            "storage": {"error": str(e)},
            "uptime": "unknown",
            "errors": [str(e)]
        }

async def execute_control_command(action: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute a control command on the Raspberry Pi."""
    try:
        async with RaspberryPiClient(config["raspberry_pi"]["api_url"]) as client:
            result = await client.execute_command(action, parameters)

            # Log the command execution
            log_entry = LogEntry(
                event_type="control_command",
                timestamp=datetime.now(),
                details={
                    "action": action,
                    "parameters": parameters,
                    "result": result
                },
                severity=Severity.INFO,
                source="user"
            )

            return result
    except Exception as e:
        logger.error(f"Error executing command {action}: {e}")
        raise

async def get_maintenance_status(db: Session) -> Dict[str, Any]:
    """Get system maintenance status."""
    try:
        last_maintenance = db.query(MaintenanceLog).filter(
            MaintenanceLog.status == "completed"
        ).order_by(MaintenanceLog.timestamp.desc()).first()

        next_maintenance = db.query(MaintenanceLog).filter(
            MaintenanceLog.status == "scheduled"
        ).order_by(MaintenanceLog.next_maintenance.asc()).first()

        return {
            "last_maintenance": last_maintenance.timestamp if last_maintenance else None,
            "next_maintenance": next_maintenance.next_maintenance if next_maintenance else None,
            "last_maintenance_type": last_maintenance.type if last_maintenance else None,
            "next_maintenance_type": next_maintenance.type if next_maintenance else None
        }
    except Exception as e:
        logger.error(f"Error getting maintenance status: {e}")
        return {}

async def cleanup_old_records(db: Session) -> None:
    """Clean up old records based on retention policies."""
    try:
        # Get retention periods from config
        log_retention = timedelta(days=config["monitoring"]["max_log_retention_days"])
        video_retention = timedelta(days=config["monitoring"]["max_video_retention_days"])

        # Clean up old log entries
        cutoff_date = datetime.now() - log_retention
        db.query(LogEntry).filter(LogEntry.timestamp < cutoff_date).delete()

        # Clean up old video records
        cutoff_date = datetime.now() - video_retention
        old_videos = db.query(VideoRecord).filter(VideoRecord.record_time < cutoff_date).all()
        for video in old_videos:
            try:
                if os.path.exists(video.file_path):
                    os.remove(video.file_path)
            except Exception as e:
                logger.error(f"Error deleting video file {video.file_path}: {e}")
        db.query(VideoRecord).filter(VideoRecord.record_time < cutoff_date).delete()

        db.commit()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
        raise

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
from .raspberry_pi_client import RaspberryPiClient
from .schemas import RaspberryPiEvent
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # Use .get() for safer config access with a default
        storage_threshold = config.get("monitoring", {}).get("storage_threshold_gb", 10) # Default 10GB
        storage = {
            "total_gb": total // (2**30),
            "used_gb": used // (2**30),
            "free_gb": free // (2**30),
            "low_space": free // (2**30) < storage_threshold
        }

        # Get system uptime
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        uptime = str(timedelta(seconds=int(uptime_seconds)))

        # Get Raspberry Pi status
        pi_url = config.get("raspberry_pi", {}).get("api_url")
        pi_key = config.get("raspberry_pi", {}).get("api_key")
        if not pi_url:
             logger.error("Raspberry Pi API URL not configured in server config.")
             # Return partial status or raise error?
             # For now, return indicating Pi status unavailable.
             pi_status = {"error": "Raspberry Pi API URL not configured"}
             sensors = {}
        else:
            async with RaspberryPiClient(pi_url, pi_key) as client:
                 pi_status = await client.get_status()
                 # Process sensor status from Pi response
                 sensors = {}
                 pi_sensor_data = pi_status.get("sensors", {})
                 if isinstance(pi_sensor_data, dict): # Check if it's a dictionary
                     for sensor_name, sensor_data in pi_sensor_data.items():
                         if isinstance(sensor_data, dict): # Check if sensor_data is a dict
                             sensors[sensor_name] = {
                                 "name": sensor_data.get("name", sensor_name),
                                 "is_active": sensor_data.get("is_active", False),
                                 "last_check": datetime.fromisoformat(sensor_data["last_check"]) if sensor_data.get("last_check") else None,
                                 "error": sensor_data.get("error"),
                                 "data": sensor_data.get("data"),
                                 "location": sensor_data.get("location"),
                                 "type": sensor_data.get("type"),
                                 "firmware_version": sensor_data.get("firmware_version"),
                                 "last_event_timestamp": datetime.fromisoformat(sensor_data["last_event_timestamp"]) if sensor_data.get("last_event_timestamp") else None,
                                 "event_count": sensor_data.get("event_count", 0)
                             }
                         else:
                              logger.warning(f"Received invalid sensor data format for {sensor_name} from Pi: {sensor_data}")
                 else:
                      logger.warning(f"Received invalid format for 'sensors' key from Pi: {pi_sensor_data}")

        # Check for errors based on processed sensor data
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
                "firmware_version": pi_status.get("firmware_version", "unknown"),
                "sensor_types": [s["type"] for s in sensors.values() if s.get("type")],
                "total_events": sum(s["event_count"] for s in sensors.values())
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

async def execute_control_command(
    action: str,
    db: Session,
    user_id: Optional[int] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute a control command on the Raspberry Pi and log the action."""
    pi_client = None # Initialize client variable
    try:
        # Access config hierarchically
        pi_config = config.get("raspberry_pi", {})
        pi_base_url = pi_config.get("api_url")
        pi_api_key = pi_config.get("api_key")
        
        if not pi_base_url:
            # Use a more specific error or log and raise HTTP 500?
            logger.error("RASPBERRY_PI_API_URL is not configured in server config (config.yaml or env var)")
            raise HTTPException(
                status_code=500, 
                detail="Raspberry Pi communication endpoint not configured on server."
            )

        logger.info(f"Executing command '{action}' on Pi: {pi_base_url} with params: {parameters}")
        # Pass the potentially None api_key to the client
        pi_client = RaspberryPiClient(pi_base_url, pi_api_key)
        async with pi_client as client: # Use async context manager
            result = await client.execute_command(action, parameters)
            logger.info(f"Command '{action}' executed on Pi. Result: {result}")

            # Log the command execution to DB *after* successful execution
            try:
                log_entry = LogEntry(
                    event_type="control_command",
                    timestamp=datetime.now(),
                    details={
                        "action": action,
                        "parameters": parameters,
                        "result": result,
                        "user_id": user_id # Log which user triggered it
                    },
                    severity=Severity.INFO,
                    source="server_api",
                    user_id=user_id
                )
                db.add(log_entry)
                db.commit()
                logger.info(f"Control command '{action}' logged successfully.")
            except Exception as db_err:
                logger.error(f"Database error logging control command '{action}': {db_err}", exc_info=True)
                db.rollback()
                # Non-fatal, command executed, but logging failed.
                # Result is already captured, so we can still return it.

            return result # Return the result from the Pi

    except Exception as e:
        logger.error(f"Error executing command '{action}' on Pi: {e}", exc_info=True)
        # Consider returning a specific error structure or re-raising a custom exception
        raise HTTPException(
            status_code=503, # Service Unavailable (failed to communicate with Pi)
            detail=f"Failed to execute command '{action}' on Raspberry Pi: {e}"
        )

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

# ✅ New controller function to handle events from Raspberry Pi
async def process_pi_event(
    db: Session,
    event: RaspberryPiEvent # Use the new schema - remove quotes now that it's imported
) -> LogEntry:
    """Process an event received from the Raspberry Pi and create a log entry."""
    logger.info(f"Processing event from Raspberry Pi: {event.event_type}")
    log_entry = None # Initialize log_entry
    try:
        # Determine image/video URL from incoming media_url
        incoming_media_url = event.media_url
        image_url = incoming_media_url if incoming_media_url and incoming_media_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) else None
        video_url = incoming_media_url if incoming_media_url and incoming_media_url.lower().endswith(('.mp4', '.avi', '.mov', '.h264')) else None

        # Create log entry using data from the Pi event
        log_entry = LogEntry(
            event_type=event.event_type,
            timestamp=event.timestamp,
            details={
                "message": event.message,
                "sensor_data": event.sensor_data,
                "media_url": incoming_media_url # Store the original URL here for reference
            },
            image_url=image_url, # Store determined image URL
            video_url=video_url, # Store determined video URL
            severity=event.severity,
            source=event.source,
            user_id=None # Events from Pi are typically system events, no specific user
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        logger.info(f"Successfully logged event from Pi: ID {log_entry.id}, Type: {log_entry.event_type}")

        # Optionally trigger alerts based on severity (similar to process_alert_and_event)
        if event.severity in [Severity.WARNING, Severity.ERROR, Severity.CRITICAL]:
            logger.warning(f"High severity event received from Pi ({event.severity}): {event.event_type}. Consider triggering server-side alerts.")
            # Placeholder: Add logic here to trigger server-side notifications
            # based on the received event, if needed beyond what the Pi already sent.
            # Example: Create an Alert record, trigger push notifications, etc.

        return log_entry # Return the created entry

    except Exception as e:
        logger.error(f"Error processing event from Pi (Type: {event.event_type}, Timestamp: {event.timestamp}): {e}", exc_info=True)
        try:
            db.rollback() # Ensure transaction is rolled back on error
            logger.info("Database transaction rolled back due to error processing Pi event.")
        except Exception as rb_exc:
            logger.error(f"Failed to rollback database transaction after Pi event processing error: {rb_exc}")
        # Re-raising the exception might cause the background task runner to log it,
        # but avoid crashing the whole server if possible.
        # Depending on the background task runner, this might be sufficient.
        # Alternatively, log the error to a dedicated error table/file.
        raise # Re-raise the exception to be potentially caught by the task runner

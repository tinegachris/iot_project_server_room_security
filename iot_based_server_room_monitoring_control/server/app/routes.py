from fastapi import APIRouter, HTTPException, status, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import json
from .database import get_db
from .controllers import process_alert_and_event, get_sensor_status, execute_control_command
from .models import LogEntry as DBLogEntry
from .schemas import LogEntry, Alert, ControlCommand, SensorStatus, SystemHealth
from .rate_limit import rate_limit
from .auth import get_current_user
from ..config.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60    # seconds

@router.get("/status", response_model=SystemHealth)
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def get_status(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /status endpoint returns the current status of the server room.
    Includes system health metrics and sensor status.
    """
    try:
        # Get system health metrics
        system_status = await get_sensor_status(db)

        # Add user context
        system_status["user"] = current_user["username"]
        system_status["timestamp"] = datetime.now()

        # Log status check
        background_tasks.add_task(
            process_alert_and_event,
            "status_check",
            f"Status check by {current_user['username']}",
            None,
            current_user["username"]
        )

        return system_status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )

@router.get("/logs", response_model=List[LogEntry])
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def get_logs(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /logs endpoint returns a list of log entries with filtering options.
    """
    try:
        query = db.query(DBLogEntry)

        # Apply filters
        if event_type:
            query = query.filter(DBLogEntry.event_type == event_type)
        if start_date:
            query = query.filter(DBLogEntry.timestamp >= start_date)
        if end_date:
            query = query.filter(DBLogEntry.timestamp <= end_date)

        # Apply pagination
        total = query.count()
        logs = query.offset(skip).limit(limit).all()

        return {
            "logs": logs,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error retrieving logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve logs"
        )

@router.post("/alert", status_code=status.HTTP_201_CREATED)
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def post_alert(
    request: Request,
    alert: Alert,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    POST /alert endpoint for manual alert triggering.
    Includes validation and processing of alert data.
    """
    try:
        # Validate alert data
        if not alert.message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alert message is required"
            )

        # Process the alert
        log_entry = await process_alert_and_event(
            db,
            "manual_alert",
            alert.message,
            alert.video_url,
            current_user["username"]
        )

        # Log the alert
        logger.info(f"Alert created by {current_user['username']}: {alert.message}")

        return {
            "message": "Alert processed successfully",
            "log_id": log_entry.id,
            "timestamp": log_entry.timestamp
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process alert"
        )

@router.post("/control")
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def post_control(
    request: Request,
    command: ControlCommand,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    POST /control endpoint to manually control server room functions.
    Includes command validation and execution logging.
    """
    try:
        # Validate command
        valid_actions = ["lock", "unlock", "restart_system", "test_sensors", "capture_image", "record_video"]
        if command.action not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid command action. Must be one of: {', '.join(valid_actions)}"
            )

        # Check user permissions
        if command.action in ["restart_system"] and not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this command"
            )

       # Execute command
        result = await execute_control_command(command.action)

        # Log the command execution
        log_entry = DBLogEntry(
            event_type="control_command",
            timestamp=datetime.now(),
            details=json.dumps({
                "command": command.action,
                "user": current_user["username"],
                "result": result
            }),
            user_id=current_user["id"]
        )
        db.add(log_entry)
        db.commit()

        return {
            "message": f"Command '{command.action}' executed successfully",
            "timestamp": datetime.now(),
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing control command: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute control command"
        )

async def get_system_health():
    """
    Get system health metrics including sensor status, storage space, and system uptime.
    """
    try:
        # This would be implemented to gather actual system metrics
        return {
            "sensors": {
                "motion": "active",
                "door": "active",
                "window": "active",
                "rfid": "active"
            },
            "storage": {
                "total": "500GB",
                "used": "200GB",
                "free": "300GB"
            },
            "uptime": "7 days",
            "last_maintenance": "2024-03-17"
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {"error": "Failed to retrieve system health metrics"}

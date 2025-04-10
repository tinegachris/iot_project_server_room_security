from fastapi import APIRouter, HTTPException, status, Depends, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
import json
from .database import get_db
from .controllers import (
    process_alert_and_event, get_sensor_status,
    execute_control_command, process_pi_event,
    authenticate_user
)
from .models import LogEntry as DBLogEntry, User
from .schemas import (
    LogEntry, Alert, ControlCommand, SensorStatus, SystemHealth,
    RaspberryPiEvent,
    Token,
    Severity,
    LogResponse,
    UserCreate,
    User as UserSchema
)
from .rate_limit import rate_limit
from .auth import get_current_user, get_api_key, create_access_token, create_user as auth_create_user
from ..config.config import config
from .raspberry_pi_client import RaspberryPiClient

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
    current_user: User = Depends(get_current_user) # Re-enable auth
):
    """
    GET /status endpoint returns the current status of the server room.
    Includes system health metrics and sensor status.
    """
    try:
        # Get system health metrics
        system_status = await get_sensor_status(db)

        # Add user context (use authenticated user)
        system_status["user"] = current_user.username
        system_status["timestamp"] = datetime.now()

        # Log status check (use authenticated user)
        background_tasks.add_task(
            process_alert_and_event,
            db,
            "status_check",
            f"Status check by {current_user.username}",
            None,
            current_user.username,
            Severity.INFO
        )

        return SystemHealth(**system_status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )

@router.get("/logs", response_model=LogResponse)
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def get_logs(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
            current_user.username
        )

        # Log the alert
        logger.info(f"Alert created by {current_user.username}: {alert.message}")

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
    command: ControlCommand, # Restore body param
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    """Post control command to the Raspberry Pi and log the action."""
    # Restore original function body
    try:
        # Validate command
        valid_actions = [
            "lock", "unlock", "restart_system", "test_sensors",
            "capture_image", "record_video", "clear_logs", "update_firmware"
        ]
        if command.action not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid command action. Must be one of: {', '.join(valid_actions)}"
            )

        # Check user permissions (Example: only admin can restart)
        if command.action in ["restart_system", "update_firmware"] and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this command"
            )

       # Execute command via controller, passing db session and user info
        result = await execute_control_command(
            action=command.action,
            db=db,
            user_id=current_user.id, 
            parameters=command.parameters 
        )

        # Log the command execution locally (using background task is an option too)
        # Logging is now handled within execute_control_command
        # logger.info(f"Control command '{command.action}' initiated by {current_user.username}") 

        return {
            "message": f"Command '{command.action}' sent to Raspberry Pi successfully",
            "timestamp": datetime.now(),
            "result_from_pi": result
        }
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions (like 400, 403, or 503 from controller)
        raise http_exc
    except Exception as e:
        logger.error(f"Error processing control command '{command.action}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process control command '{command.action}': An unexpected error occurred."
        )

@router.post("/events", status_code=status.HTTP_201_CREATED)
async def receive_pi_event(
    request: Request,
    event: RaspberryPiEvent,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    POST /events endpoint for Raspberry Pi to send event data.
    Requires API Key authentication.
    """
    try:
        background_tasks.add_task(process_pi_event, db, event)
        logger.info(f"Received event from Pi ({event.source}): {event.event_type}. Processing in background.")
        return {"message": "Event received successfully and queued for processing"}
    except Exception as e:
        logger.error(f"Error receiving event from Pi: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to receive event"
        )

@router.get("/sensors/{sensor_type}", response_model=Dict[str, Any])
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def get_sensor_data(
    sensor_type: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /sensors/{sensor_type} endpoint returns data from a specific sensor.
    """
    try:
        pi_url = config["raspberry_pi"]["api_url"]
        pi_key = config["raspberry_pi"]["api_key"]

        if not pi_url:
            raise HTTPException(status_code=500, detail="Pi URL not configured")

        # Ensure trailing slash for client base_url consistency
        if not pi_url.endswith('/'):
            pi_url += '/'

        async with RaspberryPiClient(pi_url, pi_key) as client:
            sensor_data = await client.get_sensor_data(sensor_type)

            # Log sensor data retrieval
            background_tasks.add_task(
                process_alert_and_event, 
                db=db, # Pass the db session correctly
                event_type="sensor_data", 
                message=f"Sensor data retrieved for {sensor_type}", 
                video_url=None, 
                username=current_user.username,
                severity=Severity.INFO, # Add severity
                sensor_data=sensor_data # Pass the retrieved data
            )

            return sensor_data
    except Exception as e:
        logger.error(f"Error getting sensor data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sensor data for {sensor_type}"
        )

@router.get("/camera/status", response_model=Dict[str, Any])
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def get_camera_status(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /camera/status endpoint returns camera status and settings.
    """
    try:
        async with RaspberryPiClient(config["raspberry_pi"]["api_url"]) as client:
            camera_status = await client.get_camera_status()

            # Log camera status check
            background_tasks.add_task(
                process_alert_and_event,
                "camera_status",
                "Camera status retrieved",
                None,
                current_user.username
            )

            return camera_status
    except Exception as e:
        logger.error(f"Error getting camera status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve camera status"
        )

@router.get("/rfid/status", response_model=Dict[str, Any])
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def get_rfid_status(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /rfid/status endpoint returns RFID reader status and last read card.
    """
    try:
        async with RaspberryPiClient(config["raspberry_pi"]["api_url"]) as client:
            rfid_status = await client.get_rfid_status()

            # Log RFID status check
            background_tasks.add_task(
                process_alert_and_event,
                "rfid_status",
                "RFID status retrieved",
                None,
                current_user.username
            )

            return rfid_status
    except Exception as e:
        logger.error(f"Error getting RFID status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve RFID status"
        )

@router.post("/camera/capture")
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def capture_image(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    POST /camera/capture endpoint triggers image capture.
    """
    try:
        async with RaspberryPiClient(config["raspberry_pi"]["api_url"]) as client:
            result = await client.execute_command("capture_image")

            # Log image capture
            background_tasks.add_task(
                process_alert_and_event,
                "image_capture",
                "Image captured",
                result.get("image_url"),
                current_user.username
            )

            return result
    except Exception as e:
        logger.error(f"Error capturing image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to capture image"
        )

@router.post("/camera/record")
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def record_video(
    request: Request,
    background_tasks: BackgroundTasks,
    duration: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    POST /camera/record endpoint triggers video recording.
    """
    try:
        result = await execute_control_command(
            action="record_video",
            parameters={"duration": duration},
            db=db,
            user_id=current_user.id
        )
        return {
            "message": f"Video recording for {duration}s initiated.",
            "pi_response": result,
            "timestamp": datetime.now()
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error initiating video recording: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate video recording"
        )

@router.get("/sensors/{sensor_type}/events", response_model=List[Dict[str, Any]])
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def get_sensor_events(
    sensor_type: str,
    request: Request,
    background_tasks: BackgroundTasks,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /sensors/{sensor_type}/events endpoint returns events from a specific sensor.
    """
    try:
        events = db.query(DBLogEntry)\
                 .filter(DBLogEntry.source == sensor_type)\
                 .order_by(DBLogEntry.timestamp.desc())\
                 .limit(limit)\
                 .all()

        return [LogEntry.from_orm(event).dict() for event in events]

    except Exception as e:
        logger.error(f"Error fetching events for sensor {sensor_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch events for sensor {sensor_type}"
        )

@router.get("/sensors/{sensor_type}/stats", response_model=Dict[str, Any])
@rate_limit(requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW)
async def get_sensor_stats(
    sensor_type: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /sensors/{sensor_type}/stats endpoint returns statistics for a specific sensor.
    """
    try:
        stats_placeholder = {
            "sensor_type": sensor_type,
            "total_events_last_24h": 0,
            "last_event_time": None
        }
        return stats_placeholder
    except Exception as e:
        logger.error(f"Error fetching stats for sensor {sensor_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats for sensor {sensor_type}"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Standard FastAPI OAuth2 password flow token endpoint."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Use dictionary access for config value with a default
    access_token_expires = timedelta(minutes=config.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current logged-in user details.
    """
    # The get_current_user dependency already fetches the user object from the DB
    # based on the token. We just need to return it.
    # Note: Ensure your schemas.User includes all necessary fields (id, username, email, name, role).
    # You might need a specific UserRead schema if you want to exclude fields like password hash.
    return current_user

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    POST /users endpoint to create a new user.
    """
    try:
        # Check if the current user is an admin
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create a user"
            )

        # Create the new user
        new_user = auth_create_user(db, user.username, user.password, user.email, user.is_admin)

        # Log the user creation
        logger.info(f"User '{new_user.username}' created by '{current_user.username}'.")

        return {
            "message": "User created successfully",
            "user_id": new_user.id,
            "username": new_user.username
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

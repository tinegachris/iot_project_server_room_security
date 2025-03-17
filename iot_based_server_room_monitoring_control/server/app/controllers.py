import logging
from datetime import datetime
from sqlalchemy.orm import Session
from .models import AccessLog, SensorEvent, VideoRecord

logger = logging.getLogger(__name__)

def log_access_attempt(db: Session, user_id: str, status: str, details: str = None):
    """
    Logs an access attempt (e.g., via RFID).
    
    Args:
        db (Session): Database session.
        user_id (str): Identifier from the RFID tag.
        status (str): "granted" or "denied".
        details (str, optional): Additional details.
    
    Returns:
        AccessLog: The created access log record.
    """
    access_log = AccessLog(user_id=user_id, status=status, details=details)
    db.add(access_log)
    db.commit()
    db.refresh(access_log)
    logger.info(f"Access attempt logged: {access_log}")
    return access_log

def log_sensor_event(db: Session, event_type: str, description: str = None):
    """
    Logs a sensor event, such as motion detected, door/window trigger, or unauthorized RFID access.
    
    Args:
        db (Session): Database session.
        event_type (str): Type of event (e.g., "motion", "door", "rfid").
        description (str, optional): Detailed description.
    
    Returns:
        SensorEvent: The created sensor event record.
    """
    sensor_event = SensorEvent(event_type=event_type, description=description)
    db.add(sensor_event)
    db.commit()
    db.refresh(sensor_event)
    logger.info(f"Sensor event logged: {sensor_event}")
    return sensor_event

def log_video_record(db: Session, file_path: str, event_type: str):
    """
    Logs a video recording triggered by an event.
    
    Args:
        db (Session): Database session.
        file_path (str): The file path or URL of the recorded video.
        event_type (str): Type of event triggering the video.
    
    Returns:
        VideoRecord: The created video record.
    """
    video_record = VideoRecord(file_path=file_path, event_type=event_type)
    db.add(video_record)
    db.commit()
    db.refresh(video_record)
    logger.info(f"Video record logged: {video_record}")
    return video_record

def process_alert_and_event(db: Session, event_type: str, description: str, video_file: str = None):
    """
    Processes an alert by logging a sensor event and, if a video file is provided,
    logging a video record as well. This function can be extended to include integration
    with cloud storage for video files.
    
    Args:
        db (Session): Database session.
        event_type (str): Type of event (e.g., "intrusion", "unauthorized_rfid").
        description (str): Description of the event.
        video_file (str, optional): Local path or URL of the recorded video.
    
    Returns:
        dict: A dictionary with the logged sensor event and video record (if any).
    """
    event = log_sensor_event(db, event_type, description)
    result = {"sensor_event": event}
    if video_file:
        video = log_video_record(db, video_file, event_type)
        result["video_record"] = video
        # Here, you could integrate with cloud storage to upload the video
        # and update the video_record with the cloud URL.
        logger.info("Simulating cloud upload for video file: %s", video_file)
    return result

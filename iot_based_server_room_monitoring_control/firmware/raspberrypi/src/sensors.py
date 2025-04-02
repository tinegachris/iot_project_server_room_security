"""
sensors.py

This module integrates all sensors (RFID, Camera, Motion) for server room monitoring.
It provides a unified interface for sensor management, event handling, and status monitoring.
"""

import time
import logging
import datetime
import threading
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from motion import MotionSensorHandler, DoorSensorHandler, WindowSensorHandler, SensorConfig
from rfid import RFIDReader, RFIDStatus, CardInfo
from camera import CameraManager, CameraConfig
from notifications import NotificationManager, create_intrusion_alert, create_rfid_alert

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SensorStatus:
    """Status information for a sensor."""
    name: str
    is_active: bool
    last_check: datetime.datetime
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    type: Optional[str] = None  # motion, door, window, rfid, camera
    firmware_version: Optional[str] = None
    last_event: Optional[datetime.datetime] = None
    event_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert sensor status to dictionary format."""
        return {
            "name": self.name,
            "is_active": self.is_active,
            "last_check": self.last_check.isoformat(),
            "error": self.error,
            "data": self.data,
            "location": self.location,
            "type": self.type,
            "firmware_version": self.firmware_version,
            "last_event": self.last_event.isoformat() if self.last_event else None,
            "event_count": self.event_count
        }

class SensorManager:
    """Manages all sensors and provides unified monitoring interface."""

    def __init__(self, verbose: bool = False):
        """Initialize the sensor manager with all sensors."""
        self.verbose = verbose
        self._lock = threading.Lock()
        self._threads: List[threading.Thread] = []
        self._sensor_status: Dict[str, SensorStatus] = {}
        self._last_event_time = datetime.datetime.now()
        self._event_cooldown = 30  # seconds
        self._running = True
        self._notification_manager = NotificationManager()

        # Initialize sensors with proper configuration
        try:
            # Motion sensor configuration
            motion_config = SensorConfig(
                gpio_pin=int(os.getenv("MOTION_SENSOR_PIN", "4")),
                led_pin=int(os.getenv("MOTION_LED_PIN", "22")),
                name="Motion",
                verbose=verbose
            )
            self._motion_sensor = MotionSensorHandler(motion_config)

            # Door sensor configuration
            door_config = SensorConfig(
                gpio_pin=int(os.getenv("DOOR_SENSOR_PIN", "17")),
                led_pin=int(os.getenv("DOOR_LED_PIN", "23")),
                name="Door",
                verbose=verbose
            )
            self._door_sensor = DoorSensorHandler(door_config)

            # Window sensor configuration
            window_config = SensorConfig(
                gpio_pin=int(os.getenv("WINDOW_SENSOR_PIN", "27")),
                led_pin=int(os.getenv("WINDOW_LED_PIN", "24")),
                name="Window",
                verbose=verbose
            )
            self._window_sensor = WindowSensorHandler(window_config)

            # RFID reader initialization
            self._rfid_reader = RFIDReader()

            # Camera initialization with default configuration
            self._camera = CameraManager()

            # Initialize sensor status
            self._update_sensor_status('motion', False)
            self._update_sensor_status('door', False)
            self._update_sensor_status('window', False)
            self._update_sensor_status('rfid', False)
            self._update_sensor_status('camera', True)

            logger.info("Sensor manager initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize sensor manager: %s", e)
            raise

    def _handle_motion(self) -> None:
        """Handle motion sensor events."""
        while self._running:
            try:
                motion_detected = self._motion_sensor.check_motion()
                self._update_sensor_status('motion', True, data={'detected': motion_detected})

                if motion_detected:
                    logger.info("Motion detected in server room")
                    self._handle_intrusion_event("motion_detected", "Motion detected in server room")

                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('motion', False, str(e))
                logger.error("Motion sensor error: %s", e)
                time.sleep(5)

    def _handle_door(self) -> None:
        """Handle door sensor events."""
        while self._running:
            try:
                door_open = self._door_sensor.check_state()
                self._update_sensor_status('door', True, data={'open': door_open})

                if door_open:
                    logger.info("Door opened in server room")
                    self._handle_intrusion_event("door_opened", "Door opened in server room")

                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('door', False, str(e))
                logger.error("Door sensor error: %s", e)
                time.sleep(5)

    def _handle_window(self) -> None:
        """Handle window sensor events."""
        while self._running:
            try:
                window_open = self._window_sensor.check_state()
                self._update_sensor_status('window', True, data={'open': window_open})

                if window_open:
                    logger.info("Window opened in server room")
                    self._handle_intrusion_event("window_opened", "Window opened in server room")

                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('window', False, str(e))
                logger.error("Window sensor error: %s", e)
                time.sleep(5)

    def _handle_rfid(self) -> None:
        """Handle RFID events."""
        while self._running:
            try:
                status, uid = self._rfid_reader.read_card()

                if status == RFIDStatus.OK:
                    auth_status, role = self._rfid_reader.authenticate_card(uid)
                    uid_str = '-'.join(str(x) for x in uid)

                    self._update_sensor_status('rfid', True, data={
                        'uid': uid_str,
                        'authorized': auth_status == RFIDStatus.OK,
                        'role': role if auth_status == RFIDStatus.OK else 'unauthorized'
                    })

                    if auth_status == RFIDStatus.OK:
                        logger.info("RFID access granted: %s (%s)", uid_str, role)
                    else:
                        logger.warning("Unauthorized RFID access: %s", uid_str)
                        self._handle_unauthorized_access(uid_str)

                time.sleep(0.5)  # Shorter sleep for more responsive RFID reading
            except Exception as e:
                self._update_sensor_status('rfid', False, str(e))
                logger.error("RFID error: %s", e)
                time.sleep(5)

    def _handle_intrusion_event(self, event_type: str, message: str) -> None:
        """Handle intrusion events by capturing media and sending notifications."""
        current_time = datetime.datetime.now()
        if (current_time - self._last_event_time).total_seconds() < self._event_cooldown:
            logger.debug("Intrusion event cooldown active, skipping media capture")
            return

        try:
            # Capture image and video
            image_path, image_url = self._camera.capture_image()
            video_path, video_url = self._camera.record_video(duration=30)

            # Update camera status with latest capture info
            self._update_sensor_status('camera', True, data={
                'last_image': image_path,
                'last_image_url': image_url,
                'last_video': video_path,
                'last_video_url': video_url
            })

            # Create and send alert
            alert = create_intrusion_alert(
                event_type=event_type,
                message=message,
                media_url=image_url,
                sensor_data={
                    'location': event_type.split('_')[0],
                    'image_url': image_url,
                    'video_url': video_url
                }
            )
            self._notification_manager.send_alert(alert)

            logger.warning("Intrusion detected! Media captured: %s, %s", image_path, video_path)
            self._last_event_time = current_time
        except Exception as e:
            self._update_sensor_status('camera', False, str(e))
            logger.error("Failed to handle intrusion event: %s", e)

    def _handle_unauthorized_access(self, uid: str) -> None:
        """Handle unauthorized access events."""
        current_time = datetime.datetime.now()
        if (current_time - self._last_event_time).total_seconds() < self._event_cooldown:
            logger.debug("Unauthorized access event cooldown active, skipping media capture")
            return

        try:
            # Capture image and video
            image_path, image_url = self._camera.capture_image()
            video_path, video_url = self._camera.record_video(duration=30)

            # Update camera status with latest capture info
            self._update_sensor_status('camera', True, data={
                'last_image': image_path,
                'last_image_url': image_url,
                'last_video': video_path,
                'last_video_url': video_url,
                'event_type': 'unauthorized_access'
            })

            # Create and send alert
            alert = create_rfid_alert(
                event_type="unauthorized_access",
                message="Unauthorized RFID access attempt",
                uid=uid,
                media_url=image_url
            )
            self._notification_manager.send_alert(alert)

            logger.warning("Unauthorized access! Media captured: %s, %s", image_path, video_path)
            self._last_event_time = current_time
        except Exception as e:
            self._update_sensor_status('camera', False, str(e))
            logger.error("Failed to handle unauthorized access event: %s", e)

    def _update_sensor_status(self, sensor_name: str, is_active: bool, error: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> None:
        """Update the status of a sensor."""
        with self._lock:
            self._sensor_status[sensor_name] = SensorStatus(
                name=sensor_name,
                is_active=is_active,
                last_check=datetime.datetime.now(),
                error=error,
                data=data
            )

    def get_sensor_status(self) -> Dict[str, Any]:
        """Get the current status of all sensors."""
        with self._lock:
            return {
                name: status.to_dict()
                for name, status in self._sensor_status.items()
            }

    def start(self) -> None:
        """Start all sensor monitoring threads."""
        self._running = True
        self._threads = [
            threading.Thread(target=self._handle_motion, name="MotionThread"),
            threading.Thread(target=self._handle_door, name="DoorThread"),
            threading.Thread(target=self._handle_window, name="WindowThread"),
            threading.Thread(target=self._handle_rfid, name="RFIDThread")
        ]

        for thread in self._threads:
            thread.daemon = True
            thread.start()

        logger.info("All sensor threads started successfully")

    def stop(self) -> None:
        """Stop all sensor monitoring threads."""
        self._running = False
        logger.info("Stopping all sensor threads...")
        time.sleep(2)  # Give threads time to exit gracefully

    def cleanup(self) -> None:
        """Clean up all sensor resources."""
        try:
            self.stop()
            self._motion_sensor.cleanup()
            self._door_sensor.cleanup()
            self._window_sensor.cleanup()
            self._rfid_reader.cleanup()
            logger.info("All sensor resources cleaned up successfully")
        except Exception as e:
            logger.error("Error during cleanup: %s", e)

def main() -> None:
    """Test the sensor manager functionality."""
    sensor_manager = SensorManager(verbose=True)
    try:
        sensor_manager.start()
        logger.info("Sensor manager started. Press Ctrl+C to exit.")

        while True:
            status = sensor_manager.get_sensor_status()
            logger.info("Sensor status: %s", status)
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error("Unexpected error: %s", e)
    finally:
        sensor_manager.cleanup()
        logger.info("Exiting...")

if __name__ == "__main__":
    main()

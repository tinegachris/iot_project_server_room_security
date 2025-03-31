#!/home/admin/iot_project_server_room_security/venv/bin/python3
"""
sensors.py

This module integrates all sensors (RFID, Camera, Motion) for server room monitoring.
It provides a unified interface for sensor management, event handling, and status monitoring.
"""

import time
import logging
import datetime
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from motion import MotionSensorHandler, DoorSensorHandler, WindowSensorHandler, SensorConfig
from rfid import RFIDReader, RFIDStatus
from camera import CameraManager, CameraConfig

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

        # Initialize sensors with proper configuration
        self._motion_sensor = MotionSensorHandler(
            SensorConfig(gpio_pin=4, led_pin=22, name="Motion", verbose=verbose)
        )
        self._door_sensor = DoorSensorHandler(
            SensorConfig(gpio_pin=17, led_pin=23, name="Door", verbose=verbose)
        )
        self._window_sensor = WindowSensorHandler(
            SensorConfig(gpio_pin=27, led_pin=24, name="Window", verbose=verbose)
        )
        self._rfid_reader = RFIDReader()
        self._camera = CameraManager()

        logger.info("Sensor manager initialized successfully")

    def _handle_motion(self) -> None:
        """Handle motion sensor events."""
        while True:
            try:
                if self._motion_sensor.check_motion():
                    self._update_sensor_status('motion', True)
                    self._handle_intrusion_event()
                else:
                    self._update_sensor_status('motion', True)
                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('motion', False, str(e))
                logger.error("Motion sensor error: %s", e)
                time.sleep(5)

    def _handle_door(self) -> None:
        """Handle door sensor events."""
        while True:
            try:
                if self._door_sensor.check_state():
                    self._update_sensor_status('door', True)
                    self._handle_intrusion_event()
                else:
                    self._update_sensor_status('door', True)
                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('door', False, str(e))
                logger.error("Door sensor error: %s", e)
                time.sleep(5)

    def _handle_window(self) -> None:
        """Handle window sensor events."""
        while True:
            try:
                if self._window_sensor.check_state():
                    self._update_sensor_status('window', True)
                    self._handle_intrusion_event()
                else:
                    self._update_sensor_status('window', True)
                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('window', False, str(e))
                logger.error("Window sensor error: %s", e)
                time.sleep(5)

    def _handle_rfid(self) -> None:
        """Handle RFID events."""
        while True:
            try:
                status, uid = self._rfid_reader.read_card()
                if status == RFIDStatus.OK:
                    status, role = self._rfid_reader.authenticate_card(uid)
                    if status == RFIDStatus.OK:
                        logger.info("RFID access granted: %s (%s)", uid, role)
                        self._update_sensor_status('rfid', True)
                    else:
                        logger.warning("Unauthorized RFID access: %s", uid)
                        self._handle_unauthorized_access()
                        self._update_sensor_status('rfid', True)
                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('rfid', False, str(e))
                logger.error("RFID error: %s", e)
                time.sleep(5)

    def _handle_intrusion_event(self) -> None:
        """Handle intrusion events by capturing images and videos."""
        current_time = datetime.datetime.now()
        if (current_time - self._last_event_time).total_seconds() < self._event_cooldown:
            return

        try:
            # Capture image and video
            image_path, image_url = self._camera.capture_image()
            video_path, video_url = self._camera.record_video(duration=30)

            logger.warning("Intrusion detected! Media captured: %s, %s", image_path, video_path)
            self._last_event_time = current_time
        except Exception as e:
            logger.error("Failed to capture intrusion media: %s", e)

    def _handle_unauthorized_access(self) -> None:
        """Handle unauthorized access events."""
        current_time = datetime.datetime.now()
        if (current_time - self._last_event_time).total_seconds() < self._event_cooldown:
            return

        try:
            # Capture image and video
            image_path, image_url = self._camera.capture_image()
            video_path, video_url = self._camera.record_video(duration=30)

            logger.warning("Unauthorized access! Media captured: %s, %s", image_path, video_path)
            self._last_event_time = current_time
        except Exception as e:
            logger.error("Failed to capture unauthorized access media: %s", e)

    def _update_sensor_status(self, sensor_name: str, is_active: bool, error: Optional[str] = None) -> None:
        """Update the status of a sensor."""
        with self._lock:
            self._sensor_status[sensor_name] = SensorStatus(
                name=sensor_name,
                is_active=is_active,
                last_check=datetime.datetime.now(),
                error=error
            )

    def get_sensor_status(self) -> Dict:
        """Get the current status of all sensors."""
        with self._lock:
            return {
                name: {
                    'is_active': status.is_active,
                    'last_check': status.last_check.isoformat(),
                    'error': status.error
                }
                for name, status in self._sensor_status.items()
            }

    def start(self) -> None:
        """Start all sensor monitoring threads."""
        self._threads = [
            threading.Thread(target=self._handle_motion),
            threading.Thread(target=self._handle_door),
            threading.Thread(target=self._handle_window),
            threading.Thread(target=self._handle_rfid)
        ]

        for thread in self._threads:
            thread.daemon = True
            thread.start()

        logger.info("All sensor threads started successfully")

    def cleanup(self) -> None:
        """Clean up all sensor resources."""
        try:
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
        while True:
            status = sensor_manager.get_sensor_status()
            logger.info("Sensor status: %s", status)
            time.sleep(5)
    except KeyboardInterrupt:
        sensor_manager.cleanup()
        logger.info("Exiting...")
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        sensor_manager.cleanup()

if __name__ == "__main__":
    main()

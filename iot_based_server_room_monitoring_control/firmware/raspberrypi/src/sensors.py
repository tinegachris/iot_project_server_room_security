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
from .motion import MotionSensorHandler, DoorSensorHandler, WindowSensorHandler, SensorConfig
from .rfid import RFIDReader, RFIDStatus, CardInfo
from .camera import CameraManager, CameraConfig
from .notifications import NotificationManager, create_intrusion_alert, create_rfid_alert

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
    type: str # Made non-optional: motion, door, window, rfid, camera, door_lock etc.
    location: Optional[str] = None # e.g., 'main_door', 'rack_window'
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    firmware_version: Optional[str] = None # Can be added if sensors have firmware
    last_event_timestamp: Optional[datetime.datetime] = None # Renamed for clarity
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
            "last_event_timestamp": self.last_event_timestamp.isoformat() if self.last_event_timestamp else None,
            "event_count": self.event_count
        }

class SensorManager:
    """Manages all sensors and provides unified monitoring interface."""

    def __init__(self, camera_config: Optional[CameraConfig] = None, verbose: bool = False):
        """Initialize the sensor manager with all sensors."""
        self.verbose = verbose
        self._lock = threading.Lock()
        self._threads: List[threading.Thread] = []
        self._sensor_status: Dict[str, SensorStatus] = {}
        self._last_event_time = datetime.datetime.now() - datetime.timedelta(seconds=300) # Initialize to allow immediate event
        self._event_cooldown = int(os.getenv("EVENT_COOLDOWN", "300")) # Cooldown in seconds
        self._running = True
        self._notification_manager = NotificationManager()

        # Initialize sensors with proper configuration
        try:
            # Motion sensor configuration
            motion_pin = int(os.getenv("MOTION_SENSOR_PIN", "17"))
            motion_config = SensorConfig(
                gpio_pin=motion_pin,
                led_pin=int(os.getenv("MOTION_LED_PIN", "23")),
                name="Motion",
                verbose=verbose
            )
            self._motion_sensor = MotionSensorHandler(motion_config)
            self._initialize_sensor_status('motion', type='motion', location=f'pin_{motion_pin}')

            # Door sensor configuration
            door_pin = int(os.getenv("DOOR_SENSOR_PIN", "27"))
            door_config = SensorConfig(
                gpio_pin=door_pin,
                led_pin=int(os.getenv("DOOR_LED_PIN", "24")),
                name="Door",
                verbose=verbose
            )
            self._door_sensor = DoorSensorHandler(door_config)
            self._initialize_sensor_status('door', type='door', location=f'pin_{door_pin}')

            # Window sensor configuration
            window_pin = int(os.getenv("WINDOW_SENSOR_PIN", "22"))
            window_config = SensorConfig(
                gpio_pin=window_pin,
                led_pin=int(os.getenv("WINDOW_LED_PIN", "25")),
                name="Window",
                verbose=verbose
            )
            self._window_sensor = WindowSensorHandler(window_config)
            self._initialize_sensor_status('window', type='window', location=f'pin_{window_pin}')

            # RFID reader initialization
            self._rfid_reader = RFIDReader()
            self._initialize_sensor_status('rfid', type='rfid', location='main_reader')

            # Camera initialization - Pass the config if provided
            self._camera = CameraManager(config=camera_config)
            self._initialize_sensor_status('camera', type='camera', location='main_camera')

            # Door lock status (managed by api_server, but status reflected here)
            door_lock_pin = int(os.getenv("DOOR_LOCK_PIN", "24"))
            self._initialize_sensor_status('door_lock', type='actuator', location=f'pin_{door_lock_pin}')
            
            # Window lock status (managed by api_server, but status reflected here)
            window_lock_pin = int(os.getenv("WINDOW_LOCK_PIN", "25"))
            self._initialize_sensor_status('window_lock', type='actuator', location=f'pin_{window_lock_pin}')

            logger.info("Sensor manager initialized successfully with initial statuses")
        except Exception as e:
            logger.error("Failed to initialize sensor manager: %s", e)
            raise

    # Helper to initialize status entries
    def _initialize_sensor_status(self, sensor_name: str, type: str, location: Optional[str] = None):
        with self._lock:
            if sensor_name not in self._sensor_status:
                 self._sensor_status[sensor_name] = SensorStatus(
                     name=sensor_name,
                     type=type,
                     location=location,
                     is_active=False, # Will be set to True once checks start
                     last_check=datetime.datetime.now(),
                     event_count=0,
                     last_event_timestamp=None
                 )

    # Update method to preserve existing static info and update counts/timestamps
    def _update_sensor_status(self, sensor_name: str, is_active: bool, error: Optional[str] = None, data: Optional[Dict[str, Any]] = None, event_detected: bool = False) -> None:
        """Update the status of a sensor, incrementing event count if needed."""
        now = datetime.datetime.now()
        with self._lock:
            if sensor_name in self._sensor_status:
                current_status = self._sensor_status[sensor_name]
                current_status.is_active = is_active
                current_status.last_check = now
                current_status.error = error
                current_status.data = data

                if event_detected:
                     current_status.event_count += 1
                     current_status.last_event_timestamp = now
            else:
                # Should not happen if initialized correctly, but handle defensively
                logger.warning(f"Attempted to update status for uninitialized sensor: {sensor_name}. Creating entry.")
                # Need type/location info here if creating dynamically
                fallback_type = 'unknown'
                fallback_location = None
                if sensor_name == 'motion': fallback_type = 'motion'
                elif sensor_name == 'door': fallback_type = 'door'
                elif sensor_name == 'window': fallback_type = 'window'
                elif sensor_name == 'rfid': fallback_type = 'rfid'
                elif sensor_name == 'camera': fallback_type = 'camera'
                elif sensor_name == 'door_lock': fallback_type = 'actuator'
                elif sensor_name == 'window_lock': fallback_type = 'actuator'
                # ... add other fallbacks if necessary ...

                self._sensor_status[sensor_name] = SensorStatus(
                    name=sensor_name,
                    is_active=is_active,
                    last_check=now,
                    error=error,
                    data=data,
                    type=fallback_type,
                    location=fallback_location,
                    event_count=1 if event_detected else 0,
                    last_event_timestamp=now if event_detected else None
                )

    def _handle_motion(self) -> None:
        """Handle motion sensor events."""
        while self._running:
            try:
                motion_detected = self._motion_sensor.check_motion()
                self._update_sensor_status('motion', True, data={'detected': motion_detected})

                if motion_detected:
                    logger.info("Motion detected in server room")
                    self._update_sensor_status('motion', True, data={'detected': True}, event_detected=True)
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
                    self._update_sensor_status('door', True, data={'open': True}, event_detected=True)
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
                    self._update_sensor_status('window', True, data={'open': True}, event_detected=True)
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
                    }, event_detected=True)

                    if auth_status == RFIDStatus.OK:
                        logger.info("RFID access granted: %s (%s)", uid_str, role)
                    else:
                        logger.warning("Unauthorized RFID access: %s", uid_str)
                        self._handle_unauthorized_access(uid_str)

                time.sleep(60)  # Check RFID every 60 seconds
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
            video_path, video_url = self._camera.record_video(duration=10)

            # Update camera status with latest capture info
            self._update_sensor_status('camera', True, data={
                'last_image': image_path,
                'last_image_url': image_url,
                'last_video': video_path,
                'last_video_url': video_url,
                'trigger_event': event_type
            }, event_detected=True)

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
                'trigger_event': 'unauthorized_access',
                'uid': uid
            }, event_detected=True)

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

    def get_sensor_status(self) -> Dict[str, Any]:
        """Get the current status of all sensors."""
        with self._lock:
            return {
                name: status.to_dict()
                for name, status in self._sensor_status.items()
            }

    def start(self) -> None:
        """Start all sensor monitoring threads."""
        if self._threads:
            logger.warning("Sensor threads already started or not cleaned up properly. Attempting restart.")
            self.stop()

        self._running = True
        self._threads = [
            threading.Thread(target=self._handle_motion, name="MotionThread"),
            threading.Thread(target=self._handle_door, name="DoorThread"),
            threading.Thread(target=self._handle_window, name="WindowThread"),
            threading.Thread(target=self._handle_rfid, name="RFIDThread")
        ]

        for thread in self._threads:
            thread.daemon = False # Set to False for graceful shutdown
            thread.start()

        logger.info("All sensor threads started successfully")

    def stop(self) -> None:
        """Stop all sensor monitoring threads."""
        if not self._running:
            logger.info("Sensor threads already stopping or stopped.")
            return

        self._running = False
        logger.info("Stopping all sensor threads...")

        # Wait for threads to finish
        thread_join_timeout = 5.0 # Seconds to wait for each thread
        threads_to_join = list(self._threads) # Copy list as we might modify it later
        self._threads = [] # Clear the list of active threads

        for thread in threads_to_join:
            if thread.is_alive():
                 logger.debug(f"Waiting for thread {thread.name} to join...")
                 thread.join(timeout=thread_join_timeout)
                 if thread.is_alive():
                     logger.warning(f"Thread {thread.name} did not join within {thread_join_timeout}s.")
                 else:
                     logger.debug(f"Thread {thread.name} joined successfully.")
            else:
                 logger.debug(f"Thread {thread.name} was already finished.")

        logger.info("Finished attempting to stop sensor threads.")

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

    def run_sensor_test(self) -> Dict[str, Any]:
        """Runs a diagnostic check on all initialized sensors."""
        logger.info("Running sensor test...")
        results = {}
        all_ok = True

        # Test motion sensor
        try:
            status = self._motion_sensor.check_motion() # Or a dedicated test method if available
            results['motion'] = {"status": "ok", "details": f"Current state: {status}"}
            logger.info("Motion sensor test: OK")
        except Exception as e:
            results['motion'] = {"status": "error", "details": str(e)}
            logger.error(f"Motion sensor test failed: {e}")
            all_ok = False

        # Test door sensor
        try:
            status = self._door_sensor.check_state() # Or a dedicated test method
            results['door'] = {"status": "ok", "details": f"Current state: {'open' if status else 'closed'}"}
            logger.info("Door sensor test: OK")
        except Exception as e:
            results['door'] = {"status": "error", "details": str(e)}
            logger.error(f"Door sensor test failed: {e}")
            all_ok = False

        # Test window sensor
        try:
            status = self._window_sensor.check_state() # Or a dedicated test method
            results['window'] = {"status": "ok", "details": f"Current state: {'open' if status else 'closed'}"}
            logger.info("Window sensor test: OK")
        except Exception as e:
            results['window'] = {"status": "error", "details": str(e)}
            logger.error(f"Window sensor test failed: {e}")
            all_ok = False

        # Test RFID reader
        try:
            # Simple test: try to read for a short duration
            # More advanced test might involve checking connection status
            status, _ = self._rfid_reader.read_card(timeout=0.5) # Short timeout
            if status in [RFIDStatus.OK, RFIDStatus.NO_CARD]: # No card is also OK for a test
                results['rfid'] = {"status": "ok", "details": "Reader responsive"}
                logger.info("RFID reader test: OK")
            else:
                results['rfid'] = {"status": "error", "details": f"Reader status: {status.name}"}
                logger.warning(f"RFID reader test status: {status.name}")
                # Decide if non-OK status during test is an error
                # all_ok = False
        except Exception as e:
            results['rfid'] = {"status": "error", "details": str(e)}
            logger.error(f"RFID reader test failed: {e}")
            all_ok = False

        # Test Camera
        try:
            # Simple test: get status from CameraManager
            cam_status = self._camera.get_status()
            if cam_status.get("is_active"):
                 results['camera'] = {"status": "ok", "details": "Camera active"}
                 logger.info("Camera test: OK")
            else:
                 results['camera'] = {"status": "error", "details": cam_status.get("error") or "Camera inactive"}
                 logger.error(f"Camera test failed: {results['camera']['details']}")
                 all_ok = False
        except Exception as e:
            results['camera'] = {"status": "error", "details": str(e)}
            logger.error(f"Camera test failed: {e}")
            all_ok = False

        # Test Door Lock (Check GPIO state if possible?)
        # This is harder without reading input pins. Maybe just log the expected state.
        try:
            # Example: If using api_server's IS_LOCKED state
            # from .api_server import IS_LOCKED
            # current_lock_state = IS_LOCKED
            # Or query GPIO if possible?
            # status = GPIO.input(DOOR_LOCK_PIN) # Assuming DOOR_LOCK_PIN is accessible
            results['door_lock'] = {"status": "info", "details": "Test not fully implemented (check logs for state)"}
            logger.info("Door Lock Test: Status logged by lock/unlock functions.")
        except Exception as e:
            results['door_lock'] = {"status": "error", "details": str(e)}
            logger.error(f"Door Lock test failed: {e}")
            all_ok = False

        summary = "All tests passed" if all_ok else "One or more tests failed"
        logger.info(f"Sensor test completed. Summary: {summary}")
        return {"summary": summary, "results": results}

    # Add health check method for main loop
    def is_healthy(self) -> bool:
        """Check if all sensor threads are running."""
        if not self._running:
            return False # Not running means not healthy in this context
        for thread in self._threads:
            if not thread.is_alive():
                logger.error(f"Sensor thread {thread.name} is not alive!")
                return False
        return True

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

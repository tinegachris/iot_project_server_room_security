#!/home/admin/iot_project_server_room_security/venv/bin/python3
"""
sensors.py

This module handles the following sensors:

    - A PIR motion sensor (to detect motion)
    - A door sensor (e.g., a reed switch on a door)
    - A window sensor (e.g., a reed switch on a window)
    - An RFID sensor (to detect unauthorized access)

The class `SensorManager` manages all sensors and provides methods to check for
intrusion and unauthorized access.
"""

import time
import logging
import datetime
import threading
import json
from typing import List, Dict, Optional
from motion import MotionSensorHandler, DoorSensorHandler, WindowSensorHandler
from rfid import RFIDReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SensorStatus:
    def __init__(self, name: str, is_active: bool, last_check: datetime.datetime, error: Optional[str] = None):
        self.name = name
        self.is_active = is_active
        self.last_check = last_check
        self.error = error

class SensorManager:
    """Class to manage all sensors."""

    def __init__(self, verbose: bool):
        self.verbose = verbose
        self._motion_sensor = MotionSensorHandler(4, verbose)
        self._door_sensor = DoorSensorHandler(17, verbose)
        self._window_sensor = WindowSensorHandler(27, verbose)
        self._rfid_reader = RFIDReader()
        self._threads: List[threading.Thread] = []
        self._sensor_status: Dict[str, SensorStatus] = {}
        self._lock = threading.Lock()
        self._last_event_time = datetime.datetime.now()
        self._event_cooldown = 30  # seconds to wait before processing new events

    def _handle_motion(self):
        """Handles motion detection by the motion sensor."""
        while True:
            try:
                if self._motion_sensor.sensor.motion_detected:
                    self._motion_sensor.on_motion()
                    self._update_sensor_status('motion', True)
                else:
                    self._motion_sensor.on_no_motion()
                    self._update_sensor_status('motion', True)
                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('motion', False, str(e))
                logging.error(f"Error in motion sensor handler: {e}")
                time.sleep(5)  # Wait before retrying

    def _handle_door(self):
        """Handles door detection by the door sensor."""
        while True:
            try:
                if self._door_sensor.on_open:
                    self._door_sensor.on_open()
                    self._update_sensor_status('door', True)
                else:
                    self._door_sensor.on_close()
                    self._update_sensor_status('door', True)
                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('door', False, str(e))
                logging.error(f"Error in door sensor handler: {e}")
                time.sleep(5)

    def _handle_window(self):
        """Handles window detection by the window sensor."""
        while True:
            try:
                if self._window_sensor.on_open:
                    self._window_sensor.on_open()
                    self._update_sensor_status('window', True)
                else:
                    self._window_sensor.on_close()
                    self._update_sensor_status('window', True)
                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('window', False, str(e))
                logging.error(f"Error in window sensor handler: {e}")
                time.sleep(5)

    def _handle_rfid(self):
        """Handles RFID detection by the RFID sensor."""
        while True:
            try:
                status, uid = self._rfid_reader.read_card()
                if status == self._rfid_reader.rfid.MI_OK:
                    logging.info("Card detected: %s", uid)
                    status, role = self._rfid_reader.authenticate_card(uid)
                    if status == self._rfid_reader.rfid.MI_OK:
                        logging.info("Authenticated as: %s", role)
                        self.log_access_attempt(uid, True)
                        self._update_sensor_status('rfid', True)
                    else:
                        logging.warning("Unauthorized RFID access detected.")
                        self.log_access_attempt(uid, False)
                        self._update_sensor_status('rfid', True)
                time.sleep(1)
            except Exception as e:
                self._update_sensor_status('rfid', False, str(e))
                logging.error(f"Error in RFID handler: {e}")
                time.sleep(5)

    def _update_sensor_status(self, sensor_name: str, is_active: bool, error: Optional[str] = None):
        """Update the status of a sensor."""
        with self._lock:
            self._sensor_status[sensor_name] = SensorStatus(
                name=sensor_name,
                is_active=is_active,
                last_check=datetime.datetime.now(),
                error=error
            )

    def check_sensor_status(self) -> Dict:
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

    def start(self):
        """Starts the sensor handling threads."""
        self._threads = [
            threading.Thread(target=self._handle_motion),
            threading.Thread(target=self._handle_door),
            threading.Thread(target=self._handle_window),
            threading.Thread(target=self._handle_rfid)
        ]
        for thread in self._threads:
            thread.daemon = True
            thread.start()
        logging.info("All sensor threads started successfully")

    def check_intrusion(self) -> bool:
        """
        Checks for intrusion by checking the status of the motion, door, and window sensors.
        Implements a cooldown period to prevent rapid-fire alerts.

        Returns:
            bool: True if intrusion is detected, otherwise False.
        """
        current_time = datetime.datetime.now()
        if (current_time - self._last_event_time).total_seconds() < self._event_cooldown:
            return False

        try:
            motion_status = self._motion_sensor.check_motion()
            door_status = self._door_sensor.check_door()
            window_status = self._window_sensor.check_window()

            if motion_status or door_status or window_status:
                self._last_event_time = current_time
                logging.warning("Intrusion detected!")
                return True
            return False
        except Exception as e:
            logging.error(f"Error checking for intrusion: {e}")
            return False

    def check_rfid(self) -> bool:
        """
        Checks for unauthorized access by checking the RFID sensor.
        Implements a cooldown period to prevent rapid-fire alerts.

        Returns:
            bool: True if unauthorized access is detected, otherwise False.
        """
        current_time = datetime.datetime.now()
        if (current_time - self._last_event_time).total_seconds() < self._event_cooldown:
            return False

        try:
            status, uid = self._rfid_reader.read_card()
            if status == self._rfid_reader.rfid.MI_OK:
                logging.info("Card detected: %s", uid)
                status, role = self._rfid_reader.authenticate_card(uid)
                if status == self._rfid_reader.rfid.MI_OK:
                    logging.info("Authenticated as: %s", role)
                    self.log_access_attempt(uid, True)
                    return False
                else:
                    self._last_event_time = current_time
                    logging.warning("Unauthorized RFID access detected.")
                    self.log_access_attempt(uid, False)
                    return True
            return False
        except Exception as e:
            logging.error(f"Error checking RFID: {e}")
            return False

    def log_access_attempt(self, card_uid, authorized):
        """
        Logs each access attempt with a timestamp.

        Args:
            card_uid (tuple): The UID of the RFID card.
            authorized (bool): Whether the access was authorized.
        """
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = "Authorized" if authorized else "Unauthorized"
        logging.info("Access attempt: UID=%s, Status=%s, Timestamp=%s", card_uid, status, timestamp)

    def cleanup(self):
        """Clean up resources used by all sensors."""
        try:
            self._motion_sensor.cleanup()
            self._door_sensor.cleanup()
            self._window_sensor.cleanup()
            self._rfid_reader.cleanup()
            logging.info("Cleaned up all sensor resources.")
        except Exception as e:
            logging.error(f"Error during sensor cleanup: {e}")

if __name__ == "__main__":
    """
    Main method to test the sensor manager.
    """
    sensor_manager = SensorManager(verbose=True)
    try:
        sensor_manager.start()
        while True:
            sensor_manager.check_intrusion()
            sensor_manager.check_rfid()
            time.sleep(1)
    except KeyboardInterrupt:
        sensor_manager.cleanup()
        logging.info("Exiting...")

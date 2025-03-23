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

from typing import List
from motion import MotionSensorHandler, DoorSensorHandler, WindowSensorHandler
from rfid import RFIDReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SensorManager:
    """Class to manage all sensors."""

    def __init__(self, verbose: bool):
        self._motion_sensor = MotionSensorHandler(4, verbose)
        self._door_sensor = DoorSensorHandler(17, verbose)
        self._window_sensor = WindowSensorHandler(27, verbose)
        self._rfid_reader = RFIDReader()
        self._threads: List[threading.Thread] = []

    def _handle_motion(self):
        """Handles motion detection by the motion sensor."""
        while True:
            if self._motion_sensor.sensor.motion_detected:
                self._motion_sensor.on_motion()
            else:
                self._motion_sensor.on_no_motion()
            time.sleep(1)

    def _handle_door(self):
        """Handles door detection by the door sensor."""
        while True:
            if self._door_sensor.on_open:
                self._door_sensor.on_open()
            else:
                self._door_sensor.on_close()
            time.sleep(1)

    def _handle_window(self):
        """Handles window detection by the window sensor."""
        while True:
            if self._window_sensor.on_open:
                self._window_sensor.on_open()
            else:
                self._window_sensor.on_close()
            time.sleep(1)

    def _handle_rfid(self):
        """Handles RFID detection by the RFID sensor."""
        while True:
            status, uid = self._rfid_reader.read_card()
            if status == self._rfid_reader.rfid.MI_OK:
                logging.info("Card detected: %s", uid)
                status, role = self._rfid_reader.authenticate_card(uid)
                if status == self._rfid_reader.rfid.MI_OK:
                    logging.info("Authenticated as: %s", role)
                    self.log_access_attempt(uid, True)
                else:
                    logging.warning("Unauthorized RFID access detected.")
                    self.log_access_attempt(uid, False)
            time.sleep(1)

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

    def check_intrusion(self) -> bool:
        """
        Checks for intrusion by checking the status of the motion, door, and window sensors.

        Returns:
            bool: True if intrusion is detected, otherwise False.
        """
        motion_status = self._motion_sensor.check_motion()
        door_status = self._door_sensor.check_door()
        window_status = self._window_sensor.check_window()
        if motion_status or door_status or window_status:
            logging.warning("Intrusion detected!")
            return True
        return False

    def check_rfid(self) -> bool:
        """
        Checks for unauthorized access by checking the RFID sensor.

        Returns:
            bool: True if unauthorized access is detected, otherwise False.
        """
        status, uid = self._rfid_reader.read_card()
        if status == self._rfid_reader.rfid.MI_OK:
            logging.info("Card detected: %s", uid)
            status, role = self._rfid_reader.authenticate_card(uid)
            if status == self._rfid_reader.rfid.MI_OK:
                logging.info("Authenticated as: %s", role)
                self.log_access_attempt(uid, True)
            else:
                logging.warning("Unauthorized RFID access detected.")
                self.log_access_attempt(uid, False)
            return True
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
        self._motion_sensor.cleanup()
        self._door_sensor.cleanup()
        self._window_sensor.cleanup()
        self._rfid_reader.cleanup()
        logging.info("Cleaned up all sensor resources.")

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

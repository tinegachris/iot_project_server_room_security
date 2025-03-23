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

    def check_intrusion(self) -> bool:
        """
        Polls the sensor states to determine if an intrusion is detected.

        Returns:
            bool: True if the motion sensor, door sensor, or window sensor is triggered,
                  otherwise False.
        """
        sensors = [
            (self._motion_sensor.sensor.motion_detected, "Motion sensor triggered."),
            (self._door_sensor.sensor.is_pressed, "Door sensor triggered."),
            (self._window_sensor.sensor.is_pressed, "Window sensor triggered.")
        ]

        for sensor_triggered, message in sensors:
            if sensor_triggered:
                logging.info(message)
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

    def check_rfid(self) -> bool:
        """
        Polls the RFID sensor to determine if an unauthorized RFID tag is detected.

        Returns:
            bool: True if an unauthorized RFID access is detected, otherwise False.
        """
        status, uid = self._rfid_reader.read_card()
        if status == self._rfid_reader.rfid.MI_OK:
            logging.info("Card detected: %s", uid)
            status, role = self._rfid_reader.authenticate_card(uid)
            if status == self._rfid_reader.rfid.MI_OK:
                logging.info("Authenticated as: %s", role)
                self.log_access_attempt(uid, True)
                return False
            else:
                logging.warning("Unauthorized RFID access detected.")
                self.log_access_attempt(uid, False)
                return True
        return False

    def cleanup(self):
        """Clean up GPIO resources."""
        self._rfid_reader.cleanup()

if __name__ == "__main__":
    """
    Simple test loop to print sensor status.
    Press Ctrl+C to exit.
    """
    sensor_manager = SensorManager(verbose=True)
    try:
        logging.info("Starting sensor module test. Press Ctrl+C to exit.")
        while True:
            intrusion = sensor_manager.check_intrusion()
            rfid_issue = sensor_manager.check_rfid()

            if intrusion:
                print("Intrusion detected!")
            else:
                print("No intrusion detected.")

            if rfid_issue:
                print("Unauthorized RFID access detected!")
            else:
                print("RFID sensor normal.")

            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Exiting sensor module test.")
    finally:
        sensor_manager.cleanup()

#!/home/admin/iot_project_server_room_security/venv/bin/python3
"""
sensors.py

This module interfaces with physical sensors connected to the Raspberry Pi.
It currently supports:
        - A PIR motion sensor (to detect motion)
        - A door sensor (e.g., a reed switch on a door)
        - A window sensor (e.g., a reed switch on a window)
        - An RFID reader for access control

The function `check_intrusion()` polls the sensor states and returns True if any of the
motion, door, or window sensors are triggered.

The function `check_rfid()` polls the RFID sensor and returns True if an unauthorized
RFID tag is detected.

Dependencies:
        - gpiozero library (install with `pip install gpiozero`)
        - MFRC522 library (install with `pip install MFRC522`) for RFID sensor

Make sure your sensors are wired to the correct GPIO pins as defined below.
"""

import time
import logging
import datetime
from gpiozero import MotionSensor, Button
from rfid import MFRC522

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Sensor Pin Configuration ---
# Adjust these pin numbers to match your hardware wiring.
MOTION_SENSOR_PIN = 4    # GPIO pin for the PIR motion sensor
DOOR_SENSOR_PIN   = 17   # GPIO pin for the door/contact sensor
WINDOW_SENSOR_PIN = 27   # GPIO pin for the window sensor

# Initialize sensor objects
try:
    motion_sensor = MotionSensor(MOTION_SENSOR_PIN)
    door_sensor = Button(DOOR_SENSOR_PIN)
    window_sensor = Button(WINDOW_SENSOR_PIN)
except Exception as e:
    logging.error("Failed to initialize sensors: %s", e)
    raise

# Initialize RFID reader
try:
    MIFAREReader = MFRC522()
except Exception as e:
    logging.error("Failed to initialize RFID reader: %s", e)
    MIFAREReader = None

# Define authorized RFID cards
AUTHORIZED_CARDS = {
    (5, 74, 28, 185, 234): {"name": "Card A", "role": "Admin"},
    (83, 164, 247, 164, 164): {"name": "Card B", "role": "User"},
    (20, 38, 121, 207, 132): {"name": "Card C", "role": "Guest"}
}

def check_intrusion():
    """
    Polls the sensor states to determine if an intrusion is detected.

    Returns:
        bool: True if the motion sensor, door sensor, or window sensor is triggered,
              otherwise False.
    """
    sensors = [
        (motion_sensor.motion_detected, "Motion sensor triggered."),
        (door_sensor.is_pressed, "Door sensor triggered."),
        (window_sensor.is_pressed, "Window sensor triggered.")
    ]

    for sensor_triggered, message in sensors:
        if sensor_triggered:
            logging.info(message)
            return True
    return False

def log_access_attempt(card_uid, authorized):
    """
    Logs each access attempt with a timestamp.

    Args:
        card_uid (tuple): The UID of the RFID card.
        authorized (bool): Whether the access was authorized.
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "Authorized" if authorized else "Unauthorized"
    logging.info("Access attempt: UID=%s, Status=%s, Timestamp=%s", card_uid, status, timestamp)

def check_rfid():
    """
    Polls the RFID sensor to determine if an unauthorized RFID tag is detected.

    Returns:
        bool: True if an unauthorized RFID access is detected, otherwise False.
    """
    if MIFAREReader is None:
        return False

    status, TagType = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
    if status == MIFAREReader.MI_OK:
        logging.info("Card detected")
        status, backData = MIFAREReader.MFRC522_Anticoll()
        if status == MIFAREReader.MI_OK:
            card_uid = tuple(backData[:5])
            logging.info("Card read UID: %s", card_uid)
            if card_uid in AUTHORIZED_CARDS:
                card_info = AUTHORIZED_CARDS[card_uid]
                logging.info("Authorized access: %s, Role: %s", card_info["name"], card_info["role"])
                log_access_attempt(card_uid, True)
                return False
            else:
                logging.warning("Unauthorized RFID access detected.")
                log_access_attempt(card_uid, False)
                return True
    return False

if __name__ == "__main__":
    """
    Simple test loop to print sensor status.
    Press Ctrl+C to exit.
    """
    try:
        logging.info("Starting sensor module test. Press Ctrl+C to exit.")
        while True:
            intrusion = check_intrusion()
            rfid_issue = check_rfid()

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
        if MIFAREReader:
            MIFAREReader.GPIO_CLEAN()

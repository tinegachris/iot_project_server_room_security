#!/usr/bin/env python3
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
  - gpiozero

Make sure your sensors are wired to the correct GPIO pins as defined below.
"""

import time
import logging
from gpiozero import MotionSensor, Button

# Configure logging for debugging and operational insights
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Sensor Pin Configuration ---
# Adjust these pin numbers to match your hardware wiring.
MOTION_SENSOR_PIN = 4    # Example GPIO pin for the PIR motion sensor
DOOR_SENSOR_PIN   = 17   # Example GPIO pin for the door/contact sensor
WINDOW_SENSOR_PIN = 27   # Example GPIO pin for the window sensor

# Initialize sensor objects
motion_sensor = MotionSensor(MOTION_SENSOR_PIN)
door_sensor   = Button(DOOR_SENSOR_PIN)
window_sensor = Button(WINDOW_SENSOR_PIN)

def check_intrusion():
    """
    Polls the sensor states to determine if an intrusion is detected.

    Returns:
        bool: True if the motion sensor, door sensor, or window sensor is triggered,
              otherwise False.

    Note:
        - `motion_sensor.motion_detected` returns True if motion is detected.
        - `door_sensor.is_pressed` returns True if the door sensor is activated.
        - `window_sensor.is_pressed` returns True if the window sensor is activated.
    """
    if motion_sensor.motion_detected:
        logging.info("Motion sensor triggered.")
        return True
    elif door_sensor.is_pressed:
        logging.info("Door sensor triggered.")
        return True
    elif window_sensor.is_pressed:
        logging.info("Window sensor triggered.")
        return True
    else:
        return False

def check_rfid():
    """
    Polls the RFID sensor to determine if an unauthorized RFID tag is detected.

    Returns:
        bool: True if an unauthorized RFID access is detected, otherwise False.

    Note:
        This is a placeholder implementation. Integration with an actual RFID
        reader (e.g., using an MFRC522 module) should replace this simulation.
    """
    # Placeholder simulation: Replace with actual RFID reading logic.
    unauthorized_access = False
    # Example pseudocode for actual implementation:
    # tag_id = rfid_reader.read_tag()
    # allowed_tags = {"TAG123", "TAG456", "TAG789"}
    # if tag_id and tag_id not in allowed_tags:
    #     unauthorized_access = True

    if unauthorized_access:
        logging.info("RFID unauthorized access detected.")
    return unauthorized_access

if __name__ == "__main__":
    # Simple test loop to print sensor status
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

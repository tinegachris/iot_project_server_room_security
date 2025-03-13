#!/usr/bin/env python3
"""
sensors.py

This module interfaces with physical sensors connected to the Raspberry Pi.
It currently supports:
  - A PIR motion sensor (to detect motion)
  - A door sensor (e.g. a reed switch on a door)

The function `check_intrusion()` polls the sensor states and returns True if an
intrusion is detected (i.e. motion is detected or the door is open).

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
MOTION_SENSOR_PIN = 4   # Example GPIO pin for the PIR motion sensor
DOOR_SENSOR_PIN   = 17  # Example GPIO pin for the door/contact sensor

# Initialize sensor objects
motion_sensor = MotionSensor(MOTION_SENSOR_PIN)
door_sensor   = Button(DOOR_SENSOR_PIN)

def check_intrusion():
    """
    Polls the sensor states to determine if an intrusion is detected.

    Returns:
        bool: True if either the motion sensor or the door sensor is triggered,
              otherwise False.

    Note:
        - `motion_sensor.motion_detected` returns True if motion is detected.
        - `door_sensor.is_pressed` returns True if the door sensor is activated.
    """
    if motion_sensor.motion_detected:
        logging.info("Motion sensor triggered.")
        return True
    elif door_sensor.is_pressed:
        logging.info("Door sensor triggered.")
        return True
    else:
        return False

if __name__ == "__main__":
    # Simple test loop to print sensor status
    try:
        logging.info("Starting sensor module test. Press Ctrl+C to exit.")
        while True:
            if check_intrusion():
                print("Intrusion detected!")
            else:
                print("No intrusion detected.")
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Exiting sensor module test.")

#!/home/admin/iot_project_server_room_security/venv/bin/python3
"""
motion.py

This module handles
  - A PIR motion sensor (to detect motion)
  - A door sensor (e.g., a reed switch on a door)
  - A window sensor (e.g., a reed switch on a window)

"""

import logging
import argparse
from gpiozero import MotionSensor as PIRMotionSensor
from gpiozero import Button as OpenCloseSensor
from gpiozero import LED
from time import sleep
from typing import Type

class SensorHandler:
    """Base class to handle sensors with LEDs."""

    def __init__(self, gpio_pin: int, led_pin: int, verbose: bool):
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        logging.info(f"[{self.__class__.__name__}]: Initializing - GPIO_PIN: {gpio_pin}, LED_PIN: {led_pin}, VERBOSE: {verbose}")

        self.sensor = self.create_sensor(gpio_pin)
        self.indicator_led = LED(led_pin)

    def create_sensor(self, gpio_pin: int) -> Type:
        """Create the sensor instance. To be implemented by subclasses."""
        raise NotImplementedError

class MotionSensorHandler(SensorHandler):
    """Class to handle motion detection using a PIR sensor."""

    def __init__(self, gpio_pin: int, verbose: bool):
        super().__init__(gpio_pin, led_pin=22, verbose=verbose)
        self.sensor.when_motion = self.on_motion
        self.sensor.when_no_motion = self.on_no_motion

    def create_sensor(self, gpio_pin: int) -> PIRMotionSensor:
        return PIRMotionSensor(gpio_pin, queue_len=1, sample_rate=1)

    def on_motion(self) -> None:
        """Callback for when motion is detected."""
        logging.info("[Motion]: Motion detected!")
        self.indicator_led.on()

    def on_no_motion(self) -> None:
        """Callback for when no motion is detected."""
        logging.info("[Motion]: No motion detected!")
        self.indicator_led.off()

class DoorSensorHandler(SensorHandler):
    """Class to handle door sensors using reed switches."""

    def __init__(self, gpio_pin: int, verbose: bool):
        super().__init__(gpio_pin, led_pin=23, verbose=verbose)
        self.sensor.when_pressed = self.on_open
        self.sensor.when_released = self.on_close

    def create_sensor(self, gpio_pin: int) -> OpenCloseSensor:
        return OpenCloseSensor(gpio_pin, pull_up=True, bounce_time=0.1)

    def on_open(self) -> None:
        """Callback for when the door is opened."""
        logging.info("[DoorSensor]: Door opened!")
        self.indicator_led.on()

    def on_close(self) -> None:
        """Callback for when the door is closed."""
        logging.info("[DoorSensor]: Door closed!")
        self.indicator_led.off()

class WindowSensorHandler(SensorHandler):
    """Class to handle window sensors using reed switches."""

    def __init__(self, gpio_pin: int, verbose: bool):
        super().__init__(gpio_pin, led_pin=24, verbose=verbose)
        self.sensor.when_pressed = self.on_open
        self.sensor.when_released = self.on_close

    def create_sensor(self, gpio_pin: int) -> OpenCloseSensor:
        return OpenCloseSensor(gpio_pin, pull_up=True, bounce_time=0.1)

    def on_open(self) -> None:
        """Callback for when the window is opened."""
        logging.info("[WindowSensor]: Window opened!")
        self.indicator_led.on()

    def on_close(self) -> None:
        """Callback for when the window is closed."""
        logging.info("[WindowSensor]: Window closed!")
        self.indicator_led.off()

def main() -> None:
    """Main function to initialize sensor handlers and start monitoring."""
    parser = argparse.ArgumentParser(description="IoT Based Server Room Monitoring Control")
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Initialize sensor handlers
    motion_sensor = MotionSensorHandler(gpio_pin=4, verbose=args.verbose)
    door_sensor = DoorSensorHandler(gpio_pin=17, verbose=args.verbose)
    window_sensor = WindowSensorHandler(gpio_pin=27, verbose=args.verbose)

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        logging.info("Exiting...")

if __name__ == "__main__":
    main()

#!/home/admin/iot_project_server_room_security/venv/bin/python3
"""
motion.py

This module handles various sensors for server room monitoring:
- PIR motion sensor for motion detection
- Door sensor (reed switch) for door state
- Window sensor (reed switch) for window state

Each sensor has an associated LED indicator for visual feedback.
"""

import logging
import argparse
from dataclasses import dataclass
from typing import Optional, Type, Callable
from gpiozero import MotionSensor as PIRMotionSensor
from gpiozero import Button as OpenCloseSensor
from gpiozero import LED
from time import sleep
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SensorConfig:
    """Configuration for a sensor."""
    gpio_pin: int
    led_pin: int
    name: str
    verbose: bool

class SensorHandler:
    """Base class to handle sensors with LEDs."""

    def __init__(self, config: SensorConfig):
        """Initialize the sensor handler with configuration."""
        if config.verbose:
            logger.setLevel(logging.DEBUG)

        logger.info("[%s]: Initializing - GPIO_PIN: %d, LED_PIN: %d",
                   config.name, config.gpio_pin, config.led_pin)

        self.config = config
        self.sensor = self.create_sensor(config.gpio_pin)
        self.indicator_led = LED(config.led_pin)
        self.setup_callbacks()

    def create_sensor(self, gpio_pin: int) -> Type:
        """Create the sensor instance. To be implemented by subclasses."""
        raise NotImplementedError

    def setup_callbacks(self) -> None:
        """Setup sensor callbacks. To be implemented by subclasses."""
        raise NotImplementedError

    def cleanup(self) -> None:
        """Clean up the resources used by the sensor."""
        try:
            self.sensor.close()
            logger.info("[%s]: Cleanup completed", self.config.name)
        except Exception as e:
            logger.error("[%s]: Error during cleanup: %s", self.config.name, e)

class MotionSensorHandler(SensorHandler):
    """Class to handle motion detection using a PIR sensor."""

    def create_sensor(self, gpio_pin: int) -> PIRMotionSensor:
        """Create a PIR motion sensor instance."""
        return PIRMotionSensor(gpio_pin, queue_len=1, sample_rate=1)

    def setup_callbacks(self) -> None:
        """Setup motion detection callbacks."""
        self.sensor.when_motion = self.on_motion
        self.sensor.when_no_motion = self.on_no_motion

    def on_motion(self) -> None:
        """Callback for when motion is detected."""
        logger.info("[%s]: Motion detected!", self.config.name)
        self.indicator_led.on()

    def on_no_motion(self) -> None:
        """Callback for when no motion is detected."""
        logger.info("[%s]: No motion detected!", self.config.name)
        self.indicator_led.off()

    def check_motion(self) -> bool:
        """Check the status of the motion sensor."""
        status = self.sensor.motion_detected
        logger.debug("[%s]: Check motion status - %s",
                    self.config.name, 'Detected' if status else 'Not detected')
        return status

class OpenCloseSensorHandler(SensorHandler):
    """Base class for door and window sensors using reed switches."""

    def create_sensor(self, gpio_pin: int) -> OpenCloseSensor:
        """Create a reed switch sensor instance."""
        return OpenCloseSensor(gpio_pin, pull_up=True, bounce_time=0.1)

    def setup_callbacks(self) -> None:
        """Setup open/close detection callbacks."""
        self.sensor.when_pressed = self.on_open
        self.sensor.when_released = self.on_close

    def on_open(self) -> None:
        """Callback for when the sensor is triggered (opened)."""
        logger.info("[%s]: Opened!", self.config.name)
        self.indicator_led.on()

    def on_close(self) -> None:
        """Callback for when the sensor is released (closed)."""
        logger.info("[%s]: Closed!", self.config.name)
        self.indicator_led.off()

    def check_state(self) -> bool:
        """Check the current state of the sensor."""
        status = self.sensor.is_pressed
        logger.debug("[%s]: Check state - %s",
                    self.config.name, 'Opened' if status else 'Closed')
        return status

class DoorSensorHandler(OpenCloseSensorHandler):
    """Class to handle door sensors using reed switches."""
    pass

class WindowSensorHandler(OpenCloseSensorHandler):
    """Class to handle window sensors using reed switches."""
    pass

def main() -> None:
    """Main function to initialize sensor handlers and start monitoring."""
    parser = argparse.ArgumentParser(description="IoT Based Server Room Monitoring Control")
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    # Get GPIO pin configuration from environment variables
    motion_pin = int(os.getenv("MOTION_SENSOR_PIN", "4"))
    door_pin = int(os.getenv("DOOR_SENSOR_PIN", "17"))
    window_pin = int(os.getenv("WINDOW_SENSOR_PIN", "27"))
    motion_led_pin = int(os.getenv("MOTION_LED_PIN", "22"))
    door_led_pin = int(os.getenv("DOOR_LED_PIN", "23"))
    window_led_pin = int(os.getenv("WINDOW_LED_PIN", "24"))

    # Initialize sensor handlers
    sensors = [
        MotionSensorHandler(SensorConfig(motion_pin, motion_led_pin, "Motion", args.verbose)),
        DoorSensorHandler(SensorConfig(door_pin, door_led_pin, "Door", args.verbose)),
        WindowSensorHandler(SensorConfig(window_pin, window_led_pin, "Window", args.verbose))
    ]

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        logger.info("Exiting...")
    except Exception as e:
        logger.error("Unexpected error: %s", e)
    finally:
        for sensor in sensors:
            sensor.cleanup()

if __name__ == "__main__":
    main()

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
import os
import time
import random
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if running on Raspberry Pi
try:
    IS_RASPBERRY_PI = platform.machine().startswith('arm')
    if IS_RASPBERRY_PI:
        from gpiozero import MotionSensor as PIRMotionSensor
        from gpiozero import Button as OpenCloseSensor
        from gpiozero import LED
        logger.info("Running on Raspberry Pi with real GPIO hardware")
    else:
        logger.warning("Not running on Raspberry Pi, using mock implementation")
except ImportError:
    IS_RASPBERRY_PI = False
    logger.warning("Running in mock mode - no Raspberry Pi GPIO hardware detected")

@dataclass
class SensorConfig:
    """Configuration for a sensor."""
    gpio_pin: int
    led_pin: int
    name: str
    verbose: bool

class MockSensor:
    """Mock sensor implementation for non-Raspberry Pi systems."""
    
    def __init__(self, pin: int, pull_up: bool = True, bounce_time: float = 0.1):
        """Initialize the mock sensor."""
        self.pin = pin
        self.pull_up = pull_up
        self.bounce_time = bounce_time
        self._value = False
        self._last_change = 0
        self._callbacks = []
        
    def is_pressed(self) -> bool:
        """Get the current state of the sensor."""
        return self._value
        
    def when_pressed(self, callback: Callable) -> None:
        """Register a callback for when the sensor is pressed."""
        self._callbacks.append(('pressed', callback))
        
    def when_released(self, callback: Callable) -> None:
        """Register a callback for when the sensor is released."""
        self._callbacks.append(('released', callback))
        
    def _trigger_callbacks(self) -> None:
        """Trigger registered callbacks."""
        current_time = time.time()
        if current_time - self._last_change < self.bounce_time:
            return
            
        for event_type, callback in self._callbacks:
            if (event_type == 'pressed' and self._value) or \
               (event_type == 'released' and not self._value):
                callback()
                
        self._last_change = current_time
        
    def update_state(self, new_value: bool) -> None:
        """Update the sensor state and trigger callbacks if changed."""
        if new_value != self._value:
            self._value = new_value
            self._trigger_callbacks()
            
    def close(self) -> None:
        """Clean up resources."""
        self._callbacks.clear()

class MockLED:
    """Mock LED implementation for non-Raspberry Pi systems."""
    
    def __init__(self, pin: int):
        """Initialize the mock LED."""
        self.pin = pin
        self._value = False
        
    def on(self) -> None:
        """Turn the LED on."""
        self._value = True
        logger.debug("Mock LED %d turned on", self.pin)
        
    def off(self) -> None:
        """Turn the LED off."""
        self._value = False
        logger.debug("Mock LED %d turned off", self.pin)
        
    def close(self) -> None:
        """Clean up resources."""
        pass

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
        self.indicator_led = self.create_led(config.led_pin)
        self.setup_callbacks()

    def create_sensor(self, gpio_pin: int) -> Type:
        """Create the sensor instance. To be implemented by subclasses."""
        raise NotImplementedError

    def create_led(self, gpio_pin: int) -> Type:
        """Create the LED instance."""
        if IS_RASPBERRY_PI:
            return LED(gpio_pin)
        return MockLED(gpio_pin)

    def setup_callbacks(self) -> None:
        """Setup sensor callbacks. To be implemented by subclasses."""
        raise NotImplementedError

    def cleanup(self) -> None:
        """Clean up the resources used by the sensor."""
        try:
            self.sensor.close()
            self.indicator_led.close()
            logger.info("[%s]: Cleanup completed", self.config.name)
        except Exception as e:
            logger.error("[%s]: Error during cleanup: %s", self.config.name, e)

class MotionSensorHandler(SensorHandler):
    """Class to handle motion detection using a PIR sensor."""

    def create_sensor(self, gpio_pin: int) -> Type:
        """Create a PIR motion sensor instance."""
        if IS_RASPBERRY_PI:
            return PIRMotionSensor(gpio_pin, queue_len=1, sample_rate=1)
        return MockSensor(gpio_pin)

    def setup_callbacks(self) -> None:
        """Setup motion detection callbacks."""
        if IS_RASPBERRY_PI:
            self.sensor.when_motion = self.on_motion
            self.sensor.when_no_motion = self.on_no_motion
        else:
            self.sensor.when_pressed = self.on_motion
            self.sensor.when_released = self.on_no_motion

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
        if IS_RASPBERRY_PI:
            status = self.sensor.motion_detected
        else:
            # Simulate random motion detection
            status = random.random() < 0.1  # 10% chance of motion
            self.sensor.update_state(status)
            
        logger.debug("[%s]: Check motion status - %s",
                    self.config.name, 'Detected' if status else 'Not detected')
        return status

class OpenCloseSensorHandler(SensorHandler):
    """Base class for door and window sensors using reed switches."""

    def create_sensor(self, gpio_pin: int) -> Type:
        """Create a reed switch sensor instance."""
        if IS_RASPBERRY_PI:
            return OpenCloseSensor(gpio_pin, pull_up=True, bounce_time=0.1)
        return MockSensor(gpio_pin)

    def setup_callbacks(self) -> None:
        """Setup open/close detection callbacks."""
        if IS_RASPBERRY_PI:
            self.sensor.when_pressed = self.on_open
            self.sensor.when_released = self.on_close
        else:
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
        if IS_RASPBERRY_PI:
            status = self.sensor.is_pressed
        else:
            # Simulate random open/close state
            status = random.random() < 0.05  # 5% chance of being open
            self.sensor.update_state(status)
            
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
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Exiting...")
    except Exception as e:
        logger.error("Unexpected error: %s", e)
    finally:
        for sensor in sensors:
            sensor.cleanup()

if __name__ == "__main__":
    main()

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
from typing import Optional, Type, Callable, Any
import os
import time
import random
import platform
from gpiozero import MotionSensor as PIRMotionSensor, Button as OpenCloseSensor, LED
from gpiozero import InputDevice

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if running on Raspberry Pi
try:
    IS_RASPBERRY_PI = platform.machine().startswith(('arm', 'aarch64'))
    if IS_RASPBERRY_PI:
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
    led_pin: Optional[int] = None # Optional LED pin
    name: str = "Sensor"
    verbose: bool = False

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

class BaseSensorHandler:
    """Base class to handle sensors with optional LEDs."""

    def __init__(self, config: SensorConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if config.verbose:
            self.logger.setLevel(logging.DEBUG)
        self.logger.info(f"[{config.name}]: Initializing - GPIO_PIN: {config.gpio_pin}, LED_PIN: {config.led_pin}")

        self.sensor = None # Placeholder for gpiozero sensor object
        self.led = None    # Placeholder for gpiozero LED object

        # Initialize LED if configured
        if config.led_pin is not None:
            try:
                self.led = LED(config.led_pin)
                self.led.off() # Start with LED off
            except Exception as e:
                self.logger.error(f"[{config.name}]: Failed to initialize LED on pin {config.led_pin}: {e}")
                self.led = None # Ensure LED is None if init fails

    def create_sensor(self, gpio_pin: int) -> Any:
        """Placeholder method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement create_sensor")

    def cleanup(self):
        """Clean up resources (LED and Sensor)."""
        self.logger.debug(f"[{self.config.name}]: Starting base cleanup...")
        # Close Sensor object first
        if self.sensor:
            sensor_instance = self.sensor
            self.sensor = None # Clear reference before closing
            self.logger.info(f"[{self.config.name}]: Closing sensor object on pin {self.config.gpio_pin}")
            try:
                # Detach any remaining internal callbacks if possible (gpiozero handles most)
                if hasattr(sensor_instance, 'close'):
                    sensor_instance.close()
                self.logger.debug(f"[{self.config.name}]: Sensor object closed.")
            except Exception as e:
                 self.logger.error(f"[{self.config.name}]: Error closing sensor object: {e}")

        # Close LED object
        if self.led:
            led_instance = self.led
            self.led = None # Clear reference before closing
            self.logger.info(f"[{self.config.name}]: Cleaning up LED on pin {self.config.led_pin}")
            try:
                if hasattr(led_instance, 'close'):
                    led_instance.close()
                self.logger.debug(f"[{self.config.name}]: LED closed.")
            except Exception as e:
                self.logger.error(f"[{self.config.name}]: Error closing LED: {e}")

        self.logger.info(f"[{self.config.name}]: Base cleanup finished.")

    def _flash_led(self, times=1, duration=0.1):
        """Flash the associated LED briefly."""
        if self.led:
            try:
                self.led.blink(on_time=duration, off_time=duration, n=times, background=True)
            except Exception as e:
                 self.logger.warning(f"[{self.config.name}]: Could not flash LED: {e}")

class MotionSensorHandler(BaseSensorHandler):
    """Handles PIR motion sensor."""
    def __init__(self, config: SensorConfig):
        super().__init__(config)
        try:
            self.sensor = self.create_sensor(config.gpio_pin)
            self.sensor.when_motion = self.on_motion_detected
            self.sensor.when_no_motion = self.on_motion_stopped
            self.logger.info(f"[{config.name}]: PIR Motion sensor initialized and callbacks attached.")
        except Exception as e:
            self.logger.error(f"[{config.name}]: Failed to initialize PIR sensor on pin {config.gpio_pin}: {e}")
            self.cleanup() # Attempt cleanup if init fails
            raise # Re-raise exception

    def create_sensor(self, gpio_pin: int):
        # Using PIR Motion Sensor for potentially better handling than basic MotionSensor
        return PIRMotionSensor(gpio_pin, queue_len=10, sample_rate=5, threshold=0.5)

    def on_motion_detected(self):
        self.logger.info(f"[{self.config.name}]: Motion DETECTED")
        self._flash_led(times=2)
        # Callback handled by SensorManager polling check_motion

    def on_motion_stopped(self):
        self.logger.info(f"[{self.config.name}]: Motion STOPPED")
        if self.led:
            self.led.off()

    def check_motion(self) -> bool:
        """Check if motion is currently detected."""
        if not self.sensor:
            self.logger.warning(f"[{self.config.name}]: Check motion called but sensor not initialized.")
            return False
        return self.sensor.is_active

    def cleanup(self):
        """Clean up motion sensor resources."""
        self.logger.debug(f"[{self.config.name}]: Starting motion sensor specific cleanup...")
        # Detach callbacks before closing sensor in base class
        if self.sensor:
            self.logger.debug(f"[{self.config.name}]: Detaching callbacks...")
            try:
                self.sensor.when_motion = None
                self.sensor.when_no_motion = None
            except Exception as e:
                 self.logger.error(f"[{self.config.name}]: Error detaching callbacks: {e}")
        super().cleanup() # Call base class cleanup
        self.logger.info(f"[{self.config.name}]: Motion sensor cleanup finished.")

class OpenCloseSensorHandler(BaseSensorHandler):
    """Base class for sensors using InputDevice (like reed switches)."""
    def __init__(self, config: SensorConfig):
        super().__init__(config)
        self._is_open = False # Internal state - kept for potential future use but check_state will use is_active directly
        try:
            self.sensor = self.create_sensor(config.gpio_pin)
            # Assuming pull_up=True means pin is LOW when closed (magnet near) and HIGH when open (magnet away)
            # is_active is True if pin is HIGH (Open)
            self._is_open = self.sensor.is_active
            # Remove callback assignments as InputDevice doesn't have when_activated/deactivated
            # self.sensor.when_activated = self._handle_opened # Pin goes HIGH
            # self.sensor.when_deactivated = self._handle_closed # Pin goes LOW
            self.logger.info(f"[{config.name}]: Open/Close sensor initialized. Initial state: {'OPEN' if self._is_open else 'CLOSED'}")
        except Exception as e:
            self.logger.error(f"[{config.name}]: Failed to initialize Open/Close sensor on pin {config.gpio_pin}: {e}")
            self.cleanup()
            raise

    def create_sensor(self, gpio_pin: int):
        # Using InputDevice with pull-up
        # bounce_time helps debounce noisy switches - removed as InputDevice doesn't support it
        # return InputDevice(gpio_pin, pull_up=True, bounce_time=0.1)
        return InputDevice(gpio_pin, pull_up=True)

    def _handle_opened(self):
        self._is_open = True
        self.logger.info(f"[{self.config.name}]: State changed to OPEN")
        self._flash_led()
        # Further action handled by SensorManager polling check_state

    def _handle_closed(self):
        self._is_open = False
        self.logger.info(f"[{self.config.name}]: State changed to CLOSED")
        if self.led:
            self.led.off()
        # Further action handled by SensorManager polling check_state

    def check_state(self) -> bool:
        """Check if the sensor is currently in the open state."""
        # Returns the internally tracked state based on callbacks - CHANGED
        # Now directly checks the sensor's active state
        if not self.sensor:
            self.logger.warning(f"[{self.config.name}]: Check state called but sensor not initialized.")
            return False # Or raise error?
        # self._is_open = self.sensor.is_active # Update internal state if needed elsewhere
        return self.sensor.is_active # is_active is True if pin is HIGH (Open)

    def cleanup(self):
        """Clean up open/close sensor resources."""
        self.logger.debug(f"[{self.config.name}]: Starting open/close sensor specific cleanup...")
        # Remove callback detachment as they are no longer assigned
        # if self.sensor:
        #     self.logger.debug(f"[{self.config.name}]: Detaching callbacks...")
        #     try:
        #         self.sensor.when_activated = None
        #         self.sensor.when_deactivated = None
        #     except Exception as e:
        #          self.logger.error(f"[{self.config.name}]: Error detaching callbacks: {e}")
        super().cleanup() # Call base class cleanup
        self.logger.info(f"[{self.config.name}]: Open/Close sensor cleanup finished.")

class DoorSensorHandler(OpenCloseSensorHandler):
    """Handles door magnetic reed switch sensor."""
    pass # Inherits functionality from OpenCloseSensorHandler

class WindowSensorHandler(OpenCloseSensorHandler):
    """Handles window magnetic reed switch sensor."""
    pass # Inherits functionality from OpenCloseSensorHandler

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

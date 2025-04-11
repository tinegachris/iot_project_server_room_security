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
    # Use platform module for consistency
    IS_RASPBERRY_PI = platform.machine().startswith(('arm', 'aarch64'))
    # IS_RASPBERRY_PI = False
    if IS_RASPBERRY_PI:
        logger.info("Running on Raspberry Pi with real GPIO hardware")
        # Import GPIOZero components only if on RPi
        from gpiozero import MotionSensor as PIRMotionSensor, Button as OpenCloseSensor, LED, InputDevice
    else:
        logger.warning("Not running on Raspberry Pi, using mock implementation")
        # Define placeholders for type hinting if needed
        PIRMotionSensor = None
        OpenCloseSensor = None
        LED = None
        InputDevice = None
except ImportError:
    IS_RASPBERRY_PI = False
    logger.warning("Running in mock mode - GPIOZero library likely not installed or platform detection failed")
    PIRMotionSensor = None
    OpenCloseSensor = None
    LED = None
    InputDevice = None

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

        self.sensor = None # Placeholder for gpiozero or mock sensor object
        self.led = None    # Placeholder for gpiozero or mock LED object

        # Initialize LED if configured
        if config.led_pin is not None:
            if IS_RASPBERRY_PI and LED is not None:
                try:
                    self.led = LED(config.led_pin)
                    self.led.off() # Start with LED off
                    self.logger.info(f"[{config.name}]: Real LED initialized on pin {config.led_pin}")
                except Exception as e:
                    self.logger.error(f"[{config.name}]: Failed to initialize real LED on pin {config.led_pin}: {e}")
                    self.led = None # Ensure LED is None if init fails
            else:
                self.logger.info(f"[{config.name}]: Initializing Mock LED on pin {config.led_pin}")
                self.led = MockLED(config.led_pin)

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
            self.logger.info(f"[{self.config.name}]: Closing sensor object on pin {self.config.gpio_pin} (Type: {type(sensor_instance).__name__})")
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
            self.logger.info(f"[{self.config.name}]: Cleaning up LED on pin {self.config.led_pin} (Type: {type(led_instance).__name__})")
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
            if IS_RASPBERRY_PI and hasattr(self.led, 'blink'): # Check if it's a real LED
                try:
                    self.led.blink(on_time=duration, off_time=duration, n=times, background=True)
                except Exception as e:
                     self.logger.warning(f"[{self.config.name}]: Could not flash real LED: {e}")
            elif isinstance(self.led, MockLED):
                self.logger.debug(f"[{self.config.name}]: Simulating flash for Mock LED on pin {self.led.pin}")
                # Mock flash: log on/off sequence (no actual timing)
                for _ in range(times):
                    self.led.on()
                    self.led.off()
            else:
                 self.logger.warning(f"[{self.config.name}]: Cannot flash LED - unknown type or not initialized.")

class MotionSensorHandler(BaseSensorHandler):
    """Handles PIR motion sensor."""
    def __init__(self, config: SensorConfig):
        super().__init__(config)
        try:
            self.sensor = self.create_sensor(config.gpio_pin)
            if IS_RASPBERRY_PI and self.sensor is not None and not isinstance(self.sensor, MockSensor):
                self.sensor.when_motion = self.on_motion_detected
                self.sensor.when_no_motion = self.on_motion_stopped
                self.logger.info(f"[{config.name}]: Real PIR Motion sensor initialized and callbacks attached.")
            elif isinstance(self.sensor, MockSensor):
                self.logger.info(f"[{config.name}]: Mock PIR Motion sensor initialized.")
            else: # Sensor creation failed
                 raise ValueError("Sensor object is None after creation attempt")
        except Exception as e:
            self.logger.error(f"[{config.name}]: Failed to initialize PIR sensor on pin {config.gpio_pin}: {e}")
            self.cleanup() # Attempt cleanup if init fails
            raise # Re-raise exception

    def create_sensor(self, gpio_pin: int):
        if IS_RASPBERRY_PI and PIRMotionSensor is not None:
            self.logger.info(f"[{self.config.name}]: Creating real PIRMotionSensor on pin {gpio_pin}")
            # Using PIR Motion Sensor for potentially better handling than basic MotionSensor
            return PIRMotionSensor(gpio_pin, queue_len=10, sample_rate=5, threshold=0.5)
        else:
            self.logger.info(f"[{self.config.name}]: Creating MockSensor for PIR on pin {gpio_pin}")
            return MockSensor(gpio_pin) # Use the MockSensor class

    def on_motion_detected(self):
        # This callback only runs if IS_RASPBERRY_PI is True
        self.logger.info(f"[{self.config.name}]: Motion DETECTED")
        self._flash_led(times=2)
        # Callback handled by SensorManager polling check_motion

    def on_motion_stopped(self):
        # This callback only runs if IS_RASPBERRY_PI is True
        self.logger.info(f"[{self.config.name}]: Motion STOPPED")
        if self.led and not isinstance(self.led, MockLED):
            self.led.off()

    def check_motion(self) -> bool:
        """Check if motion is currently detected."""
        if not self.sensor:
            self.logger.warning(f"[{self.config.name}]: Check motion called but sensor not initialized.")
            return False

        if IS_RASPBERRY_PI and hasattr(self.sensor, 'is_active'):
            return self.sensor.is_active
        elif isinstance(self.sensor, MockSensor):
            # For mock sensor, return its internal state (or simulate changes)
            # For now, let's assume it can be manually toggled or remains False
            return self.sensor.is_pressed() # Using is_pressed from MockSensor
        else:
            self.logger.warning(f"[{self.config.name}]: Unknown sensor type for check_motion: {type(self.sensor).__name__}")
            return False

    def cleanup(self):
        """Clean up motion sensor resources."""
        self.logger.debug(f"[{self.config.name}]: Starting motion sensor specific cleanup...")
        # Detach callbacks before closing sensor in base class
        if IS_RASPBERRY_PI and self.sensor and not isinstance(self.sensor, MockSensor):
            self.logger.debug(f"[{self.config.name}]: Detaching real sensor callbacks...")
            try:
                self.sensor.when_motion = None
                self.sensor.when_no_motion = None
            except Exception as e:
                 self.logger.error(f"[{self.config.name}]: Error detaching real sensor callbacks: {e}")
        super().cleanup() # Call base class cleanup
        self.logger.info(f"[{self.config.name}]: Motion sensor cleanup finished.")

class OpenCloseSensorHandler(BaseSensorHandler):
    """Base class for sensors using InputDevice (like reed switches)."""
    def __init__(self, config: SensorConfig):
        super().__init__(config)
        self._is_open = False # Internal state for consistency
        try:
            self.sensor = self.create_sensor(config.gpio_pin)
            if IS_RASPBERRY_PI and self.sensor is not None and not isinstance(self.sensor, MockSensor):
                 # Assuming pull_up=True means pin is LOW when closed (magnet near) and HIGH when open (magnet away)
                 # is_active is True if pin is HIGH (Open)
                 self._is_open = self.sensor.is_active
                 # InputDevice doesn't have when_activated/deactivated, polling is needed
                 self.logger.info(f"[{config.name}]: Real Open/Close sensor initialized. Initial state: {'OPEN' if self._is_open else 'CLOSED'}")
            elif isinstance(self.sensor, MockSensor):
                 self._is_open = self.sensor.is_pressed() # Use mock sensor state
                 self.logger.info(f"[{config.name}]: Mock Open/Close sensor initialized. Initial state: {'OPEN' if self._is_open else 'CLOSED'}")
            else:
                 raise ValueError("Sensor object is None after creation attempt")

        except Exception as e:
            self.logger.error(f"[{config.name}]: Failed to initialize Open/Close sensor on pin {config.gpio_pin}: {e}")
            self.cleanup()
            raise

    def create_sensor(self, gpio_pin: int):
        if IS_RASPBERRY_PI and InputDevice is not None:
            self.logger.info(f"[{self.config.name}]: Creating real InputDevice sensor on pin {gpio_pin}")
            # Using InputDevice with pull-up
            return InputDevice(gpio_pin, pull_up=True)
        else:
             self.logger.info(f"[{self.config.name}]: Creating MockSensor for Open/Close on pin {gpio_pin}")
             return MockSensor(gpio_pin, pull_up=True) # Use MockSensor

    # Callbacks (_handle_opened, _handle_closed) are removed as InputDevice doesn't use them directly

    def check_state(self) -> bool:
        """Check if the sensor is currently in the open state (True if open, False if closed)."""
        if not self.sensor:
            self.logger.warning(f"[{self.config.name}]: Check state called but sensor not initialized.")
            return False # Or raise error? Consider default state

        if IS_RASPBERRY_PI and hasattr(self.sensor, 'is_active'):
            # is_active is True if pin is HIGH (Open)
            current_state_is_open = self.sensor.is_active
        elif isinstance(self.sensor, MockSensor):
            current_state_is_open = self.sensor.is_pressed() # Use mock state
        else:
            self.logger.warning(f"[{self.config.name}]: Unknown sensor type for check_state: {type(self.sensor).__name__}")
            return False # Default to closed/inactive

        # Log state change if it occurs (optional, can be noisy)
        # if current_state_is_open != self._is_open:
        #     self._is_open = current_state_is_open
        #     self.logger.info(f"[{self.config.name}]: State polled as {'OPEN' if self._is_open else 'CLOSED'}")
        #     if self._is_open:
        #          self._flash_led()
        #     elif self.led and not isinstance(self.led, MockLED):
        #          self.led.off()

        self._is_open = current_state_is_open # Update internal state
        return self._is_open

    def cleanup(self):
        """Clean up open/close sensor resources."""
        self.logger.debug(f"[{self.config.name}]: Starting open/close sensor specific cleanup...")
        # No callbacks to detach for InputDevice
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

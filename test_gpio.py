# test_gpio.py (corrected)
import time
import logging
from gpiozero import Button
from gpiozero.pins.native import NativeFactory # A potential default factory
from gpiozero.pins.lgpio import LGPIOFactory  # The preferred factory if lgpio is installed and working
from gpiozero.devices import Device

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check the default pin factory being used
default_factory = Device.pin_factory
logger.info(f"Default GPIOZero pin factory: {default_factory.__class__.__name__}")
if isinstance(default_factory, LGPIOFactory):
    logger.info("lgpio factory is active.")
elif isinstance(default_factory, NativeFactory):
     logger.info("Native factory is active (often used for mock/non-Pi).")
else:
     logger.info(f"Using other factory: {type(default_factory)}")


DOOR_PIN = 17

def door_opened():
    logger.info(f"Edge detected: Pin {DOOR_PIN} triggered (opened)")

def door_closed():
    logger.info(f"Edge detected: Pin {DOOR_PIN} triggered (closed)")

try:
    logger.info(f"Initializing Button on GPIO pin {DOOR_PIN}...")
    # Use pull_up=True assuming a simple switch connecting the pin to GND when closed (door closed)
    # Adjust pull_up/pull_down based on your actual sensor wiring
    door_button = Button(DOOR_PIN, pull_up=True) # Use default factory

    logger.info("Assigning event handlers (when_pressed/when_released)...")
    # when_pressed = pin goes LOW (connected to GND) -> Door Closed
    # when_released = pin goes HIGH (disconnected from GND) -> Door Opened
    door_button.when_released = door_opened # Door opened
    door_button.when_pressed = door_closed # Door closed

    logger.info("GPIO edge detection test started. Press Ctrl+C to exit.")
    logger.info("Waiting for pin changes on GPIO %d...", DOOR_PIN)

    # Keep the script running
    while True:
        time.sleep(1)

except Exception as e:
    logger.error(f"Error during GPIO test: {e}", exc_info=True)

finally:
    logger.info("Cleaning up GPIO...")
    # No explicit cleanup needed for Button if script exits cleanly
    # but good practice if managing pins directly
    logger.info("GPIO test finished.") 
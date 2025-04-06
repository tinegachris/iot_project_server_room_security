import os
import logging
from functools import wraps
from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException, Unauthorized, Forbidden, BadRequest, InternalServerError
from dotenv import load_dotenv
import RPi.GPIO as GPIO # ✅ Import GPIO library
import atexit # ✅ To ensure GPIO cleanup
import subprocess # ✅ Import subprocess for restart

# Import necessary components from other firmware modules
# (Assuming SensorManager and CameraManager will be passed in)
# from .sensors import SensorManager
# from .camera import CameraManager

# Load environment variables (especially RASPBERRY_PI_API_KEY)
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Global placeholders for managers - these will be set by main.py
sensor_manager = None
camera_manager = None
# Add other managers if needed (e.g., rfid_reader)

# --- Authentication ---
EXPECTED_API_KEY = os.getenv("RASPBERRY_PI_API_KEY")

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not EXPECTED_API_KEY:
            logger.critical("API Key not configured on the Pi! Set RASPBERRY_PI_API_KEY.")
            raise InternalServerError("API Key not configured on server.")
        if not api_key or api_key != EXPECTED_API_KEY:
            logger.warning(f"Unauthorized API access attempt. Provided key: {api_key}")
            raise Unauthorized("Invalid or missing API Key")
        return f(*args, **kwargs)
    return decorated_function

# --- Door Lock Control --- 
# Assumes GPIO.LOW = Locked, GPIO.HIGH = Unlocked. Adjust if needed.
DOOR_LOCK_PIN = int(os.getenv("DOOR_LOCK_PIN", "25")) 
IS_GPIO_SETUP = False

def setup_door_lock():
    global IS_GPIO_SETUP
    if IS_GPIO_SETUP:
        return # Already setup
    try:
        GPIO.setmode(GPIO.BCM) # Use Broadcom pin numbering
        GPIO.setup(DOOR_LOCK_PIN, GPIO.OUT)
        # Set initial state to unlocked (HIGH)
        GPIO.output(DOOR_LOCK_PIN, GPIO.HIGH)
        IS_GPIO_SETUP = True
        logger.info(f"Door lock GPIO {DOOR_LOCK_PIN} initialized. Initial state: UNLOCKED (HIGH)")
        # Register cleanup function to run on exit
        atexit.register(gpio_cleanup)
    except RuntimeError as e:
        # Handle cases where GPIO might already be in use or setup fails
        logger.error(f"Could not set up GPIO for door lock (Pin {DOOR_LOCK_PIN}): {e}. Might need root privileges or pin conflict.")
        # Decide if this is critical - perhaps raise an exception or just log?
    except Exception as e:
        logger.error(f"Failed to setup door lock GPIO {DOOR_LOCK_PIN}: {e}")

def gpio_cleanup():
    global IS_GPIO_SETUP
    if IS_GPIO_SETUP:
        logger.info("Cleaning up door lock GPIO...")
        GPIO.cleanup(DOOR_LOCK_PIN)
        IS_GPIO_SETUP = False

def lock_door():
    if not IS_GPIO_SETUP:
        logger.error("Cannot lock door: GPIO not initialized.")
        return {"status": "error", "message": "GPIO not initialized"}
    try:
        GPIO.output(DOOR_LOCK_PIN, GPIO.LOW) # Set pin LOW to lock
        logger.info(f"Door LOCKED (GPIO {DOOR_LOCK_PIN} set LOW)")
        # Update sensor manager status if possible
        if sensor_manager:
            # Assuming sensor_manager has _update_sensor_status method
             try:
                sensor_manager._update_sensor_status('door_lock', True, data={'locked': True})
             except AttributeError:
                 logger.warning("sensor_manager does not have _update_sensor_status")
        return {"status": "success", "door_locked": True}
    except Exception as e:
        logger.error(f"Failed to lock door (GPIO {DOOR_LOCK_PIN}): {e}")
        return {"status": "error", "message": str(e)}

def unlock_door():
    if not IS_GPIO_SETUP:
        logger.error("Cannot unlock door: GPIO not initialized.")
        return {"status": "error", "message": "GPIO not initialized"}
    try:
        GPIO.output(DOOR_LOCK_PIN, GPIO.HIGH) # Set pin HIGH to unlock
        logger.info(f"Door UNLOCKED (GPIO {DOOR_LOCK_PIN} set HIGH)")
        # Update sensor manager status if possible
        if sensor_manager:
             try:
                 sensor_manager._update_sensor_status('door_lock', True, data={'locked': False})
             except AttributeError:
                 logger.warning("sensor_manager does not have _update_sensor_status")
        return {"status": "success", "door_locked": False}
    except Exception as e:
        logger.error(f"Failed to unlock door (GPIO {DOOR_LOCK_PIN}): {e}")
        return {"status": "error", "message": str(e)}

# --- Flask App Creation ---
def create_pi_api_server(sm, cm):
    """Creates the Flask app instance, injecting dependencies."""
    global sensor_manager, camera_manager
    sensor_manager = sm
    camera_manager = cm

    # Setup hardware (like door lock) before starting server
    setup_door_lock()

    app = Flask(__name__)
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False # Good practice for Flask

    # --- API Routes ---

    @app.route("/api/status", methods=['GET'])
    @require_api_key
    def get_pi_status():
        """Return overall status from SensorManager and CameraManager."""
        if not sensor_manager or not camera_manager:
             raise InternalServerError("Managers not initialized")
        try:
            sm_status = sensor_manager.get_sensor_status()
            cm_status = camera_manager.get_status() # Assuming CameraManager has get_status()
            return jsonify({
                "timestamp": datetime.now().isoformat(),
                "sensors": sm_status,
                "camera": cm_status,
                # Add more status info as needed
            })
        except Exception as e:
            logger.error(f"Error getting Pi status: {e}", exc_info=True)
            raise InternalServerError(f"Failed to get status: {e}")

    @app.route("/api/control", methods=['POST'])
    @require_api_key
    def control_pi():
        """Execute control commands."""
        if not request.is_json:
            raise BadRequest("Request must be JSON")

        data = request.get_json()
        action = data.get('action')
        params = data.get('parameters', {})

        if not action:
            raise BadRequest("Missing 'action' in request body")

        logger.info(f"Received control command: {action} with params: {params}")

        try:
            if action == "lock":
                result = lock_door()
            elif action == "unlock":
                result = unlock_door()
            elif action == "capture_image":
                if not camera_manager: raise InternalServerError("CameraManager not initialized")
                image_path, image_url = camera_manager.capture_image()
                result = {"status": "success", "image_path": image_path, "image_url": image_url}
            elif action == "record_video":
                if not camera_manager: raise InternalServerError("CameraManager not initialized")
                duration = params.get('duration', 10) # Default duration 10s
                video_path, video_url = camera_manager.record_video(duration=duration)
                result = {"status": "success", "video_path": video_path, "video_url": video_url, "duration": duration}
            elif action == "test_sensors":
                if not sensor_manager: raise InternalServerError("SensorManager not initialized")
                # Assuming SensorManager has run_sensor_test method
                test_results = sensor_manager.run_sensor_test()
                result = {"status": "success", "message": "Sensor test completed", **test_results}
            elif action == "restart_system":
                logger.warning("Restart command received via API. Restarting system in 5 seconds...")
                # Run reboot command in the background so we can return a response
                # Use subprocess.Popen for non-blocking execution
                # Ensure the user running this script has sudo privileges for reboot without password
                try:
                    subprocess.Popen(["sudo", "shutdown", "-r", "+0"]) # Immediate reboot
                    # Or: subprocess.Popen(["sleep 5 && sudo reboot now"], shell=True)
                    result = {"status": "success", "message": "System reboot initiated."}
                except FileNotFoundError:
                    logger.error("Could not execute reboot command. 'sudo' or 'shutdown' not found?")
                    raise InternalServerError("Failed to initiate reboot: command not found.")
                except Exception as e:
                    logger.error(f"Failed to initiate reboot: {e}")
                    raise InternalServerError(f"Failed to initiate reboot: {e}")
            else:
                raise BadRequest(f"Unsupported action: {action}")

            return jsonify(result)

        except HTTPException: # Re-raise known Flask/Werkzeug errors
            raise
        except Exception as e:
            logger.error(f"Error executing control action '{action}': {e}", exc_info=True)
            raise InternalServerError(f"Failed to execute action '{action}': {e}")

    # --- Error Handling ---
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
        response = e.get_response()
        response.data = json.dumps({
            "code": e.code,
            "name": e.name,
            "description": e.description,
        })
        response.content_type = "application/json"
        return response

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        """Handle unexpected errors."""
        logger.error(f"Unhandled exception in API server: {e}", exc_info=True)
        response = InternalServerError().get_response()
        response.data = json.dumps({
            "code": 500,
            "name": "Internal Server Error",
            "description": f"An unexpected error occurred: {e}",
        })
        response.content_type = "application/json"
        return response


    return app

if __name__ == '__main__':
    # This is for testing the server directly, NOT how it should be run in production
    # In production, main.py will import create_pi_api_server and run it via threading/gunicorn/waitress
    print("Starting Flask server directly for testing (Do not use in production)...")
    # Create dummy managers for testing if run directly
    class DummyManager:
        def get_sensor_status(self): return {"dummy_sensor": {"is_active": True}}
        def get_status(self): return {"dummy_cam": {"is_active": True}}
        def capture_image(self): return "/path/dummy.jpg", "http://dummy/dummy.jpg"
        def record_video(self, duration): return f"/path/dummy_{duration}s.mp4", f"http://dummy/dummy_{duration}s.mp4"
        def _update_sensor_status(self, *args, **kwargs): pass # No-op

    test_app = create_pi_api_server(DummyManager(), DummyManager())
    # Run on 0.0.0.0 to be accessible externally, port 5000 as expected by server config
    test_app.run(host='0.0.0.0', port=5000, debug=True) # Debug=True only for testing 
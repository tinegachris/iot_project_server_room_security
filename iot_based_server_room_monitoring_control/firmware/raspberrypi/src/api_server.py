import os
import logging
import json
import platform
from functools import wraps
from typing import Optional, Dict, Any, Callable, TypeVar, cast
from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException, Unauthorized, Forbidden, BadRequest, InternalServerError, NotFound
from dotenv import load_dotenv

# Platform check
IS_RPI = platform.machine().startswith(('arm', 'aarch64'))
logger = logging.getLogger(__name__ + ".platform_check")

# Type hints for GPIO and atexit
GPIO: Optional[Any] = None
atexit: Optional[Any] = None

if IS_RPI:
    try:
        import RPi.GPIO as GPIO  # type: ignore
        import atexit  # type: ignore
        logger.info("RPi.GPIO imported successfully.")
    except (RuntimeError, ModuleNotFoundError) as e:
        logger.warning(f"Failed to import RPi.GPIO: {e}. GPIO functionality will be disabled.")
        GPIO = None
        atexit = None
else:
    logger.warning("Platform check: Not running on Raspberry Pi/ARM. Hardware features will be mocked.")

import subprocess
import shutil
import psutil
from datetime import datetime

# Type variable for decorator
F = TypeVar('F', bound=Callable[..., Any])

# Import necessary components from other firmware modules
# (Assuming SensorManager and CameraManager will be passed in)
# Removed redundant manager imports

# Load environment variables (especially RASPBERRY_PI_API_KEY)
# Removed redundant load_dotenv() call

# Configure logging
logger = logging.getLogger(__name__)

# Global placeholders for managers - these will be set by main.py
sensor_manager = None
camera_manager = None
# Add other managers if needed (e.g., rfid_reader)

# --- Authentication ---
EXPECTED_API_KEY = os.getenv("RASPBERRY_PI_API_KEY")

def require_api_key(f: F) -> F:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            logger.warning("API key missing in request")
            raise Unauthorized("API key is required")

        if api_key != os.getenv('API_KEY'):
            logger.warning("Invalid API key provided")
            raise Unauthorized("Invalid API key")

        return f(*args, **kwargs)
    return cast(F, decorated_function)

# --- Door Lock Control ---
# Assumes GPIO.LOW = Locked, GPIO.HIGH = Unlocked. Adjust if needed.
DOOR_LOCK_PIN = int(os.getenv("DOOR_LOCK_PIN", "25"))
WINDOW_LOCK_PIN = int(os.getenv("WINDOW_LOCK_PIN", "24")) # Add window lock pin
IS_GPIO_SETUP = False
IS_WINDOW_GPIO_SETUP = False # Add separate flag for window

def setup_door_lock() -> None:
    """Setup GPIO for door lock control."""
    if not IS_RPI or GPIO is None:
        logger.warning("GPIO not available, door lock setup skipped")
        return

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DOOR_LOCK_PIN, GPIO.OUT)
        GPIO.output(DOOR_LOCK_PIN, GPIO.LOW)  # Start unlocked
        logger.info("Door lock GPIO setup completed")
    except Exception as e:
        logger.error(f"Failed to setup door lock GPIO: {e}")
        raise InternalServerError("Failed to initialize door lock hardware")

def setup_window_lock() -> None:
    """Setup GPIO for window lock control."""
    if not IS_RPI or GPIO is None:
        logger.warning("GPIO not available, window lock setup skipped")
        return

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(WINDOW_LOCK_PIN, GPIO.OUT)
        GPIO.output(WINDOW_LOCK_PIN, GPIO.LOW)  # Start unlocked
        logger.info("Window lock GPIO setup completed")
    except Exception as e:
        logger.error(f"Failed to setup window lock GPIO: {e}")
        raise InternalServerError("Failed to initialize window lock hardware")

def gpio_cleanup() -> None:
    """Cleanup GPIO resources."""
    if not IS_RPI or GPIO is None:
        return

    try:
        GPIO.cleanup()
        logger.info("GPIO cleanup completed")
    except Exception as e:
        logger.error(f"Error during GPIO cleanup: {e}")

# Register cleanup with atexit if available
if atexit is not None:
    atexit.register(gpio_cleanup)

def lock_door():
    if not IS_RPI or not GPIO:
        logger.warning("Mock lock: Not on RPi or GPIO unavailable.")
        # Simulate success for mock environment
        return {"status": "success", "door_locked": True, "mock": True}

    if not IS_GPIO_SETUP:
        logger.error("Cannot lock door: GPIO not initialized properly.")
        return {"status": "error", "message": "GPIO not initialized"}
    try:
        GPIO.output(DOOR_LOCK_PIN, GPIO.LOW) # Set pin LOW to lock
        logger.info(f"Door LOCKED (GPIO {DOOR_LOCK_PIN} set LOW)")
        # Update sensor manager status if possible
        if sensor_manager:
             try:
                 sensor_manager._update_sensor_status('door_lock', True, data={'locked': True})
             except AttributeError:
                 logger.warning("sensor_manager does not have _update_sensor_status")
        return {"status": "success", "door_locked": True}
    except Exception as e:
        logger.error(f"Failed to lock door (GPIO {DOOR_LOCK_PIN}): {e}")
        return {"status": "error", "message": str(e)}

def unlock_door():
    if not IS_RPI or not GPIO:
        logger.warning("Mock unlock: Not on RPi or GPIO unavailable.")
        # Simulate success for mock environment
        return {"status": "success", "door_locked": False, "mock": True}

    if not IS_GPIO_SETUP:
        logger.error("Cannot unlock door: GPIO not initialized properly.")
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

# --- Add Window Lock Functions ---
def lock_window():
    if not IS_RPI or not GPIO:
        logger.warning("Mock lock_window: Not on RPi or GPIO unavailable.")
        return {"status": "success", "window_locked": True, "mock": True}

    if not IS_WINDOW_GPIO_SETUP:
        logger.error("Cannot lock window: GPIO not initialized properly.")
        return {"status": "error", "message": "Window GPIO not initialized"}
    try:
        GPIO.output(WINDOW_LOCK_PIN, GPIO.LOW) # Set pin LOW to lock
        logger.info(f"Window LOCKED (GPIO {WINDOW_LOCK_PIN} set LOW)")
        # Update sensor manager status if possible (assuming window sensor handles 'locked' state)
        if sensor_manager:
             try:
                 sensor_manager._update_sensor_status('window', True, data={'locked': True})
             except AttributeError:
                 logger.warning("sensor_manager does not have _update_sensor_status or window sensor doesn't support 'locked' data")
        return {"status": "success", "window_locked": True}
    except Exception as e:
        logger.error(f"Failed to lock window (GPIO {WINDOW_LOCK_PIN}): {e}")
        return {"status": "error", "message": str(e)}

def unlock_window():
    if not IS_RPI or not GPIO:
        logger.warning("Mock unlock_window: Not on RPi or GPIO unavailable.")
        return {"status": "success", "window_locked": False, "mock": True}

    if not IS_WINDOW_GPIO_SETUP:
        logger.error("Cannot unlock window: GPIO not initialized properly.")
        return {"status": "error", "message": "Window GPIO not initialized"}
    try:
        GPIO.output(WINDOW_LOCK_PIN, GPIO.HIGH) # Set pin HIGH to unlock
        logger.info(f"Window UNLOCKED (GPIO {WINDOW_LOCK_PIN} set HIGH)")
        if sensor_manager:
             try:
                 sensor_manager._update_sensor_status('window', True, data={'locked': False})
             except AttributeError:
                 logger.warning("sensor_manager does not have _update_sensor_status or window sensor doesn't support 'locked' data")
        return {"status": "success", "window_locked": False}
    except Exception as e:
        logger.error(f"Failed to unlock window (GPIO {WINDOW_LOCK_PIN}): {e}")
        return {"status": "error", "message": str(e)}

# --- Helper Functions ---
def get_storage_status():
    total, used, free = shutil.disk_usage("/")
    return {
        "total_gb": round(total / (2**30), 2),
        "used_gb": round(used / (2**30), 2),
        "free_gb": round(free / (2**30), 2),
        "used_percent": round((used / total) * 100, 2)
    }

def get_network_status():
    interfaces = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    status = {}
    for name, addrs in interfaces.items():
        interface_stats = stats.get(name)
        status[name] = {
            "addresses": [addr.address for addr in addrs if addr.family == psutil.AF_LINK or addr.family == psutil.AF_INET],
            "is_up": interface_stats.isup if interface_stats else False,
            "speed_mbps": interface_stats.speed if interface_stats else 0,
        }
    return status

def get_pi_health():
     # Basic health - extend as needed
     cpu_usage = psutil.cpu_percent(interval=1)
     memory = psutil.virtual_memory()
     return {
        "cpu_usage_percent": cpu_usage,
        "memory_usage_percent": memory.percent,
        "status": "healthy" if cpu_usage < 90 and memory.percent < 90 else "warning"
     }

# --- Flask App Creation ---
def create_pi_api_server(sm, cm):
    """Creates the Flask app instance, injecting dependencies."""
    global sensor_manager, camera_manager
    sensor_manager = sm
    camera_manager = cm

    # Setup hardware (like door lock) before starting server
    setup_door_lock()
    setup_window_lock() # Setup window lock too

    app = Flask(__name__)
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False # Good practice for Flask

    # --- API Routes ---

    @app.route("/api/v1/status", methods=['GET'])
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

    @app.route("/api/v1/sensors/<string:sensor_type>", methods=['GET'])
    @require_api_key
    def get_sensor_data(sensor_type):
        """Return data for a specific sensor type."""
        if not sensor_manager:
            raise InternalServerError("SensorManager not initialized")
        try:
            status_data = sensor_manager.get_sensor_status()
            if sensor_type in status_data:
                return jsonify(status_data[sensor_type])
            else:
                # Check common variations like 'door_lock' if applicable
                if sensor_type == 'door' and 'door_lock' in status_data:
                     return jsonify(status_data['door_lock']) # Example alias
                raise NotFound(f"Sensor type '{sensor_type}' not found or status unavailable.")
        except Exception as e:
            logger.error(f"Error getting sensor data for {sensor_type}: {e}", exc_info=True)
            raise InternalServerError(f"Failed to get sensor data: {e}")

    @app.route("/api/v1/camera/status", methods=['GET'])
    @require_api_key
    def get_camera_pi_status():
        """Return camera status."""
        if not camera_manager:
            raise InternalServerError("CameraManager not initialized")
        try:
            status = camera_manager.get_status() # Assuming this method exists
            return jsonify(status)
        except Exception as e:
            logger.error(f"Error getting camera status: {e}", exc_info=True)
            raise InternalServerError(f"Failed to get camera status: {e}")

    @app.route("/api/v1/rfid/status", methods=['GET'])
    @require_api_key
    def get_rfid_pi_status():
        """Return RFID reader status."""
        if not sensor_manager:
            raise InternalServerError("SensorManager not initialized")
        try:
            # Assuming RFID status is part of the main sensor status
            status_data = sensor_manager.get_sensor_status()
            if 'rfid' in status_data:
                 return jsonify(status_data['rfid'])
            else:
                 raise NotFound("RFID status not found in SensorManager.")
        except Exception as e:
            logger.error(f"Error getting RFID status: {e}", exc_info=True)
            raise InternalServerError(f"Failed to get RFID status: {e}")

    @app.route("/api/v1/health", methods=['GET'])
    @require_api_key
    def get_health_status():
        """Return system health metrics."""
        try:
            health = get_pi_health()
            return jsonify(health)
        except Exception as e:
            logger.error(f"Error getting health status: {e}", exc_info=True)
            raise InternalServerError(f"Failed to get health status: {e}")

    @app.route("/api/v1/storage", methods=['GET'])
    @require_api_key
    def get_storage_pi_status():
        """Return storage status."""
        try:
            storage = get_storage_status()
            return jsonify(storage)
        except Exception as e:
            logger.error(f"Error getting storage status: {e}", exc_info=True)
            raise InternalServerError(f"Failed to get storage status: {e}")

    @app.route("/api/v1/network", methods=['GET'])
    @require_api_key
    def get_network_pi_status():
        """Return network status."""
        try:
            network = get_network_status()
            return jsonify(network)
        except Exception as e:
            logger.error(f"Error getting network status: {e}", exc_info=True)
            raise InternalServerError(f"Failed to get network status: {e}")

    @app.route("/api/v1/config", methods=['POST'])
    @require_api_key
    def update_pi_config():
        """Update Pi configuration (placeholder)."""
        # NOTE: Implementing dynamic config updates safely is complex.
        # This is a placeholder. Requires careful implementation to parse,
        # validate, apply config, and potentially restart services.
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        new_config = request.get_json()
        logger.warning(f"Received config update request (NOT IMPLEMENTED): {new_config}")
        # Example: update specific env var or config file, then maybe restart
        return jsonify({"status": "warning", "message": "Configuration update not fully implemented"})

    @app.route("/api/v1/logs", methods=['GET'])
    @require_api_key
    def get_pi_logs():
        """Retrieve Pi system logs (e.g., last N lines of firmware log)."""
        limit = request.args.get('limit', default=100, type=int)
        log_file_path = os.getenv('RASPBERRYPI_LOG_FILE', os.path.join(os.getcwd(), 'logs/raspberrypi.log'))
        try:
            if not os.path.exists(log_file_path):
                 raise NotFound(f"Log file not found: {log_file_path}")
            # Use tail command for efficiency
            process = subprocess.run(['tail', f'-n{limit}', log_file_path], capture_output=True, text=True, check=True)
            logs = process.stdout.strip().split('\\n')
            return jsonify({"logs": logs})
        except FileNotFoundError:
             raise NotFound(f"Log file not found: {log_file_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error reading log file with tail: {e}")
            raise InternalServerError(f"Failed to read logs: {e}")
        except Exception as e:
            logger.error(f"Error getting logs: {e}", exc_info=True)
            raise InternalServerError(f"Failed to get logs: {e}")

    @app.route("/api/v1/firmware/version", methods=['GET'])
    @require_api_key
    def get_firmware_version():
        """Return firmware version (placeholder)."""
        # Version could be stored in a file or env var
        version = os.getenv("FIRMWARE_VERSION", "1.0.0-dev") # Example placeholder
        return jsonify({"version": version})

    # Add other firmware check/update endpoints if needed (placeholders)
    @app.route("/api/v1/firmware/check-updates", methods=['GET'])
    @require_api_key
    def check_firmware_updates():
        logger.info("Firmware update check requested (NOT IMPLEMENTED)")
        return jsonify({"status": "no-updates", "message": "Update check not implemented"})

    @app.route("/api/v1/control", methods=['POST'])
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
            elif action == "lock_window": # Add window lock action
                result = lock_window()
            elif action == "unlock_window": # Add window unlock action
                result = unlock_window()
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
            elif action == "clear_logs":
                 log_file_path = os.getenv('RASPBERRYPI_LOG_FILE', os.path.join(os.getcwd(), 'logs/raspberrypi.log'))
                 try:
                     # Clear the log file safely
                     with open(log_file_path, 'w') as f:
                         f.truncate(0)
                     logger.info(f"Log file cleared: {log_file_path}")
                     result = {"status": "success", "message": "Logs cleared successfully"}
                 except Exception as e:
                     logger.error(f"Failed to clear log file {log_file_path}: {e}")
                     raise InternalServerError(f"Failed to clear logs: {e}")
            elif action == "update_firmware":
                 logger.warning("Firmware update via API requested (NOT IMPLEMENTED)")
                 # Trigger update script here if implemented
                 result = {"status": "warning", "message": "Firmware update not implemented"}
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
        def get_sensor_status(self): return {
             "dummy_sensor": {"is_active": True},
             "window": {"is_active": True, "data": {"locked": False}} # Mock window status
         }
        def get_status(self): return {"dummy_cam": {"is_active": True}}
        def capture_image(self): return "/path/dummy.jpg", "http://dummy/dummy.jpg"
        def record_video(self, duration): return f"/path/dummy_{duration}s.mp4", f"http://dummy/dummy_{duration}s.mp4"
        def _update_sensor_status(self, *args, **kwargs): pass # No-op

    test_app = create_pi_api_server(DummyManager(), DummyManager())
    # Run on 0.0.0.0 to be accessible externally, port 5000 as expected by server config
    # Use waitress or gunicorn in production instead of Flask dev server
    from waitress import serve
    print("Starting Waitress server for testing...")
    serve(test_app, host='0.0.0.0', port=5000)
    # test_app.run(host='0.0.0.0', port=5000, debug=True) # Debug=True only for testing
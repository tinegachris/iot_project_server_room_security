"""
main.py

This module serves as the main entry point for the server room monitoring system.
It coordinates all sensor modules, camera operations, and notifications to provide
comprehensive server room security monitoring.

Dependencies:
    - sensors.py: For sensor management and monitoring
    - camera.py: For video surveillance
    - notifications.py: For alert handling
    - python-dotenv: For environment variable management
"""

# Force GPIOZero to use RPi.GPIO factory
import os # Re-import where it was originally
os.environ['GPIOZERO_PIN_FACTORY'] = 'rpigpio'

import time
import logging
import signal
import sys
import json
import threading
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, Any, Optional, ClassVar, Tuple, Callable
from dotenv import load_dotenv
from werkzeug.serving import run_simple
import werkzeug.serving # Need this for shutdown

from .sensors import SensorManager
from .camera import CameraManager, CameraConfig
from .notifications import NotificationManager, create_intrusion_alert, create_rfid_alert
from .api_server import create_pi_api_server

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Use environment variable for log file path with a default
        logging.FileHandler(os.getenv('RASPBERRYPI_LOG_FILE', os.path.join(os.getcwd(), 'logs/raspberrypi.log'))),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemConfig:
    """Configuration for the monitoring system."""
    poll_interval: int = int(os.getenv('POLL_INTERVAL', '5'))
    video_duration: int = int(os.getenv('VIDEO_DURATION', '10'))
    health_check_interval: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '300'))  # 5 minutes
    max_retries: int = int(os.getenv('MAX_RETRIES', '3'))
    storage_threshold_gb: int = int(os.getenv('STORAGE_THRESHOLD_GB', '10'))
    camera_config: Optional[CameraConfig] = None

    @classmethod
    def from_env(cls) -> 'SystemConfig':
        """Create SystemConfig from environment variables."""
        resolution_str = os.getenv('CAMERA_RESOLUTION', '1920x1080').split('x')
        resolution: Tuple[int, int] = (int(resolution_str[0]), int(resolution_str[1]))

        # Get the project base directory
        PROJECT_DIR = os.getenv('PROJECT_DIR', '/home/admin/iot_project_server_room_security')

        # Update the output and image directories to use the project base directory
        DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_DIR, 'videos')
        DEFAULT_IMAGE_DIR = os.path.join(PROJECT_DIR, 'images')

        camera_config = CameraConfig(
            resolution=resolution,
            framerate=int(os.getenv('VIDEO_FPS', '30')),
            rotation=int(os.getenv('CAMERA_ROTATION', '0')),
            brightness=int(os.getenv('CAMERA_BRIGHTNESS', '50')),
            output_dir=os.getenv('VIDEO_OUTPUT_DIR', DEFAULT_OUTPUT_DIR),
            image_dir=os.getenv('IMAGE_OUTPUT_DIR', DEFAULT_IMAGE_DIR)
        )
        return cls(camera_config=camera_config)

class ServerRoomMonitor:
    """Main class for server room monitoring system."""

    def __init__(self) -> None:
        """Initialize the monitoring system."""
        # Load configuration directly from environment variables
        self.config = SystemConfig.from_env()
        logger.info("Configuration loaded from environment variables.")

        self.sensor_manager: Optional[SensorManager] = None
        self.camera_manager: Optional[CameraManager] = None
        self.notification_manager: Optional[NotificationManager] = None
        self.running = True
        self.last_health_check = datetime.now()
        self.setup_signal_handlers()
        self.api_thread: Optional[threading.Thread] = None
        self.api_server = None
        self._api_server_shutdown_trigger: Optional[Callable[[], None]] = None # To trigger shutdown

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle system shutdown signals."""
        logger.info("Shutdown signal received. Cleaning up...")
        self.running = False

        # Trigger API server shutdown first
        if self._api_server_shutdown_trigger:
            logger.info("Attempting to trigger API server shutdown...")
            try:
                 # This relies on run_simple supporting shutdown, might need adjustment
                 # Alternatively, use a different server like waitress with explicit shutdown
                 self._api_server_shutdown_trigger()
            except Exception as e:
                 logger.error(f"Error triggering API server shutdown: {e}")

        # Now cleanup other components
        self.cleanup()

        # Wait for API thread to finish
        if self.api_thread and self.api_thread.is_alive():
            logger.info("Waiting for API server thread to join...")
            self.api_thread.join(timeout=10.0) # Wait up to 10 seconds
            if self.api_thread.is_alive():
                 logger.warning("API server thread did not join cleanly.")

        logger.info("Firmware shutdown complete.")
        sys.exit(0) # Ensure clean exit

    def perform_health_check(self) -> None:
        """Perform system health check and send status report."""
        try:
            current_time = datetime.now()
            if (current_time - self.last_health_check).total_seconds() >= self.config.health_check_interval:
                logger.info("Performing system health check...")

                # Get sensor status
                if self.sensor_manager:
                    sensor_status = self.sensor_manager.get_sensor_status()
                else:
                    sensor_status = {"error": "Sensor manager not initialized"}

                # Check storage space
                storage_status = self.check_storage_space()

                # Create health report
                health_report = {
                    'timestamp': current_time.isoformat(),
                    'sensor_status': sensor_status,
                    'storage_status': storage_status,
                    'system_uptime': self.get_system_uptime()
                }

                # Send health report
                if self.notification_manager:
                    alert = create_intrusion_alert(
                        event_type="health_check",
                        message="System Health Check Report",
                        sensor_data=health_report
                    )
                    self.notification_manager.send_alert(alert, channels=['email'])

                self.last_health_check = current_time
                logger.info("Health check completed successfully")
        except Exception as e:
            logger.error("Error during health check: %s", e)

    def get_system_uptime(self) -> str:
        """Get system uptime."""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            return str(timedelta(seconds=int(uptime_seconds)))
        except Exception as e:
            logger.error("Error getting system uptime: %s", e)
            return "unknown"

    def check_storage_space(self) -> Dict[str, Any]:
        """Check available storage space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            return {
                'total_gb': total // (2**30),
                'used_gb': used // (2**30),
                'free_gb': free // (2**30),
                'low_space': free // (2**30) < self.config.storage_threshold_gb
            }
        except Exception as e:
            logger.error("Error checking storage space: %s", e)
            return {'error': str(e)}

    def cleanup(self) -> None:
        """Clean up system resources."""
        try:
            if self.sensor_manager:
                logger.info("Cleaning up SensorManager...")
                self.sensor_manager.cleanup()
                logger.info("SensorManager cleanup finished.")
            else:
                logger.info("SensorManager was not initialized, skipping cleanup.")

            # Camera manager cleanup (if needed)
            if self.camera_manager:
                logger.info("Cleaning up CameraManager...")
                # Assuming CameraManager has a cleanup method
                try:
                    self.camera_manager.cleanup()
                    logger.info("CameraManager cleanup finished.")
                except AttributeError:
                    logger.warning("CameraManager does not have a cleanup method.")
                except Exception as e:
                    logger.error(f"Error during CameraManager cleanup: {e}")
            else:
                 logger.info("CameraManager was not initialized, skipping cleanup.")

            # Note: GPIO cleanup for the door lock is handled by atexit in api_server.py
            logger.info("System resource cleanup process completed.")

        except Exception as e:
            logger.error("Error during main cleanup routine: %s", e, exc_info=True)

    def start_api_server(self) -> None:
        if not self.sensor_manager or not self.camera_manager:
            logger.error("Cannot start API server: Managers not initialized.")
            return

        try:
            # Create the Flask app instance, passing the managers
            self.api_server = create_pi_api_server(self.sensor_manager, self.camera_manager)

            # Run Flask server in a separate thread
            # Use run_simple from werkzeug for simplicity here
            # For production, consider waitress or gunicorn
            host = "0.0.0.0" # Listen on all interfaces
            port = int(os.getenv("RASPBERRY_PI_API_PORT", "5000")) # Get port from env or default 5000

            # Prepare shutdown mechanism for run_simple (requires newer werkzeug)
            shutdown_event = threading.Event()
            self._api_server_shutdown_trigger = shutdown_event.set

            def run_server():
                # Create a simple server environment
                # This is a basic way; production might use WSGI server directly
                try:
                    # Check if shutdown_trigger attribute exists (newer werkzeug versions)
                    if hasattr(werkzeug.serving, 'make_server'):
                        srv = werkzeug.serving.make_server(host, port, self.api_server, threaded=True)
                        self._api_server_shutdown_trigger = srv.shutdown # More reliable shutdown
                        logger.info(f"Flask API server (make_server) starting on http://{host}:{port}")
                        srv.serve_forever()
                    else:
                        # Fallback for older werkzeug, shutdown might be less reliable
                        logger.info(f"Flask API server (run_simple) starting on http://{host}:{port}")
                        run_simple(host, port, self.api_server, use_reloader=False, use_debugger=False, threaded=True)
                        # run_simple doesn't have a direct shutdown method easily exposed here
                        # Using the event is a workaround signal
                        shutdown_event.wait() # Keep thread alive until shutdown is triggered
                        logger.info("run_simple server loop exiting due to shutdown trigger.")
                except Exception as e:
                    logger.error(f"API server thread encountered an error: {e}", exc_info=True)
                finally:
                    logger.info("API server thread finished.")

            self.api_thread = threading.Thread(
                target=run_server,
                daemon=False # Make it non-daemon so we can join it
            )
            self.api_thread.start()
            logger.info(f"Flask API server started in background thread.")

        except Exception as e:
            logger.error(f"Failed to start API server thread: {e}", exc_info=True)

    def run(self) -> None:
        """Main system loop."""
        logger.info("Starting IoT-based Server Room Monitoring System...")

        try:
            # Initialize system components
            logger.info("Initializing SensorManager...")
            self.sensor_manager = SensorManager(camera_config=self.config.camera_config, verbose=True)
            logger.info("Initializing CameraManager...")
            self.camera_manager = CameraManager(self.config.camera_config)
            logger.info("Initializing NotificationManager...")
            self.notification_manager = NotificationManager()

            # Start sensor monitoring threads (part of SensorManager init or a separate start method)
            if self.sensor_manager:
                logger.info("Starting SensorManager monitoring threads...")
                self.sensor_manager.start()

            # Start the API server in a background thread
            logger.info("Starting API server thread...")
            self.start_api_server()

            # Main loop - Check health and keep running
            logger.info("Entering main monitoring loop...")
            while self.running:
                # Perform periodic health checks
                self.perform_health_check()

                # Check if sensor manager or API thread died unexpectedly
                if self.sensor_manager and not self.sensor_manager.is_healthy():
                    logger.error("SensorManager reported unhealthy state. Shutting down...")
                    self.handle_shutdown(signal.SIGTERM, None) # Trigger shutdown
                    break # Exit loop

                if self.api_thread and not self.api_thread.is_alive():
                     logger.error("API server thread died unexpectedly. Shutting down...")
                     self.handle_shutdown(signal.SIGTERM, None) # Trigger shutdown
                     break # Exit loop

                # Sleep for a short interval before next check
                # The actual sensor checks are happening in their own threads
                time.sleep(self.config.poll_interval)

            logger.info("Main loop exited.")

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received. Initiating shutdown...")
            self.handle_shutdown(signal.SIGINT, None)
        except Exception as e:
            logger.critical(f"Unhandled exception in main run loop: {e}", exc_info=True)
            self.handle_shutdown(signal.SIGTERM, None) # Attempt graceful shutdown on error
        finally:
            # Final cleanup call just in case shutdown wasn't fully handled
            logger.info("Executing final cleanup in finally block...")
            self.cleanup()
            # Ensure GPIO is cleaned up if atexit didn't run (e.g., forceful kill)
            try:
                from .api_server import gpio_cleanup
                gpio_cleanup()
            except Exception as gpio_e:
                logger.warning(f"Error during final GPIO cleanup attempt: {gpio_e}")
            logger.info("ServerRoomMonitor run method finished.")

def main() -> None:
    """Entry point for the monitoring system."""
    try:
        monitor = ServerRoomMonitor()
        monitor.run()
    except Exception as e:
        logger.critical("Failed to start monitoring system: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()

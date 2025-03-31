#!/home/admin/iot_project_server_room_security/venv/bin/python3
"""
main.py

This module serves as the main entry point for the server room monitoring system.
It coordinates all sensor modules, camera operations, and notifications to provide
comprehensive server room security monitoring.

Dependencies:
    - sensors.py: For sensor management and monitoring
    - camera.py: For video surveillance
    - notifications.py: For alert handling
"""

import time
import logging
import signal
import sys
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional, ClassVar

from sensors import SensorManager
from camera import CameraManager
from notifications import NotificationManager, create_intrusion_alert

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_room_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemConfig:
    """Configuration for the monitoring system."""
    poll_interval: int = 5
    video_duration: int = 10
    health_check_interval: int = 300  # 5 minutes
    max_retries: int = 3
    storage_threshold_gb: int = 10

class ServerRoomMonitor:
    """Main class for server room monitoring system."""

    def __init__(self, config_path: str = 'config.json') -> None:
        """Initialize the monitoring system."""
        self.config = self._load_config(config_path)
        self.sensor_manager: Optional[SensorManager] = None
        self.camera_manager: Optional[CameraManager] = None
        self.notification_manager: Optional[NotificationManager] = None
        self.running = True
        self.last_health_check = datetime.now()
        self.setup_signal_handlers()

    def _load_config(self, config_path: str) -> SystemConfig:
        """Load system configuration from file."""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file) as f:
                    config_data = json.load(f)
                    return SystemConfig(**config_data)
            return SystemConfig()
        except Exception as e:
            logger.error("Error loading config: %s", e)
            return SystemConfig()

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle system shutdown signals."""
        logger.info("Shutdown signal received. Cleaning up...")
        self.running = False
        self.cleanup()

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
                    'storage_status': storage_status
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
                self.sensor_manager.cleanup()
            logger.info("System resources cleaned up successfully")
        except Exception as e:
            logger.error("Error during cleanup: %s", e)

    def run(self) -> None:
        """Main system loop."""
        logger.info("Starting IoT-based Server Room Monitoring System...")

        try:
            # Initialize system components
            self.sensor_manager = SensorManager(verbose=True)
            self.camera_manager = CameraManager()
            self.notification_manager = NotificationManager()

            # Start sensor monitoring
            if self.sensor_manager:
                self.sensor_manager.start()

            retry_count = 0
            while self.running:
                try:
                    # Get sensor status
                    if self.sensor_manager:
                        sensor_status = self.sensor_manager.get_sensor_status()
                    else:
                        sensor_status = {"error": "Sensor manager not initialized"}

                    # Check for storage issues
                    storage_status = self.check_storage_space()
                    if storage_status.get('low_space', False) and self.notification_manager:
                        alert = create_intrusion_alert(
                            event_type="storage_warning",
                            message="Low storage space detected",
                            sensor_data=storage_status
                        )
                        self.notification_manager.send_alert(alert, channels=['email'])

                    # Perform health check
                    self.perform_health_check()

                    time.sleep(self.config.poll_interval)
                    retry_count = 0  # Reset retry count on successful iteration

                except Exception as e:
                    logger.error("Error during monitoring: %s", e)
                    retry_count += 1

                    if retry_count >= self.config.max_retries:
                        logger.critical("Maximum retry attempts reached. Shutting down...")
                        self.running = False
                    else:
                        logger.info("Retrying in %d seconds...", self.config.poll_interval * 2)
                        time.sleep(self.config.poll_interval * 2)

        except Exception as e:
            logger.critical("Fatal error: %s", e)
            self.running = False
        finally:
            self.cleanup()
            logger.info("Server Room Monitoring System stopped.")

def main() -> None:
    """Entry point for the monitoring system."""
    monitor = ServerRoomMonitor()
    monitor.run()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""
Main script for running the IoT-based Server Room Monitoring System.
This script initializes the sensor manager, camera, and notification modules.
It then continuously monitors the server room for intrusion events and unauthorized access.
Upon detecting an event, it records a video clip and sends an alert to the system administrator.
"""

import time
import logging
import signal
import sys
import json
from pathlib import Path
from datetime import datetime

# Import our custom modules
import sensors      # Module for sensor interfacing (e.g., motion/door/RFID sensors)
import camera       # Module for handling camera functions (e.g., video capture)
import notifications  # Module for sending alerts (e.g., via Twilio)

# Configure logging for debugging purposes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_room_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class Config:
    def __init__(self):
        self.config_file = Path('config.json')
        self.load_config()

    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    config = json.load(f)
                    self.poll_interval = config.get('poll_interval', 5)
                    self.video_duration = config.get('video_duration', 10)
                    self.health_check_interval = config.get('health_check_interval', 300)  # 5 minutes
                    self.max_retries = config.get('max_retries', 3)
            else:
                self.create_default_config()
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self.create_default_config()

    def create_default_config(self):
        default_config = {
            'poll_interval': 5,
            'video_duration': 10,
            'health_check_interval': 300,
            'max_retries': 3
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            self.__dict__.update(default_config)
        except Exception as e:
            logging.error(f"Error creating default config: {e}")
            raise

class ServerRoomMonitor:
    def __init__(self):
        self.config = Config()
        self.sensor_manager = None
        self.running = True
        self.last_health_check = datetime.now()
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        logging.info("Shutdown signal received. Cleaning up...")
        self.running = False
        if self.sensor_manager:
            self.sensor_manager.cleanup()
        sys.exit(0)

    def perform_health_check(self):
        """Perform system health check and send status report."""
        try:
            current_time = datetime.now()
            if (current_time - self.last_health_check).total_seconds() >= self.config.health_check_interval:
                logging.info("Performing system health check...")
                
                # Check sensor status
                sensor_status = self.sensor_manager.check_sensor_status()
                
                # Check camera status
                camera_status = camera.check_camera_status()
                
                # Check storage space
                storage_status = self.check_storage_space()
                
                health_report = {
                    'timestamp': current_time.isoformat(),
                    'sensor_status': sensor_status,
                    'camera_status': camera_status,
                    'storage_status': storage_status
                }
                
                # Send health report via notifications
                notifications.send_alert(
                    f"Health Check Report: {json.dumps(health_report, indent=2)}",
                    channels=['email']
                )
                
                self.last_health_check = current_time
                logging.info("Health check completed successfully")
        except Exception as e:
            logging.error(f"Error during health check: {e}")

    def check_storage_space(self):
        """Check available storage space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            return {
                'total_gb': total // (2**30),
                'used_gb': used // (2**30),
                'free_gb': free // (2**30)
            }
        except Exception as e:
            logging.error(f"Error checking storage space: {e}")
            return {'error': str(e)}

    def run(self):
        logging.info("Starting IoT-based Server Room Monitoring System...")
        
        try:
            self.sensor_manager = sensors.SensorManager(verbose=True)
            self.sensor_manager.start()
            
            retry_count = 0
            while self.running:
                try:
                    # Check for traditional intrusion events
                    intrusion_detected = self.sensor_manager.check_intrusion()
                    # Check for unauthorized RFID access
                    rfid_violation = self.sensor_manager.check_rfid()

                    if intrusion_detected or rfid_violation:
                        if intrusion_detected:
                            logging.warning("Intrusion detected!")
                        if rfid_violation:
                            logging.warning("Unauthorized RFID access detected!")

                        logging.info("Activating video capture and sending alert.")

                        # Record video clip upon event detection
                        video_file, cloud_url = camera.record_video(duration=self.config.video_duration)
                        logging.info(f"Video recorded: {video_file}, Cloud URL: {cloud_url}")

                        # Build alert message including the event type
                        event_type = []
                        if intrusion_detected:
                            event_type.append("intrusion")
                        if rfid_violation:
                            event_type.append("unauthorized RFID access")
                        event_str = " and ".join(event_type)

                        alert_message = f"Alert: {event_str} in server room. Video captured at {cloud_url}"
                        notifications.send_alert(alert_message, media_url=cloud_url, channels=["sms", "email", "fcm"])

                        # Reset retry count on successful operation
                        retry_count = 0
                    else:
                        logging.info("No intrusion or unauthorized RFID access detected. Continuing monitoring...")

                    # Perform health check
                    self.perform_health_check()

                    time.sleep(self.config.poll_interval)

                except Exception as e:
                    logging.error(f"An error occurred during monitoring: {e}")
                    retry_count += 1
                    
                    if retry_count >= self.config.max_retries:
                        logging.critical("Maximum retry attempts reached. Shutting down...")
                        self.running = False
                    else:
                        logging.info(f"Retrying in {self.config.poll_interval * 2} seconds...")
                        time.sleep(self.config.poll_interval * 2)

        except Exception as e:
            logging.critical(f"Fatal error: {e}")
            self.running = False
        finally:
            if self.sensor_manager:
                self.sensor_manager.cleanup()
            logging.info("Server Room Monitoring System stopped.")

if __name__ == "__main__":
    monitor = ServerRoomMonitor()
    monitor.run()

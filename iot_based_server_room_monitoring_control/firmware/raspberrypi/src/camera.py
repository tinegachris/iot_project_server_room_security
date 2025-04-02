"""
camera.py

This module handles video surveillance functions using the Raspberry Pi Camera.
It provides functionality for capturing images and recording videos with configurable settings,
and includes cloud storage integration for remote access to captured media.

Dependencies:
    - picamera (install with `pip install picamera`)
    - requests (install with `pip install requests`)
    - python-dotenv (install with `pip install python-dotenv`)
"""

import time
import os
import logging
import requests
from dataclasses import dataclass
from typing import Optional, Tuple
from picamera import PiCamera
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class CameraConfig:
    """Configuration for camera settings."""
    resolution: Tuple[int, int] = (1280, 720)
    framerate: int = 30
    rotation: int = 0
    brightness: int = 50
    output_dir: str = "/home/pi/Videos"
    image_dir: str = "/home/pi/Pictures"

class CameraManager:
    """Manages camera operations and cloud storage integration."""

    def __init__(self, config: Optional[CameraConfig] = None):
        """Initialize the camera manager with optional configuration."""
        self.config = config or CameraConfig()
        self.cloud_url = os.getenv("CLOUD_STORAGE_URL")
        self._setup_directories()
        self._check_camera()

    def _setup_directories(self) -> None:
        """Create output directories if they don't exist."""
        try:
            os.makedirs(self.config.output_dir, exist_ok=True)
            os.makedirs(self.config.image_dir, exist_ok=True)
            logger.info("Output directories created successfully")
        except Exception as e:
            logger.error("Failed to create output directories: %s", e)
            raise

    def _check_camera(self) -> None:
        """Verify camera availability."""
        try:
            with PiCamera() as camera:
                camera.close()
            logger.info("Camera initialized successfully")
        except Exception as e:
            logger.error("Camera initialization failed: %s", e)
            raise

    def _configure_camera(self, camera: PiCamera) -> None:
        """Configure camera with current settings."""
        camera.resolution = self.config.resolution
        camera.framerate = self.config.framerate
        camera.rotation = self.config.rotation
        camera.brightness = self.config.brightness
        logger.debug("Camera configured with: resolution=%s, framerate=%d, rotation=%d, brightness=%d",
                    self.config.resolution, self.config.framerate, self.config.rotation, self.config.brightness)

    def _upload_to_cloud(self, file_path: str) -> Optional[str]:
        """Upload a file to cloud storage."""
        if not self.cloud_url:
            logger.warning("Cloud storage URL not configured")
            return None

        try:
            with open(file_path, 'rb') as file:
                response = requests.post(self.cloud_url, files={'file': file})
                response.raise_for_status()
                cloud_url = response.json().get('url')
                logger.info("File uploaded successfully: %s", cloud_url)
                return cloud_url
        except Exception as e:
            logger.error("Failed to upload file: %s", e)
            return None

    def capture_image(self) -> Tuple[str, Optional[str]]:
        """
        Capture a still image with current camera settings.

        Returns:
            Tuple of (local_file_path, cloud_url)
        """
        timestamp = int(time.time())
        file_path = os.path.join(self.config.image_dir, f"image_{timestamp}.jpg")

        try:
            with PiCamera() as camera:
                self._configure_camera(camera)
                time.sleep(2)  # Warm-up time
                camera.capture(file_path)
                logger.info("Image captured: %s", file_path)

            cloud_url = self._upload_to_cloud(file_path)
            return file_path, cloud_url
        except Exception as e:
            logger.error("Failed to capture image: %s", e)
            raise

    def record_video(self, duration: int = 10) -> Tuple[str, Optional[str]]:
        """
        Record a video with current camera settings.

        Args:
            duration: Recording duration in seconds

        Returns:
            Tuple of (local_file_path, cloud_url)
        """
        timestamp = int(time.time())
        file_path = os.path.join(self.config.output_dir, f"video_{timestamp}.h264")

        try:
            with PiCamera() as camera:
                self._configure_camera(camera)
                time.sleep(2)  # Warm-up time

                camera.start_recording(file_path)
                camera.wait_recording(duration)
                camera.stop_recording()
                logger.info("Video recorded: %s", file_path)

            cloud_url = self._upload_to_cloud(file_path)
            return file_path, cloud_url
        except Exception as e:
            logger.error("Failed to record video: %s", e)
            raise

    def update_config(self, new_config: CameraConfig) -> None:
        """Update camera configuration."""
        self.config = new_config
        self._setup_directories()
        logger.info("Camera configuration updated")

def main() -> None:
    """Test the camera functionality."""
    try:
        camera = CameraManager()

        # Test image capture
        logger.info("Testing image capture...")
        image_path, image_url = camera.capture_image()
        logger.info("Image saved to: %s, Cloud URL: %s", image_path, image_url)

        # Test video recording
        logger.info("Testing video recording...")
        video_path, video_url = camera.record_video(duration=5)
        logger.info("Video saved to: %s, Cloud URL: %s", video_path, video_url)

    except Exception as e:
        logger.error("Test failed: %s", e)

if __name__ == "__main__":
    main()

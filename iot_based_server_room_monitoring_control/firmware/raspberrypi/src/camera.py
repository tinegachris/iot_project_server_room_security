"""
camera.py

This module handles video surveillance functions using the Raspberry Pi Camera.
It provides functionality for capturing images and recording videos with configurable settings,
and includes cloud storage integration for remote access to captured media.

Dependencies:
    - picamera2 (install with `pip install picamera2`) - Only on Raspberry Pi
    - requests (install with `pip install requests`)
    - python-dotenv (install with `pip install python-dotenv`)
    - PIL (install with `pip install pillow`) - For mock implementation
"""

import time
import os
import logging
import requests
import datetime as dt
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import atexit
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check if running on Raspberry Pi
try:
    import platform
    IS_RASPBERRY_PI = platform.machine().startswith(('arm', 'aarch64'))
    # IS_RASPBERRY_PI = False
    if IS_RASPBERRY_PI:
        from picamera2 import Picamera2
        from picamera2.encoders import H264Encoder
        from picamera2.outputs import FileOutput
        from picamera2.controls import Controls
        logger.info("Running on Raspberry Pi with real camera hardware")
    else:
        logger.warning("Not running on Raspberry Pi, using mock implementation")
except ImportError:
    IS_RASPBERRY_PI = False
    logger.warning("Running in mock mode - no Raspberry Pi camera hardware detected")

CWD = os.getcwd()
DEFAULT_OUTPUT_DIR = os.path.join(CWD, 'iot_based_server_room_monitoring_control/media/videos')
DEFAULT_IMAGE_DIR = os.path.join(CWD, 'iot_based_server_room_monitoring_control/media/images')

@dataclass
class CameraConfig:
    """Configuration for camera settings."""
    resolution: Tuple[int, int] = (1280, 720)
    framerate: int = 30
    rotation: int = 0
    brightness: int = 50
    output_dir: str = DEFAULT_OUTPUT_DIR
    image_dir: str = DEFAULT_IMAGE_DIR

class MockCamera:
    """Mock camera implementation for non-Raspberry Pi systems."""
    
    def __init__(self, config: CameraConfig):
        """Initialize the mock camera."""
        self.config = config
        self._setup_directories()
        
    def _setup_directories(self) -> None:
        """Create output directories if they don't exist."""
        try:
            # Create parent directory first
            os.makedirs(os.path.dirname(self.config.output_dir), exist_ok=True)
            os.makedirs(os.path.dirname(self.config.image_dir), exist_ok=True)
            
            # Then create the specific directories
            os.makedirs(self.config.output_dir, exist_ok=True)
            os.makedirs(self.config.image_dir, exist_ok=True)
            logger.info("Output directories created successfully")
        except Exception as e:
            logger.error("Failed to create output directories: %s", e)
            raise
            
    def _create_mock_image(self, file_path: str) -> None:
        """Create a mock image for testing."""
        width, height = self.config.resolution
        image = Image.new('RGB', (width, height), color=(73, 109, 137))
        draw = ImageDraw.Draw(image)
        
        # Add some text to the image
        try:
            font = ImageFont.truetype("Arial", 36)
        except IOError:
            font = ImageFont.load_default()
            
        timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"Mock Image - {timestamp}"
        text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (width//2, 36)
        position = ((width - text_width) // 2, (height - text_height) // 2)
        draw.text(position, text, fill=(255, 255, 255), font=font)
        
        # Save the image
        image.save(file_path)
        logger.info("Mock image created: %s", file_path)
        
    def _create_mock_video(self, file_path: str, duration: int) -> None:
        """Create a mock video file for testing."""
        # Create a simple text file as a placeholder for video
        with open(file_path, 'w') as f:
            f.write(f"Mock video file - Duration: {duration} seconds\n")
            f.write(f"Created at: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Resolution: {self.config.resolution[0]}x{self.config.resolution[1]}\n")
            f.write(f"Framerate: {self.config.framerate}\n")
        logger.info("Mock video file created: %s", file_path)
        
    def capture_file(self, file_path: str, is_video: bool = False, duration: int = 10) -> None:
        """Capture an image or video file."""
        if is_video:
            self._create_mock_video(file_path, duration)
        else:
            self._create_mock_image(file_path)
            
    def close(self) -> None:
        """Clean up resources."""
        pass

class CameraManager:
    """Manages camera operations and cloud storage integration."""

    def __init__(self, config: Optional[CameraConfig] = None):
        """Initialize the camera manager with optional configuration."""
        self.config = config or CameraConfig()
        self.cloud_url = os.getenv("CLOUD_STORAGE_URL")
        self._validate_cloud_config()
        
        if IS_RASPBERRY_PI:
            self.camera = Picamera2()
            self._setup_camera()
        else:
            self.camera = MockCamera(self.config)

        self.is_active = False
        self.last_image_path: Optional[str] = None
        self.last_image_time: Optional[datetime] = None
        self.last_video_path: Optional[str] = None
        self.last_video_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self._initialize_camera()
        atexit.register(self.cleanup)

    def _validate_cloud_config(self) -> None:
        """Validate cloud storage configuration."""
        if not self.cloud_url:
            logger.warning("Cloud storage URL not configured. Media will be stored locally only.")
            return
            
        if not self.cloud_url.startswith(('http://', 'https://')):
            logger.warning("Invalid cloud storage URL format. Must start with http:// or https://")
            self.cloud_url = None
            return
            
        try:
            # Test the URL format
            from urllib.parse import urlparse
            parsed = urlparse(self.cloud_url)
            if not parsed.netloc:
                raise ValueError("Invalid URL format")
            logger.info("Cloud storage URL validated successfully")
        except Exception as e:
            logger.warning("Invalid cloud storage URL: %s. Media will be stored locally only.", str(e))
            self.cloud_url = None

    def _setup_camera(self) -> None:
        """Setup the camera with current configuration."""
        if not IS_RASPBERRY_PI:
            return
            
        try:
            # Configure camera
            camera_config = self.camera.create_preview_configuration(
                main={"size": self.config.resolution},
                controls={
                    "FrameDurationLimits": (int(1000000/self.config.framerate), int(1000000/self.config.framerate)),
                    "Brightness": self.config.brightness,
                    "Rotation": self.config.rotation
                }
            )
            self.camera.configure(camera_config)
            self.camera.start()
            logger.info("Camera initialized successfully")
        except Exception as e:
            logger.error("Camera initialization failed: %s", e)
            raise

    def _upload_to_cloud(self, file_path: str) -> Optional[str]:
        """Upload a file to cloud storage."""
        if not self.cloud_url:
            logger.debug("Cloud storage URL not configured, skipping upload")
            return None

        try:
            if not os.path.exists(file_path):
                logger.error("File not found for upload: %s", file_path)
                return None
                
            with open(file_path, 'rb') as file:
                response = requests.post(self.cloud_url, files={'file': file})
                response.raise_for_status()
                cloud_url = response.json().get('url')
                if not cloud_url:
                    logger.error("No URL returned from cloud storage")
                    return None
                logger.info("File uploaded successfully: %s", cloud_url)
                return cloud_url
        except requests.exceptions.RequestException as e:
            logger.error("Failed to upload file: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during file upload: %s", str(e))
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
            if IS_RASPBERRY_PI:
                self.camera.capture_file(file_path)
            else:
                self.camera.capture_file(file_path, is_video=False)
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
            if IS_RASPBERRY_PI:
                # Configure video recording
                encoder = H264Encoder()
                output = FileOutput(file_path)
                
                # Start recording
                self.camera.start_recording(encoder, output)
                time.sleep(duration)
                self.camera.stop_recording()
            else:
                self.camera.capture_file(file_path, is_video=True, duration=duration)
            logger.info("Video recorded: %s", file_path)

            cloud_url = self._upload_to_cloud(file_path)
            return file_path, cloud_url
        except Exception as e:
            logger.error("Failed to record video: %s", e)
            raise

    def update_config(self, new_config: CameraConfig) -> None:
        """Update camera configuration."""
        self.config = new_config
        if IS_RASPBERRY_PI:
            self._setup_camera()
        logger.info("Camera configuration updated")

    def cleanup(self) -> None:
        """Clean up camera resources."""
        try:
            if IS_RASPBERRY_PI:
                self.camera.stop()
                self.camera.close()
            else:
                self.camera.close()
            logger.info("Camera resources cleaned up")
        except Exception as e:
            logger.error("Error during camera cleanup: %s", e)

    def _initialize_camera(self) -> None:
        """Initialize the camera with configured settings."""
        logger.info("Camera manager started.")

    def get_status(self) -> Dict[str, Any]:
        """Return the current status of the camera manager."""
        return {
            "is_active": self.is_active,
            "resolution": f"{self.config.resolution[0]}x{self.config.resolution[1]}" if self.config else "N/A",
            "framerate": self.config.framerate if self.config else "N/A",
            "rotation": self.config.rotation if self.config else "N/A",
            "brightness": self.config.brightness if self.config else "N/A",
            "last_image_time": self.last_image_time.isoformat() if self.last_image_time else None,
            "last_video_time": self.last_video_time.isoformat() if self.last_video_time else None,
            "last_image_path": self.last_image_path,
            "last_video_path": self.last_video_path,
            "error": self.error_message
        }

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
    finally:
        camera.cleanup()

if __name__ == "__main__":
    main()

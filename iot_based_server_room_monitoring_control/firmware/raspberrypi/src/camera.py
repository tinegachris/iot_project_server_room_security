#!/home/admin/iot_project_server_room_security/venv/bin/python3
"""
camera.py

This module handles video surveillance functions using the Raspberry Pi Camera.
It uses the picamera library to record video clips when triggered—typically upon an intrusion event.
The recording function allows for customization of camera settings to suit surveillance needs.

Functions:
    record_video(duration, resolution, framerate, rotation, brightness):
        Records a video for the specified duration with optional camera settings.
"""

import time
import os
import logging
import requests
from picamera import PiCamera

# Configure logging for debugging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Directory to store recorded videos; adjust this path as needed.
VIDEO_OUTPUT_DIR = "/home/pi/Videos"
IMAGE_OUTPUT_DIR = "/home/pi/Pictures"

# Ensure the output directory exists
try:
    os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
except Exception as e:
    logging.error("Failed to create output directories: %s", e)
    raise

CLOUD_STORAGE_URL = "https://your-cloud-storage-service.com/upload"

def upload_to_cloud(file_path):
    """
    Uploads a file to cloud storage.

    Args:
        file_path (str): The path to the file to upload.

    Returns:
        str: The URL of the uploaded file.
    """
    try:
        with open(file_path, 'rb') as file:
            response = requests.post(CLOUD_STORAGE_URL, files={'file': file})
            response.raise_for_status()
            logging.info("File uploaded to cloud storage successfully.")
            return response.json().get('url')
    except requests.RequestException as e:
        logging.error("Failed to upload file to cloud storage: %s", e)
        raise
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        raise

def capture_image(resolution=(1280, 720), rotation=0, brightness=50):
    """
    Captures a still image using the Raspberry Pi Camera.
    Allows customization of camera settings to optimize image capture.

    Args:
        resolution (tuple, optional): Resolution (width, height) in pixels.
                                      Defaults to (1280, 720).
        rotation (int, optional): Rotation angle in degrees (0, 90, 180, 270).
                                  Defaults to 0.
        brightness (int, optional): Brightness setting (0 to 100).
                                    Defaults to 50.

    Returns:
        str: The full file path to the captured image.
    """
    camera = PiCamera()
    try:
        camera.resolution = resolution
        camera.rotation = rotation
        camera.brightness = brightness

        logging.info("Camera settings: resolution=%s, rotation=%d, brightness=%d",
                     resolution, rotation, brightness)

        time.sleep(2)

        timestamp = int(time.time())
        file_path = os.path.join(IMAGE_OUTPUT_DIR, f"image_{timestamp}.jpg")

        logging.info(f"Capturing image: {file_path}")
        camera.capture(file_path)

        return file_path

    except Exception as e:
        logging.error("Error during image capture: %s", e)
        raise

    finally:
        camera.close()

def record_video(duration=10, resolution=(1280, 720), framerate=30, rotation=0, brightness=50):
    """
    Records a video using the Raspberry Pi Camera for a specified duration.
    Allows customization of camera settings to optimize surveillance capture.

    Args:
        duration (int, optional): Duration of the video recording in seconds.
                                  Defaults to 10 seconds.
        resolution (tuple, optional): Resolution (width, height) in pixels.
                                      Defaults to (1280, 720).
        framerate (int, optional): Frame rate for video recording.
                                   Defaults to 30.
        rotation (int, optional): Rotation angle in degrees (0, 90, 180, 270).
                                  Defaults to 0.
        brightness (int, optional): Brightness setting (0 to 100).
                                    Defaults to 50.

    Returns:
        str: The full file path to the recorded video.
    """
    camera = PiCamera()
    try:
        camera.resolution = resolution
        camera.framerate = framerate
        camera.rotation = rotation
        camera.brightness = brightness

        logging.info("Camera settings: resolution=%s, framerate=%d, rotation=%d, brightness=%d",
                     resolution, framerate, rotation, brightness)

        time.sleep(2)

        timestamp = int(time.time())
        file_path = os.path.join(VIDEO_OUTPUT_DIR, f"video_{timestamp}.h264")

        logging.info(f"Starting video recording: {file_path}")
        camera.start_recording(file_path)
        camera.wait_recording(duration)
        camera.stop_recording()
        logging.info("Video recording stopped.")

        cloud_url = upload_to_cloud(file_path)
        return file_path, cloud_url

    except Exception as e:
        logging.error("Error during video recording: %s", e)
        raise

    finally:
        camera.close()

if __name__ == "__main__":
    try:
        test_duration = 5
        logging.info(f"Recording video for {test_duration} seconds with default settings...")
        video_file, cloud_url = record_video(duration=test_duration)
        logging.info(f"Test video saved to: {video_file}, Cloud URL: {cloud_url}")
        print(f"Test video saved to: {video_file}, Cloud URL: {cloud_url}")
    except Exception as err:
        logging.error("An error occurred in testing: %s", err)

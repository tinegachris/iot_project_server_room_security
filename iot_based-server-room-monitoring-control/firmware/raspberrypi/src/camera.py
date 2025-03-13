#!/usr/bin/env python3
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
from picamera import PiCamera

# Configure logging for debugging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Directory to store recorded videos; adjust this path as needed.
VIDEO_OUTPUT_DIR = "/home/pi/Videos"

# Ensure the output directory exists
if not os.path.exists(VIDEO_OUTPUT_DIR):
    os.makedirs(VIDEO_OUTPUT_DIR)

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
    # Create a camera instance
    camera = PiCamera()
    try:
        # Set camera settings for intrusion events
        camera.resolution = resolution
        camera.framerate = framerate
        camera.rotation = rotation
        camera.brightness = brightness

        logging.info("Camera settings: resolution=%s, framerate=%d, rotation=%d, brightness=%d",
                     resolution, framerate, rotation, brightness)

        # Allow the camera to warm up
        time.sleep(2)

        # Create a unique filename based on the current timestamp
        timestamp = int(time.time())
        file_path = os.path.join(VIDEO_OUTPUT_DIR, f"video_{timestamp}.h264")

        logging.info(f"Starting video recording: {file_path}")
        camera.start_recording(file_path)
        camera.wait_recording(duration)
        camera.stop_recording()
        logging.info("Video recording stopped.")

        return file_path

    except Exception as e:
        logging.error("Error during video recording: %s", e)
        raise

    finally:
        camera.close()

if __name__ == "__main__":
    # Test the record_video function when this module is run standalone.
    try:
        test_duration = 5  # Record for 5 seconds for testing purposes.
        logging.info(f"Recording video for {test_duration} seconds with default settings...")
        video_file = record_video(duration=test_duration)
        logging.info(f"Test video saved to: {video_file}")
        print(f"Test video saved to: {video_file}")
    except Exception as err:
        logging.error("An error occurred in testing: %s", err)

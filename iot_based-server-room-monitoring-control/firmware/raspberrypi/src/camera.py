#!/usr/bin/env python3
"""
camera.py

This module handles video surveillance functions using the Raspberry Pi Camera.
It uses the picamera library to record video clips when triggered.

Functions:
    record_video(duration): Records a video for the specified duration in seconds.
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

def record_video(duration=10):
    """
    Records a video using the Raspberry Pi Camera for a specified duration.

    Args:
        duration (int, optional): Duration of the video recording in seconds.
                                  Defaults to 10 seconds.

    Returns:
        str: The full file path to the recorded video.
    """
    # Create a camera instance
    camera = PiCamera()
    try:
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
        logging.info(f"Recording video for {test_duration} seconds...")
        video_file = record_video(duration=test_duration)
        logging.info(f"Test video saved to: {video_file}")
        print(f"Test video saved to: {video_file}")
    except Exception as err:
        logging.error("An error occurred in testing: %s", err)

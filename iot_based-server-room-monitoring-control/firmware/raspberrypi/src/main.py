#!/usr/bin/env python3
import time
import logging

# Import our custom modules
import sensors      # Module for sensor interfacing (e.g., motion/door sensors)
import camera       # Module for handling camera functions (e.g., video capture)
import notifications  # Module for sending alerts (e.g., via Twilio)

# Configure logging for debugging purposes
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration parameters (can be moved to a config file later)
POLL_INTERVAL = 5         # seconds between sensor checks
VIDEO_DURATION = 10       # seconds of video to record upon intrusion

def main():
    logging.info("Starting IoT-based Server Room Monitoring System...")

    while True:
        try:
            # Check sensors for an intrusion event
            intruder_detected = sensors.check_intrusion()  # Expected to return True/False

            if intruder_detected:
                logging.warning("Intrusion detected! Activating video capture and sending alert.")

                # Record video clip upon intrusion detection
                video_file = camera.record_video(duration=VIDEO_DURATION)
                logging.info(f"Video recorded: {video_file}")

                # Send notification with video details or a link to the video file
                alert_message = f"Alert: Intruder detected in server room. Video captured at {video_file}"
                notifications.send_alert(alert_message)

                # Optional: delay longer after an intrusion event to avoid redundant alerts
                time.sleep(POLL_INTERVAL * 2)
            else:
                logging.info("No intrusion detected. Continuing monitoring...")

            time.sleep(POLL_INTERVAL)

        except Exception as e:
            logging.error("An error occurred: %s", e)
            # Optionally perform cleanup or restart operations here.
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()

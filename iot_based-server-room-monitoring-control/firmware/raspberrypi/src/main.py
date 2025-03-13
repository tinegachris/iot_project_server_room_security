#!/usr/bin/env python3
import time
import logging

# Import our custom modules
import sensors      # Module for sensor interfacing (e.g., motion/door/RFID sensors)
import camera       # Module for handling camera functions (e.g., video capture)
import notifications  # Module for sending alerts (e.g., via Twilio)

# Configure logging for debugging purposes
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration parameters (can be moved to a config file later)
POLL_INTERVAL = 5         # seconds between sensor checks
VIDEO_DURATION = 10       # seconds of video to record upon event

def main():
    logging.info("Starting IoT-based Server Room Monitoring System...")

    while True:
        try:
            # Check for traditional intrusion events (motion, door/window sensors)
            intrusion_detected = sensors.check_intrusion()  # Expected to return True/False
            # Check for unauthorized RFID access (access control violation)
            rfid_violation = sensors.check_rfid()           # Expected to return True if an unauthorized RFID scan is detected

            if intrusion_detected or rfid_violation:
                if intrusion_detected:
                    logging.warning("Intrusion detected! ")
                if rfid_violation:
                    logging.warning("Unauthorized RFID access detected! ")

                logging.info("Activating video capture and sending alert.")

                # Record video clip upon event detection
                video_file = camera.record_video(duration=VIDEO_DURATION)
                logging.info(f"Video recorded: {video_file}")

                # Build alert message including the event type
                event_type = []
                if intrusion_detected:
                    event_type.append("intrusion")
                if rfid_violation:
                    event_type.append("unauthorized RFID access")
                event_str = " and ".join(event_type)

                alert_message = f"Alert: {event_str} in server room. Video captured at {video_file}"
                notifications.send_alert(alert_message)

                # Optional: delay longer after an event to avoid redundant alerts
                time.sleep(POLL_INTERVAL * 2)
            else:
                logging.info("No intrusion or unauthorized RFID access detected. Continuing monitoring...")

            time.sleep(POLL_INTERVAL)

        except Exception as e:
            logging.error("An error occurred: %s", e)
            # Optionally perform cleanup or restart operations here.
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()

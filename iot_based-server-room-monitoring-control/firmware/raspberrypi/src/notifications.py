#!/usr/bin/env python3
"""
notifications.py

This module is responsible for sending alert notifications (e.g., SMS/MMS)
via the Twilio API. It defines the send_alert() function which takes a message,
and optionally a media URL (for sending MMS with an attached video/image).

Dependencies:
  - twilio (install via: pip install twilio)

Configuration:
  - Update the TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, and TWILIO_TO_NUMBER
    constants with your Twilio credentials and phone numbers.
"""

import logging
from twilio.rest import Client

# Configure logging for debugging and operational visibility
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Twilio Credentials ---
# Replace these placeholders with your actual Twilio credentials.
TWILIO_ACCOUNT_SID = "your_account_sid_here"
TWILIO_AUTH_TOKEN  = "your_auth_token_here"
TWILIO_FROM_NUMBER = "+1234567890"  # Your Twilio phone number
TWILIO_TO_NUMBER   = "+0987654321"  # Recipient phone number (admin)

def send_alert(message, media_url=None):
    """
    Sends an alert via SMS (or MMS if media_url is provided) using the Twilio API.

    Args:
        message (str): The text message to send.
        media_url (str, optional): URL to a media file (image or video) for MMS. Defaults to None.

    Returns:
        str: The SID of the sent message.

    Raises:
        Exception: If the API call fails.
    """
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # Build the parameters for sending the message.
        msg_params = {
            "body": message,
            "from_": TWILIO_FROM_NUMBER,
            "to": TWILIO_TO_NUMBER
        }
        if media_url:
            msg_params["media_url"] = [media_url]

        sent_msg = client.messages.create(**msg_params)
        logging.info("Alert sent successfully. Message SID: %s", sent_msg.sid)
        return sent_msg.sid

    except Exception as e:
        logging.error("Failed to send alert: %s", e)
        raise

if __name__ == "__main__":
    # Test sending an alert message when running this module standalone.
    test_message = "Test alert from IoT-based Server Room Monitoring System."
    try:
        sid = send_alert(test_message)
        print(f"Test alert sent successfully. Message SID: {sid}")
    except Exception as err:
        print(f"Error sending test alert: {err}")

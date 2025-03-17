#!/home/admin/iot_project_server_room_security/venv/bin/python3
"""
notifications.py

This module is responsible for sending alert notifications via multiple channels.
It currently supports:
    - SMS/MMS alerts via the Twilio API
    - Email alerts via SMTP
    - Push notifications via Firebase Cloud Messaging (FCM)

The main function, send_alert(), accepts detailed data (e.g., timestamp, video file URL)
and sends the alert using the specified channels.

Dependencies:
    - twilio (install via: pip install twilio)
    - requests (install via: pip install requests)
    - Standard Python libraries: smtplib, email

Configuration:
    - Set the required environment variables for Twilio, SMTP, and FCM credentials.
"""

import logging
import os
from datetime import datetime
from twilio.rest import Client
import smtplib
from email.message import EmailMessage
import requests

# Configure logging for debugging and operational visibility
logging.basicConfig(level=logging.INFO,
                                        format='%(asctime)s - %(levelname)s - %(message)s')

# --- Twilio Credentials (for SMS/MMS) ---
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
TWILIO_TO_NUMBER = os.getenv("TWILIO_TO_NUMBER")

# --- Email SMTP Configuration ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")

# --- Firebase Cloud Messaging (FCM) Configuration ---
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")
FCM_DEVICE_TOKEN = os.getenv("FCM_DEVICE_TOKEN")

def send_sms_alert(message, media_url=None):
        """
        Sends an alert via SMS/MMS using the Twilio API.

        Args:
                message (str): The text message to send.
                media_url (str, optional): URL to a media file (image or video) for MMS.

        Returns:
                str: The SID of the sent message.
        """
        try:
                if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER]):
                        raise ValueError("Twilio credentials are not fully configured.")

                client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                msg_params = {
                        "body": message,
                        "from_": TWILIO_FROM_NUMBER,
                        "to": TWILIO_TO_NUMBER
                }
                if media_url:
                        msg_params["media_url"] = [media_url]

                sent_msg = client.messages.create(**msg_params)
                logging.info("SMS alert sent successfully. Message SID: %s", sent_msg.sid)
                return sent_msg.sid

        except Exception as e:
                logging.error("Failed to send SMS alert: %s", e)
                raise

def send_email_alert(message, subject="Server Room Alert", media_url=None, event_timestamp=None):
        """
        Sends an alert via email using SMTP.

        Args:
                message (str): The email body message.
                subject (str, optional): The email subject. Defaults to "Server Room Alert".
                media_url (str, optional): URL to media (e.g., video file) to include in the email.
                event_timestamp (datetime, optional): The timestamp of the event. If provided,
                                                                                                it will be included in the email body.

        Returns:
                None
        """
        try:
                if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO]):
                        raise ValueError("SMTP credentials are not fully configured.")

                # Build the email content
                email_body = message
                if event_timestamp:
                        email_body += f"\n\nEvent Time: {event_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                if media_url:
                        email_body += f"\nVideo URL: {media_url}"

                msg = EmailMessage()
                msg.set_content(email_body)
                msg["Subject"] = subject
                msg["From"] = EMAIL_FROM
                msg["To"] = EMAIL_TO

                # Connect to the SMTP server and send the email
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                        server.starttls()  # Secure the connection
                        server.login(SMTP_USERNAME, SMTP_PASSWORD)
                        server.send_message(msg)

                logging.info("Email alert sent successfully to %s.", EMAIL_TO)

        except Exception as e:
                logging.error("Failed to send email alert: %s", e)
                raise

def send_fcm_alert(title, body):
        """
        Sends an alert notification to an Android app via Firebase Cloud Messaging (FCM).

        Args:
                title (str): The title of the notification.
                body (str): The body text of the notification.

        Returns:
                dict: The response from the FCM server.
        """
        try:
                if not all([FCM_SERVER_KEY, FCM_DEVICE_TOKEN]):
                        raise ValueError("FCM credentials are not fully configured.")

                headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'key={FCM_SERVER_KEY}',
                }
                payload = {
                        'to': FCM_DEVICE_TOKEN,
                        'notification': {
                                'title': title,
                                'body': body,
                        }
                }
                response = requests.post('https://fcm.googleapis.com/fcm/send', headers=headers, json=payload)
                response.raise_for_status()
                logging.info("FCM alert sent successfully.")
                return response.json()
        except Exception as e:
                logging.error("Failed to send FCM alert: %s", e)
                raise

def send_alert(message, media_url=None, event_timestamp=None, channels=None):
        """
        Sends an alert via multiple channels. By default, it sends SMS alerts.
        Optionally, email and FCM alerts can be sent if specified in the channels list.

        Args:
                message (str): The alert message to send.
                media_url (str, optional): URL to a media file (video or image) to include in the alert.
                event_timestamp (datetime, optional): The timestamp of the event.
                channels (list, optional): List of channels to send the alert. Options include
                                                                     'sms', 'email', and 'fcm'. Defaults to ['sms'].

        Returns:
                dict: A dictionary containing the status of each channel alert.
                            e.g., {"sms": "SID12345", "email": "sent", "fcm": "sent"}.
        """
        if channels is None:
                channels = ['sms']

        results = {}

        if 'sms' in channels:
                try:
                        sms_sid = send_sms_alert(message, media_url)
                        results["sms"] = sms_sid
                except Exception as e:
                        results["sms"] = f"Error: {e}"

        if 'email' in channels:
                try:
                        # Use current time if no timestamp provided
                        ts = event_timestamp if event_timestamp else datetime.now()
                        send_email_alert(message, media_url=media_url, event_timestamp=ts)
                        results["email"] = "sent"
                except Exception as e:
                        results["email"] = f"Error: {e}"

        if 'fcm' in channels:
                try:
                        title = "Server Room Alert"
                        body = message
                        send_fcm_alert(title, body)
                        results["fcm"] = "sent"
                except Exception as e:
                        results["fcm"] = f"Error: {e}"

        return results

if __name__ == "__main__":
        # Test sending an alert via SMS, Email, and FCM when running this module standalone.
        test_message = "Test alert from IoT-based Server Room Monitoring System."
        test_media_url = "http://example.com/video_sample.h264"
        test_timestamp = datetime.now()

        try:
                result = send_alert(test_message, media_url=test_media_url, event_timestamp=test_timestamp, channels=["sms", "email", "fcm"])
                logging.info("Alert send results: %s", result)
        except Exception as err:
                logging.error("Error sending test alert: %s", err)
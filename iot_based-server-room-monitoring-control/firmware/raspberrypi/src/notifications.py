#!/usr/bin/env python3
"""
notifications.py

This module is responsible for sending alert notifications via multiple channels.
It currently supports:
  - SMS/MMS alerts via the Twilio API
  - Email alerts via SMTP

The main function, send_alert(), accepts detailed data (e.g., timestamp, video file URL)
and sends the alert using the specified channels.

Dependencies:
  - twilio (install via: pip install twilio)
  - Standard Python libraries: smtplib, email

Configuration:
  - Update the TWILIO_* constants with your Twilio credentials.
  - Update the SMTP_* and EMAIL_* constants with your email server settings.
"""

import logging
import os
from datetime import datetime
from twilio.rest import Client
import smtplib
from email.message import EmailMessage

# Configure logging for debugging and operational visibility
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Twilio Credentials (for SMS/MMS) ---
TWILIO_ACCOUNT_SID = "your_account_sid_here"
TWILIO_AUTH_TOKEN  = "your_auth_token_here"
TWILIO_FROM_NUMBER = "+1234567890"  # Your Twilio phone number
TWILIO_TO_NUMBER   = "+0987654321"  # Recipient phone number (admin)

# --- Email SMTP Configuration ---
SMTP_SERVER   = "smtp.example.com"      # e.g., smtp.gmail.com
SMTP_PORT     = 587                     # Typically 587 for TLS
SMTP_USERNAME = "your_email@example.com"
SMTP_PASSWORD = "your_email_password"
EMAIL_FROM    = "your_email@example.com"  # Sender's email address
EMAIL_TO      = "recipient@example.com"   # Recipient's email address

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

def send_alert(message, media_url=None, event_timestamp=None, channels=None):
    """
    Sends an alert via multiple channels. By default, it sends SMS alerts.
    Optionally, email alerts can be sent if specified in the channels list.

    Args:
        message (str): The alert message to send.
        media_url (str, optional): URL to a media file (video or image) to include in the alert.
        event_timestamp (datetime, optional): The timestamp of the event.
        channels (list, optional): List of channels to send the alert. Options include
                                   'sms' and 'email'. Defaults to ['sms'].

    Returns:
        dict: A dictionary containing the status of each channel alert.
              e.g., {"sms": "SID12345", "email": "sent"}.
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

    return results

if __name__ == "__main__":
    # Test sending an alert via both SMS and Email when running this module standalone.
    test_message = "Test alert from IoT-based Server Room Monitoring System."
    test_media_url = "http://example.com/video_sample.h264"
    test_timestamp = datetime.now()

    try:
        result = send_alert(test_message, media_url=test_media_url, event_timestamp=test_timestamp, channels=["sms", "email"])
        print("Alert send results:", result)
    except Exception as err:
        print(f"Error sending test alert: {err}")

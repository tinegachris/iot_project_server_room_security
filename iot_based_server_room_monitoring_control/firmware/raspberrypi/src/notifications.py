#!/home/admin/iot_project_server_room_security/venv/bin/python3
"""
notifications.py

This module handles alert notifications for the server room monitoring system.
It integrates with the sensor and camera modules to provide comprehensive alerts
via multiple channels (SMS, Email, FCM) when security events are detected.

Dependencies:
    - twilio (install via: pip install twilio)
    - requests (install via: pip install requests)
    - python-dotenv (install via: pip install python-dotenv)
"""

import logging
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from twilio.rest import Client
import smtplib
from email.message import EmailMessage
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class AlertData:
    """Data structure for alert information."""
    event_type: str
    message: str
    timestamp: datetime
    media_url: Optional[str] = None
    sensor_data: Optional[Dict[str, Any]] = None
    severity: str = "high"

class NotificationManager:
    """Manages notification channels and alert handling."""

    def __init__(self):
        """Initialize notification channels and configurations."""
        self._setup_twilio()
        self._setup_email()
        self._setup_fcm()
        logger.info("Notification manager initialized")

    def _setup_twilio(self) -> None:
        """Setup Twilio configuration."""
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from = os.getenv("TWILIO_FROM_NUMBER")
        self.twilio_to = os.getenv("TWILIO_TO_NUMBER")
        self.twilio_client = Client(self.twilio_sid, self.twilio_token) if all([
            self.twilio_sid, self.twilio_token, self.twilio_from, self.twilio_to
        ]) else None

    def _setup_email(self) -> None:
        """Setup email configuration."""
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_to = os.getenv("EMAIL_TO")
        self.email_configured = all([
            self.smtp_server, self.smtp_port, self.smtp_username,
            self.smtp_password, self.email_from, self.email_to
        ])

    def _setup_fcm(self) -> None:
        """Setup Firebase Cloud Messaging configuration."""
        self.fcm_key = os.getenv("FCM_SERVER_KEY")
        self.fcm_token = os.getenv("FCM_DEVICE_TOKEN")
        self.fcm_configured = all([self.fcm_key, self.fcm_token])

    def _send_sms(self, alert: AlertData) -> Optional[str]:
        """Send SMS alert via Twilio."""
        if not self.twilio_client:
            logger.warning("Twilio not configured, skipping SMS alert")
            return None

        try:
            msg_params = {
                "body": self._format_message(alert),
                "from_": self.twilio_from,
                "to": self.twilio_to
            }
            if alert.media_url:
                msg_params["media_url"] = [alert.media_url]

            sent_msg = self.twilio_client.messages.create(**msg_params)
            logger.info("SMS alert sent successfully: %s", sent_msg.sid)
            return sent_msg.sid
        except Exception as e:
            logger.error("Failed to send SMS alert: %s", e)
            return None

    def _send_email(self, alert: AlertData) -> bool:
        """Send email alert via SMTP."""
        if not self.email_configured:
            logger.warning("Email not configured, skipping email alert")
            return False

        try:
            msg = EmailMessage()
            msg.set_content(self._format_message(alert))
            msg["Subject"] = f"Server Room Alert: {alert.event_type}"
            msg["From"] = self.email_from
            msg["To"] = self.email_to

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info("Email alert sent successfully")
            return True
        except Exception as e:
            logger.error("Failed to send email alert: %s", e)
            return False

    def _send_fcm(self, alert: AlertData) -> bool:
        """Send push notification via Firebase Cloud Messaging."""
        if not self.fcm_configured:
            logger.warning("FCM not configured, skipping push notification")
            return False

        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'key={self.fcm_key}',
            }
            payload = {
                'to': self.fcm_token,
                'notification': {
                    'title': f"Server Room Alert: {alert.event_type}",
                    'body': alert.message,
                },
                'data': {
                    'event_type': alert.event_type,
                    'severity': alert.severity,
                    'timestamp': alert.timestamp.isoformat(),
                    'media_url': alert.media_url or '',
                }
            }
            response = requests.post(
                'https://fcm.googleapis.com/fcm/send',
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            logger.info("FCM alert sent successfully")
            return True
        except Exception as e:
            logger.error("Failed to send FCM alert: %s", e)
            return False

    def _format_message(self, alert: AlertData) -> str:
        """Format alert message with all relevant information."""
        message = [
            f"Server Room Alert: {alert.event_type}",
            f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Message: {alert.message}",
            f"Severity: {alert.severity}"
        ]

        if alert.sensor_data:
            message.append("\nSensor Data:")
            for key, value in alert.sensor_data.items():
                message.append(f"- {key}: {value}")

        if alert.media_url:
            message.append(f"\nMedia URL: {alert.media_url}")

        return "\n".join(message)

    def send_alert(self, alert: AlertData, channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Send alert through specified channels.

        Args:
            alert: AlertData object containing alert information
            channels: List of channels to use ('sms', 'email', 'fcm'). If None, uses all configured channels.

        Returns:
            Dict containing results for each channel
        """
        if channels is None:
            channels = ['sms', 'email', 'fcm']

        results = {}

        if 'sms' in channels:
            results['sms'] = self._send_sms(alert)

        if 'email' in channels:
            results['email'] = "sent" if self._send_email(alert) else "failed"

        if 'fcm' in channels:
            results['fcm'] = "sent" if self._send_fcm(alert) else "failed"

        return results

def create_intrusion_alert(
    event_type: str,
    message: str,
    media_url: Optional[str] = None,
    sensor_data: Optional[Dict[str, Any]] = None
) -> AlertData:
    """Create an alert for intrusion events."""
    return AlertData(
        event_type=event_type,
        message=message,
        timestamp=datetime.now(),
        media_url=media_url,
        sensor_data=sensor_data,
        severity="high"
    )

def create_rfid_alert(
    event_type: str,
    message: str,
    uid: str,
    role: Optional[str] = None,
    media_url: Optional[str] = None
) -> AlertData:
    """Create an alert for RFID events."""
    sensor_data = {"card_uid": uid}
    if role:
        sensor_data["role"] = role

    return AlertData(
        event_type=event_type,
        message=message,
        timestamp=datetime.now(),
        media_url=media_url,
        sensor_data=sensor_data,
        severity="high" if event_type == "unauthorized_access" else "medium"
    )

def main() -> None:
    """Test the notification system."""
    notification_manager = NotificationManager()

    # Test intrusion alert
    intrusion_alert = create_intrusion_alert(
        event_type="motion_detected",
        message="Motion detected in server room",
        media_url="http://example.com/video.h264",
        sensor_data={"location": "main_entrance", "duration": "5s"}
    )
    results = notification_manager.send_alert(intrusion_alert)
    logger.info("Intrusion alert results: %s", results)

    # Test RFID alert
    rfid_alert = create_rfid_alert(
        event_type="unauthorized_access",
        message="Unauthorized RFID access attempt",
        uid="123-456-789",
        media_url="http://example.com/image.jpg"
    )
    results = notification_manager.send_alert(rfid_alert)
    logger.info("RFID alert results: %s", results)

if __name__ == "__main__":
    main()
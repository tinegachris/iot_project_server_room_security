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

    def _validate_twilio_credentials(self, sid: str, token: str) -> bool:
        """Validate Twilio credentials format."""
        if not sid or sid == "your-twilio-sid":
            return False
        if not token or len(token) < 32:  # Twilio auth tokens are typically longer
            return False
        return True

    def _validate_email_config(self, server: str, port: int, username: str, password: str) -> bool:
        """Validate email configuration."""
        if not server or server == "smtp.example.com":
            return False
        if not username or not password:
            return False
        if port < 1 or port > 65535:
            return False
        return True

    def _validate_fcm_config(self, key: str, token: str) -> bool:
        """Validate FCM configuration."""
        if not key or not key.startswith("AAAA"):
            return False
        if not token or len(token) < 100:  # FCM tokens are typically long
            return False
        return True

    def _handle_twilio_error(self, error: Exception) -> None:
        """Handle Twilio-specific errors and provide guidance."""
        error_str = str(error)
        if "21608" in error_str:
            logger.error("""
            Twilio Trial Account Error:
            - Your phone number is not verified
            - Please verify your number at: https://www.twilio.com/console/phone-numbers/verified
            - Or upgrade to a paid account to send to unverified numbers
            """)
        elif "20003" in error_str:
            logger.error("""
            Twilio Authentication Error:
            - Invalid Account SID or Auth Token
            - Please check your TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
            """)
        else:
            logger.error("Twilio error: %s", error_str)

    def _handle_email_error(self, error: Exception) -> None:
        """Handle email-specific errors and provide guidance."""
        error_str = str(error)
        if "535" in error_str and "gmail" in self.smtp_server.lower():
            logger.error("""
            Gmail Authentication Error:
            - Username and password not accepted
            - For Gmail, you need to use an App Password
            - Steps to create an App Password:
              1. Enable 2-Step Verification in your Google Account
              2. Go to Google Account > Security > App Passwords
              3. Generate a new App Password for this application
              4. Use the generated password in SMTP_PASSWORD
            """)
        elif "535" in error_str:
            logger.error("""
            SMTP Authentication Error:
            - Invalid username or password
            - Please check your SMTP_USERNAME and SMTP_PASSWORD
            """)
        else:
            logger.error("Email error: %s", error_str)

    def _setup_twilio(self) -> None:
        """Setup Twilio configuration."""
        self.twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from = os.getenv("TWILIO_FROM_NUMBER")
        self.twilio_to = os.getenv("TWILIO_TO_NUMBER")
        
        if all([self.twilio_sid, self.twilio_token, self.twilio_from, self.twilio_to]):
            if self._validate_twilio_credentials(self.twilio_sid, self.twilio_token):
                self.twilio_client = Client(self.twilio_sid, self.twilio_token)
                logger.info("Twilio SMS configured successfully")
            else:
                self.twilio_client = None
                logger.warning("Invalid Twilio credentials format")
        else:
            self.twilio_client = None
            missing = []
            if not self.twilio_sid or self.twilio_sid == "your-twilio-sid": missing.append("TWILIO_ACCOUNT_SID")
            if not self.twilio_token: missing.append("TWILIO_AUTH_TOKEN")
            if not self.twilio_from: missing.append("TWILIO_FROM_NUMBER")
            if not self.twilio_to: missing.append("TWILIO_TO_NUMBER")
            logger.warning("Twilio SMS not configured. Missing or invalid environment variables: %s", ", ".join(missing))

    def _setup_email(self) -> None:
        """Setup email configuration."""
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_to = os.getenv("EMAIL_TO")
        
        if all([self.smtp_server, self.smtp_port, self.smtp_username,
                self.smtp_password, self.email_from, self.email_to]):
            if self._validate_email_config(self.smtp_server, self.smtp_port, 
                                        self.smtp_username, self.smtp_password):
                self.email_configured = True
                logger.info("Email notifications configured successfully")
            else:
                self.email_configured = False
                logger.warning("Invalid email configuration format")
        else:
            self.email_configured = False
            missing = []
            if not self.smtp_server or self.smtp_server == "smtp.example.com": missing.append("SMTP_SERVER")
            if not self.smtp_username: missing.append("SMTP_USERNAME")
            if not self.smtp_password: missing.append("SMTP_PASSWORD")
            if not self.email_from: missing.append("EMAIL_FROM")
            if not self.email_to: missing.append("EMAIL_TO")
            logger.warning("Email notifications not configured. Missing or invalid environment variables: %s", ", ".join(missing))

    def _setup_fcm(self) -> None:
        """Setup Firebase Cloud Messaging configuration."""
        self.fcm_key = os.getenv("FCM_SERVER_KEY")
        self.fcm_token = os.getenv("FCM_DEVICE_TOKEN")
        
        if all([self.fcm_key, self.fcm_token]):
            if self._validate_fcm_config(self.fcm_key, self.fcm_token):
                self.fcm_configured = True
                logger.info("FCM notifications configured successfully")
            else:
                self.fcm_configured = False
                logger.warning("Invalid FCM configuration format")
        else:
            self.fcm_configured = False
            missing = []
            if not self.fcm_key or not self.fcm_key.startswith("AAAA"): missing.append("FCM_SERVER_KEY")
            if not self.fcm_token: missing.append("FCM_DEVICE_TOKEN")
            logger.warning("FCM notifications not configured. Missing or invalid environment variables: %s", ", ".join(missing))

    def _send_sms(self, alert: AlertData) -> Optional[str]:
        """Send SMS alert via Twilio."""
        if not self.twilio_client:
            logger.warning("SMS alert skipped - Twilio not configured")
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
            self._handle_twilio_error(e)
            return None

    def _send_email(self, alert: AlertData) -> bool:
        """Send email alert via SMTP."""
        if not self.email_configured:
            logger.warning("Email alert skipped - Email not configured")
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
            self._handle_email_error(e)
            return False

    def _send_fcm(self, alert: AlertData) -> bool:
        """Send push notification via Firebase Cloud Messaging."""
        if not self.fcm_configured:
            logger.warning("""
            FCM alert skipped - FCM not configured
            To configure FCM:
            1. Create a Firebase project
            2. Get the Server Key from Project Settings > Cloud Messaging
            3. Get the Device Token from your mobile app
            4. Set FCM_SERVER_KEY and FCM_DEVICE_TOKEN environment variables
            """)
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
        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 404:
                logger.error("""
                FCM Error: Invalid device token
                - The FCM_DEVICE_TOKEN is not valid
                - Make sure you're using a valid token from your mobile app
                """)
            elif e.response and e.response.status_code == 401:
                logger.error("""
                FCM Error: Invalid server key
                - The FCM_SERVER_KEY is not valid
                - Make sure you're using the correct key from Firebase Console
                """)
            else:
                logger.error("FCM error: %s", str(e))
            return False
        except Exception as e:
            logger.error("Unexpected FCM error: %s", str(e))
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
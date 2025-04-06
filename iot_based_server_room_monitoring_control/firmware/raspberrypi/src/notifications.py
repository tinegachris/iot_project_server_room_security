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
import json
import copy # ✅ Import copy for deep copies

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
    severity: str = "error"

class NotificationManager:
    """Manages notification channels and alert handling."""

    def __init__(self):
        """Initialize notification channels and configurations."""
        self._setup_twilio()
        self._setup_email()
        self._setup_fcm()
        self._setup_server_api()
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

    def _setup_server_api(self) -> None:
        """Setup main server API configuration."""
        self.server_api_url = os.getenv("SERVER_API_URL")
        self.api_key = os.getenv("RASPBERRY_PI_API_KEY")

        if self.server_api_url and self.api_key:
            if not self.server_api_url.startswith("http"):
                logger.warning("Invalid SERVER_API_URL format. Should start with http or https.")
                self.server_api_configured = False
            elif not self.api_key or len(self.api_key) < 10:
                logger.warning("RASPBERRY_PI_API_KEY seems invalid or too short.")
                self.server_api_configured = False
            else:
                self.server_api_configured = True
                self.server_events_endpoint = self.server_api_url.rstrip('/') + "/events"
                logger.info("Server API event reporting configured successfully to %s", self.server_events_endpoint)
        else:
            self.server_api_configured = False
            missing = []
            if not self.server_api_url: missing.append("SERVER_API_URL")
            if not self.api_key: missing.append("RASPBERRY_PI_API_KEY")
            logger.warning("Server API event reporting not configured. Missing environment variables: %s", ", ".join(missing))

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

    def _send_to_server(self, alert: AlertData) -> bool:
        """Send event data to the main server's /events endpoint."""
        if not self.server_api_configured:
            logger.warning("Event reporting to server skipped - Server API not configured")
            return False

        try:
            # Prepare data matching the server's RaspberryPiEvent schema
            # Ensure severity is a valid enum value expected by the server
            valid_severities = ["info", "warning", "error", "critical"]
            payload_severity = alert.severity.lower() if isinstance(alert.severity, str) else "info" # Default to info
            if payload_severity not in valid_severities:
                 logger.warning(f"Invalid severity '{alert.severity}' for event '{alert.event_type}'. Defaulting to 'info'.")
                 payload_severity = "info"

            # Attempt to make sensor_data JSON serializable (basic approach)
            serializable_sensor_data = None
            if isinstance(alert.sensor_data, dict):
                try:
                    # Create a copy to avoid modifying the original alert object
                    data_copy = copy.deepcopy(alert.sensor_data)
                    # Attempt to convert non-serializable items (e.g., datetime) to strings
                    for key, value in data_copy.items():
                        if isinstance(value, datetime):
                            data_copy[key] = value.isoformat()
                        # Add more conversions if needed (e.g., for custom objects)

                    # Test if it dumps without error before sending
                    json.dumps(data_copy)
                    serializable_sensor_data = data_copy
                except TypeError as json_err:
                    logger.warning(f"Could not make sensor_data fully JSON serializable for event '{alert.event_type}': {json_err}. Sending without it.")
                    serializable_sensor_data = {"error": "Data not serializable"}
                except Exception as deepcopy_err:
                     logger.warning(f"Could not deepcopy sensor_data for event '{alert.event_type}': {deepcopy_err}. Sending without it.")
                     serializable_sensor_data = {"error": "Data could not be copied"}
            elif alert.sensor_data is not None:
                # Handle cases where sensor_data is not a dict but also not None
                logger.warning(f"Sensor data for event '{alert.event_type}' is not a dictionary. Type: {type(alert.sensor_data)}. Sending as string.")
                serializable_sensor_data = {"raw": str(alert.sensor_data)}

            payload = {
                "event_type": alert.event_type,
                "timestamp": alert.timestamp.isoformat(),
                "message": alert.message,
                "sensor_data": serializable_sensor_data, # Use potentially cleaned data
                "media_url": alert.media_url,
                "severity": payload_severity,
                "source": "raspberry_pi"
            }

            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key
            }

            logger.debug(f"Sending event payload to server: {json.dumps(payload)}") # Log the actual payload

            response = requests.post(
                self.server_events_endpoint,
                headers=headers,
                data=json.dumps(payload), # Serialize final payload to JSON string
                timeout=10
            )

            # Check specifically for 422 error
            if response.status_code == 422:
                logger.error(f"Failed to send event '{alert.event_type}' to server. Status: 422 Unprocessable Entity. Response: {response.text}")
                # Log the payload that failed validation for debugging
                logger.error(f"Failing Payload: {json.dumps(payload)}")
                return False
            
            response.raise_for_status()

            logger.info(f"Event '{alert.event_type}' sent to server successfully. Status: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send event '{alert.event_type}' to server: {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending event '{alert.event_type}' to server: {e}", exc_info=True)
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

    def send_alert(self, alert: AlertData, channels: Optional[List[str]] = None) -> None:
        """Send alert via specified or all configured channels."""
        logger.info("Sending alert for event: %s", alert.event_type)

        server_success = self._send_to_server(alert)
        if not server_success:
            logger.warning(f"Failed to log event {alert.event_type} to the main server.")

        target_channels = channels or ['sms', 'email', 'fcm']

        if "sms" in target_channels:
            self._send_sms(alert)
        if "email" in target_channels:
            self._send_email(alert)
        if "fcm" in target_channels:
            self._send_fcm(alert)

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
        severity="critical"
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
        severity="critical" if event_type == "unauthorized_access" else "medium"
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
    notification_manager.send_alert(intrusion_alert)

    # Test RFID alert
    rfid_alert = create_rfid_alert(
        event_type="unauthorized_access",
        message="Unauthorized RFID access attempt",
        uid="123-456-789",
        media_url="http://example.com/image.jpg"
    )
    notification_manager.send_alert(rfid_alert)

if __name__ == "__main__":
    main()
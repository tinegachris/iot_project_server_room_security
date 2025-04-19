# IoT-based Server Room Monitoring System

A comprehensive server room security monitoring system built for Raspberry Pi that integrates multiple sensors, video surveillance, and notification channels.

## Features

- **Multi-Sensor Integration**
  - PIR motion detection
  - Door and window intrusion detection using reed switches
  - RFID-based access control with MFRC522 reader
  - Visual LED indicators for each sensor

- **Video Surveillance**
  - High-resolution image capture (configurable up to 1920x1080)
  - Video recording on security events
  - Cloud storage integration for remote access
  - Configurable camera settings (resolution, framerate, rotation)

- **Access Control**
  - RFID card authentication
  - Role-based access control
  - Unauthorized access detection and logging
  - Real-time access notifications

- **Notification System**
  - Multi-channel alerts (SMS via Twilio, Email via SMTP, Push via FCM)
  - Configurable notification channels
  - Rich alert content including media and sensor data
  - Severity-based alert handling

- **System Monitoring**
  - Regular health checks
  - Storage space monitoring
  - System uptime tracking
  - Comprehensive logging

## Hardware Requirements

- Raspberry Pi (3B+ or 4 recommended)
- Pi Camera Module v2 or v3
- PIR Motion Sensor (HC-SR501 or similar)
- Door/Window Reed Switches
- MFRC522 RFID Reader
- LED indicators (optional, for visual feedback)

## Software Requirements

- Python 3.8+
- Raspberry Pi OS (latest version recommended)
- Required Python packages:
  - RPi.GPIO
  - gpiozero
  - picamera
  - spidev
  - twilio
  - requests
  - python-dotenv

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd iot_based_server_room_monitoring_control/firmware/raspberrypi
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file in the project root with the following variables:

```env
# Database Configuration
DATABASE_URL=sqlite:///./<DATABASE_NAME>.db

# Security Keys
SECRET_KEY=<SECRET_KEY>
JWT_SECRET=<JWT_SECRET>

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID=<TWILIO_ACCOUNT_SID>
TWILIO_AUTH_TOKEN=<TWILIO_AUTH_TOKEN>
TWILIO_FROM_NUMBER=<TWILIO_FROM_NUMBER>
TWILIO_TO_NUMBER=<TWILIO_TO_NUMBER>

# Email Configuration
SMTP_SERVER=<SMTP_SERVER>
SMTP_PORT=<SMTP_PORT>
SMTP_USERNAME=<SMTP_USERNAME>
SMTP_PASSWORD=<SMTP_PASSWORD>
EMAIL_FROM=<EMAIL_FROM>
EMAIL_TO=<EMAIL_TO>

# Firebase Cloud Messaging
FCM_SERVER_KEY=<FCM_SERVER_KEY>
FCM_DEVICE_TOKEN=<FCM_DEVICE_TOKEN>

# Server Configuration
LOG_LEVEL=<LOG_LEVEL>
ALLOWED_IPS=<ALLOWED_IPS>

# Redis Configuration
REDIS_HOST=<REDIS_HOST>
REDIS_PORT=<REDIS_PORT>
REDIS_DB=<REDIS_DB>
REDIS_PASSWORD=<REDIS_PASSWORD>

# Cloud Storage Configuration
CLOUD_STORAGE_ACCESS_KEY=<CLOUD_STORAGE_ACCESS_KEY>
CLOUD_STORAGE_SECRET_KEY=<CLOUD_STORAGE_SECRET_KEY>

# Raspberry Pi Configuration
RASPBERRY_PI_API_URL=<RASPBERRY_PI_API_URL>
RASPBERRY_PI_API_KEY=<RASPBERRY_PI_API_KEY>
RASPBERRY_PI_API_PORT=<RASPBERRY_PI_API_PORT>

# GPIO Pin Configuration
MOTION_SENSOR_PIN=<MOTION_SENSOR_PIN>
DOOR_SENSOR_PIN=<DOOR_SENSOR_PIN>
WINDOW_SENSOR_PIN=<WINDOW_SENSOR_PIN>

# Project Base Directory
PROJECT_DIR=<PROJECT_DIR>

# Camera Settings
CAMERA_RESOLUTION=<CAMERA_RESOLUTION>
VIDEO_FPS=<VIDEO_FPS>
CAMERA_ROTATION=<CAMERA_ROTATION>
CAMERA_BRIGHTNESS=<CAMERA_BRIGHTNESS>
VIDEO_OUTPUT_DIR=<VIDEO_OUTPUT_DIR>
IMAGE_OUTPUT_DIR=<IMAGE_OUTPUT_DIR>
VIDEO_DURATION=<VIDEO_DURATION>
MAX_STORAGE_GB=<MAX_STORAGE_GB>
VIDEO_RETENTION_DAYS=<VIDEO_RETENTION_DAYS>

# Sensor Settings
MOTION_SENSITIVITY=<MOTION_SENSITIVITY>
MOTION_TRIGGER_DELAY=<MOTION_TRIGGER_DELAY>
MOTION_DEBOUNCE_TIME=<MOTION_DEBOUNCE_TIME>
DOOR_DEBOUNCE_TIME=<DOOR_DEBOUNCE_TIME>
WINDOW_DEBOUNCE_TIME=<WINDOW_DEBOUNCE_TIME>

# Monitoring Settings
HEALTH_CHECK_INTERVAL=<HEALTH_CHECK_INTERVAL>
MAX_RETRIES=<MAX_RETRIES>
STORAGE_THRESHOLD_GB=<STORAGE_THRESHOLD_GB>
MAX_LOG_RETENTION_DAYS=<MAX_LOG_RETENTION_DAYS>
MAX_VIDEO_RETENTION_DAYS=<MAX_VIDEO_RETENTION_DAYS>
EVENT_COOLDOWN=<EVENT_COOLDOWN>
CLEANUP_INTERVAL=<CLEANUP_INTERVAL>
HEARTBEAT_INTERVAL=<HEARTBEAT_INTERVAL>
OFFLINE_THRESHOLD=<OFFLINE_THRESHOLD>

# Control PINS
DOOR_LOCK_PIN=<DOOR_LOCK_PIN>
WINDOW_LOCK_PIN=<WINDOW_LOCK_PIN>

# Main Server API Configuration
SERVER_API_URL=<SERVER_API_URL>
```

## GPIO Pin Configuration

- Motion Sensor: GPIO 17 (configurable via MOTION_SENSOR_PIN)
- Door Sensor: GPIO 27 (configurable via DOOR_SENSOR_PIN)
- Window Sensor: GPIO 22 (configurable via WINDOW_SENSOR_PIN)
- RFID Reader: SPI0 (GPIO 8-11)
- LED Indicators:
  - Motion: GPIO 23
  - Door: GPIO 24
  - Window: GPIO 25

## Usage

1. Start the monitoring system:
```bash
python src/main.py
```

2. The system will automatically:
   - Initialize all sensors and camera
   - Start monitoring for security events
   - Handle RFID authentication
   - Capture and upload media on events
   - Send notifications through configured channels
   - Perform regular health checks

## System Architecture

The system is organized into several key modules:

- `main.py`: Core system coordinator
- `sensors.py`: Sensor management and event handling
- `camera.py`: Video surveillance and media capture
- `rfid.py`: RFID reader interface and authentication
- `motion.py`: Motion, door, and window sensor handling
- `notifications.py`: Multi-channel alert system

## Error Handling

The system implements comprehensive error handling:

- Graceful degradation on sensor failures
- Automatic retry mechanisms
- Detailed error logging
- Resource cleanup on shutdown
- Health check monitoring
- Storage space monitoring

## Security Features

- Environment variable-based configuration
- Secure RFID authentication
- Role-based access control
- Encrypted media transmission
- Comprehensive audit logging
- Configurable alert severity levels

## Development Notes

For Windows development:
```powershell
$env:READTHEDOCS="True"
pip install picamera
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

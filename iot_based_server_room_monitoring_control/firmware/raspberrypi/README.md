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
DATABASE_URL=sqlite:///./server_room_monitor.db
SECRET_KEY=your-secret-key-here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_FROM_NUMBER=your-twilio-number
TWILIO_TO_NUMBER=your-target-number

# Email Configuration
SMTP_SERVER=your-smtp-server
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=your-email
EMAIL_TO=target-email

# Firebase Configuration
FCM_SERVER_KEY=your-fcm-key
FCM_DEVICE_TOKEN=your-device-token

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
API_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# Monitoring Settings
HEALTH_CHECK_INTERVAL=300  # 5 minutes
MAX_LOG_RETENTION_DAYS=30
MAX_VIDEO_RETENTION_DAYS=7

# Hardware Settings
MOTION_SENSOR_PIN=17
DOOR_SENSOR_PIN=27
RFID_READER_PORT=/dev/ttyUSB0
CAMERA_RESOLUTION=1920x1080
VIDEO_FPS=30
VIDEO_DURATION=10  # seconds
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

The error you're encountering while attempting to install the picamera library on your Windows system arises because picamera is specifically designed for Raspberry Pi devices running a Linux-based operating system. During installation, it tries to access /proc/cpuinfo, a file present in Linux systems that provides CPU information, but absent in Windows environments. This discrepancy leads to the FileNotFoundError you've observed.

If your goal is to develop or test code that will eventually run on a Raspberry Pi, you might want to install picamera on your Windows system to enable code completion and linting in your development environment. While the library won't functionally operate on Windows, installing it can help maintain a smoother development workflow. To achieve this, you can set the READTHEDOCS environment variable to True before installation, which bypasses certain checks during the setup process:

For Windows PowerShell:

powershell

$env:READTHEDOCS="True"
pip install picamera

## RFID Reader Setup

https://store.nerokas.co.ke/SKU-841

https://geraintw.blogspot.com/2014/01/rfid-and-raspberry-pi.html
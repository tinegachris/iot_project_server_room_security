# Backend API Code

...existing content...

 main.py file.

Access Control Check:
The new call rfid_violation = sensors.check_rfid() is added to detect unauthorized RFID scans. You’ll need to implement this function in your sensors module.

Combined Condition:
The code checks if either intrusion_detected or rfid_violation is True. If so, it records a video using the camera module and sends an alert using the notifications module.

Alert Message:
The alert message is built dynamically to mention whether the trigger was due to a motion/door event, an unauthorized RFID scan, or both.

Window Sensor:
A new sensor object (window_sensor) is created on a designated GPIO pin (27) and integrated into check_intrusion().

RFID Handling:
The check_rfid() function is added as a placeholder to simulate RFID-based access control. Replace its logic with your actual RFID reader code when ready.

Camera Settings Parameters:
The record_video() function now accepts optional parameters—resolution, framerate, rotation, and brightness—allowing you to adjust the camera configuration to better suit surveillance needs (such as optimizing for low light).

Settings Application:
These settings are applied immediately after the camera is instantiated so that every video recording is captured with the specified parameters.

Integration with Intrusion Events:
As your main loop (in main.py) calls record_video() when an intrusion is detected, these settings help ensure that the captured footage is optimized for your monitoring scenario.

SMS Alert:
The existing Twilio-based SMS functionality is preserved in send_sms_alert().

Email Alert:
A new function send_email_alert() is added that builds an email (including an optional event timestamp and media URL) and sends it via SMTP.
Update the SMTP and email configuration values as needed.

send_alert() Interface:
The unified send_alert() function now accepts a list of channels (defaulting to SMS). It sends alerts through all requested channels and returns a status dictionary with results (e.g., the Twilio message SID for SMS and a simple confirmation for email).

Testing Block:
When run as a standalone script, the module tests both SMS and email alerts, sending a test message along with a sample media URL and timestamp.

Main API File (main.py):
Initializes the FastAPI application and includes the router from routes.py under the /api prefix.

Routes File (routes.py):

GET /status: Returns a dummy status with the current timestamp.
GET /logs: Returns an in-memory list of log entries (for demonstration).
POST /alert: Accepts an alert payload (using the Alert model) and logs it as a manual alert. In production, this endpoint would trigger your notifications module (SMS/email) and store the event in a database.
POST /control: Accepts a simple control command (like "lock" or "unlock") and returns a response confirming execution.

Models (models.py):

AccessLog: Stores user RFID scan attempts including user ID, status, and optional details.
SensorEvent: Logs events triggered by sensors (motion, door, window, RFID).
VideoRecord: Logs video recordings with file path (or cloud URL), record time, and the event type that triggered recording.
Controllers (controllers.py):

Functions such as log_access_attempt(), log_sensor_event(), and log_video_record() accept a SQLAlchemy session to write records into the database.
The process_alert_and_event() function shows how you might aggregate an event that involves both sensor data and a video recording. This is where you can add business logic for cloud integration.
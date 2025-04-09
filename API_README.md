# API Documentation

## Authentication

### POST /api/v1/token
- **Description**: Obtain a JWT token for authentication.
- **Request**: Form data with `username` and `password`.
- **Response**: JSON with `access_token` and `token_type`.

## Endpoints

### GET /api/v1/status
- **Description**: Retrieve the current status of the server room, including system health metrics and sensor status.
- **Authentication**: Bearer token in the `Authorization` header.
- **Response**: JSON with system health and sensor status.

### GET /api/v1/logs
- **Description**: Retrieve log entries with optional filtering.
- **Authentication**: Bearer token in the `Authorization` header.
- **Query Parameters**: `skip`, `limit`, `event_type`, `start_date`, `end_date`.
- **Response**: JSON with logs and pagination details.

### POST /api/v1/control
- **Description**: Send control commands to the Raspberry Pi.
- **Authentication**: Bearer token in the `Authorization` header.
- **Request**: JSON with `action` and optional `parameters`.
- **Response**: JSON with command execution result.

### GET /api/v1/sensors/{sensor_type}
- **Description**: Retrieve data for a specific sensor type.
- **Authentication**: Bearer token in the `Authorization` header.
- **Response**: JSON with sensor data.

### POST /api/v1/alert
- **Description**: Manually trigger an alert.
- **Authentication**: Bearer token in the `Authorization` header.
- **Request**: JSON with `message` and optional `video_url`.
- **Response**: JSON confirming alert processing.

### POST /api/v1/events
- **Description**: Endpoint for Raspberry Pi to send event data.
- **Authentication**: API Key in the `X-API-Key` header.
- **Request**: JSON with event details.
- **Response**: JSON confirming event receipt.

## User Management

### POST /api/v1/users
- **Description**: Create a new user.
- **Request**: JSON with `username`, `password`, `email`, and `is_admin`.
- **Response**: JSON with user details.

### GET /api/v1/users/{user_id}
- **Description**: Retrieve user details by ID.
- **Authentication**: Bearer token in the `Authorization` header.
- **Response**: JSON with user details.

### PUT /api/v1/users/{user_id}
- **Description**: Update user details by ID.
- **Authentication**: Bearer token in the `Authorization` header.
- **Request**: JSON with fields to update.
- **Response**: JSON with updated user details.

### DELETE /api/v1/users/{user_id}
- **Description**: Delete a user by ID.
- **Authentication**: Bearer token in the `Authorization` header.
- **Response**: JSON confirming user deletion.

## Notes
- All endpoints require authentication unless specified otherwise.
- Use the JWT token obtained from `/api/v1/token` for Bearer authentication.
- API Key is required for Raspberry Pi communication endpoints.

## Token Usage Example

To authenticate and obtain a token, use the following `curl` command:

```bash
curl -X POST "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
```

- **Description**: This command authenticates with the server using the provided username and password, returning a JWT token for further API requests.
- **Response**: JSON containing the `access_token` and `token_type`.

Use the `access_token` in the `Authorization` header for subsequent requests:

```http
Authorization: Bearer <access_token>
```

### Status Endpoint Example

To check the server room status, use the following `curl` command:

```bash
curl -X GET "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/status" \
     -H "Authorization: Bearer <access_token>"
```

- **Description**: This command retrieves the current status of the server room, including sensor and system health metrics.
- **Response**: JSON with detailed status information, including sensor activity, storage usage, and Raspberry Pi connectivity.

Example response:

```json
{
  "status": "degraded",
  "sensors": {
    "camera": {"name": "camera", "is_active": false, "last_check": "2025-04-09T05:45:21.731596", "error": null, "data": null, "location": "main_camera", "type": "camera", "firmware_version": null, "last_event": null, "event_count": 0},
    "door": {"name": "door", "is_active": true, "last_check": "2025-04-09T06:05:45.130764", "error": null, "data": {"open": false}, "location": "pin_17", "type": "door", "firmware_version": null, "last_event": null, "event_count": 0},
    "door_lock": {"name": "door_lock", "is_active": false, "last_check": "2025-04-09T05:45:21.731666", "error": null, "data": null, "location": "pin_25", "type": "actuator", "firmware_version": null, "last_event": null, "event_count": 0},
    "motion": {"name": "motion", "is_active": true, "last_check": "2025-04-09T06:05:44.456653", "error": null, "data": {"detected": false}, "location": "pin_4", "type": "motion", "firmware_version": null, "last_event": null, "event_count": 0},
    "rfid": {"name": "rfid", "is_active": false, "last_check": "2025-04-09T05:45:21.730087", "error": null, "data": null, "location": "main_reader", "type": "rfid", "firmware_version": null, "last_event": null, "event_count": 0},
    "window": {"name": "window", "is_active": true, "last_check": "2025-04-09T06:05:45.134648", "error": null, "data": {"open": false}, "location": "pin_27", "type": "window", "firmware_version": null, "last_event": null, "event_count": 0}
  },
  "storage": {"total_gb": 28, "used_gb": 9, "free_gb": 17, "low_space": false},
  "uptime": "0:28:15",
  "last_maintenance": null,
  "next_maintenance": null,
  "errors": ["camera sensor is inactive", "door_lock sensor is inactive", "rfid sensor is inactive"],
  "raspberry_pi": {"is_online": true, "last_heartbeat": "2025-04-09T06:05:45.468104", "firmware_version": "unknown", "sensor_types": ["camera", "door", "actuator", "motion", "rfid", "window"], "total_events": 0}
}
```

### Control Endpoint Example

To send a control command to the Raspberry Pi, use the following `curl` command:

```bash
curl -X POST "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/control" \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"action": "lock"}'
```

- **Description**: This command sends a `lock` action to the Raspberry Pi, instructing it to lock the door.
- **Response**: JSON confirming the command was sent successfully, with a timestamp and additional details from the Raspberry Pi.

Example response:

```json
{
  "message": "Command 'lock' sent to Raspberry Pi successfully",
  "timestamp": "2025-04-09T06:08:09.696182",
  "result_from_pi": {
    // Additional details from the Raspberry Pi would be here
  }
}
```

### Unlock Window Example

To send an unlock command for the window to the Raspberry Pi, use the following `curl` command:

```bash
curl -X POST "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/control" \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"action": "unlock", "parameters": {"target": "window"}}'
```

- **Description**: This command sends an `unlock` action for the window to the Raspberry Pi, instructing it to unlock the window.
- **Response**: JSON confirming the command was sent successfully, with a timestamp and additional details from the Raspberry Pi.

Example response:

```json
{
  "message": "Command 'unlock' sent to Raspberry Pi successfully",
  "timestamp": "2025-04-09T06:10:08.250239",
  "result_from_pi": {
    "door_locked": false,
    "status": "success"
  }
}
```

### Capture Image Endpoint Example

To capture an image using the Raspberry Pi, use the following `curl` command:

```bash
curl -X POST "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/control" \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"action": "capture_image"}'
```

- **Description**: This command sends a `capture_image` action to the Raspberry Pi, instructing it to capture an image.
- **Response**: JSON confirming the command was sent successfully, with a timestamp and the path to the captured image.

Example response:

```json
{
  "message": "Command 'capture_image' sent to Raspberry Pi successfully",
  "timestamp": "2025-04-09T06:26:08.830231",
  "result_from_pi": {
    "image_path": "/home/admin/iot_project_server_room_security/media/images/image_17441691"
  }
}
```

### Logs Endpoint Example

To retrieve the 10 most recent log entries, use the following `curl` command:

```bash
curl -X GET "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/logs?limit=10" \
     -H "Authorization: Bearer <access_token>"
```

- **Description**: This command retrieves the 10 most recent log entries from the server.
- **Response**: JSON with log entries, including event type, timestamp, details, and severity.

Example response:

```json
{
  "logs": [
    {"event_type": "unauthorized_access", "timestamp": "2025-04-07T00:40:04.805111", "details": {"message": "Unauthorized RFID access attempt", "sensor_data": {"card_uid": "170-232-119-190-130"}, "media_url": null}, "user_id": null, "video_url": null, "severity": "info", "source": "raspberry_pi", "id": 1, "role": null},
    {"event_type": "window_opened", "timestamp": "2025-04-07T00:40:06.742104", "details": {"message": "Window opened in server room", "sensor_data": {"location": "window", "image_url": null, "video_url": null}, "media_url": null}, "user_id": null, "video_url": null, "severity": "info", "source": "raspberry_pi", "id": 2, "role": null},
    {"event_type": "window_opened", "timestamp": "2025-04-07T00:40:36.775604", "details": {"message": "Window opened in server room", "sensor_data": {"location": "window", "image_url": null, "video_url": null}, "media_url": null}, "user_id": null, "video_url": null, "severity": "info", "source": "raspberry_pi", "id": 3, "role": null},
    {"event_type": "door_opened", "timestamp": "2025-04-07T00:40:37.766234", "details": {"message": "Door opened in server room", "sensor_data": {"location": "door", "image_url": null, "video_url": null}, "media_url": null}, "user_id": null, "video_url": null, "severity": "info", "source": "raspberry_pi", "id": 4, "role": null},
    {"event_type": "motion_detected", "timestamp": "2025-04-07T00:41:09.783392", "details": {"message": "Motion detected in server room", "sensor_data": {"location": "motion", "image_url": null, "video_url": null}, "media_url": null}, "user_id": null, "video_url": null, "severity": "info", "source": "raspberry_pi", "id": 5, "role": null},
    {"event_type": "window_opened", "timestamp": "2025-04-07T00:41:11.377247", "details": {"message": "Window opened in server room", "sensor_data": {"location": "window", "image_url": null, "video_url": null}, "media_url": null}, "user_id": null, "video_url": null, "severity": "info", "source": "raspberry_pi", "id": 6, "role": null},
    {"event_type": "unauthorized_access", "timestamp": "2025-04-07T00:41:42.106579", "details": {"message": "Unauthorized RFID access attempt", "sensor_data": {"card_uid": "4-181-34-95-233"}, "media_url": null}, "user_id": null, "video_url": null, "severity": "info", "source": "raspberry_pi", "id": 7, "role": null},
    {"event_type": "window_opened", "timestamp": "2025-04-07T00:48:04.379102", "details": {"message": "Window opened in server room", "sensor_data": {"location": "window", "image_url": null, "video_url": null}, "media_url": null}, "user_id": null, "video_url": null, "severity": "critical", "source": "raspberry_pi", "id": 8, "role": null},
    {"event_type": "door_opened", "timestamp": "2025-04-07T00:48:07.326017", "details": {"message": "Door opened in server room", "sensor_data": {"location": "door", "image_url": null, "video_url": null}, "media_url": null}, "user_id": null, "video_url": null, "severity": "critical", "source": "raspberry_pi", "id": 9, "role": null},
    {"event_type": "motion_detected", "timestamp": "2025-04-07T00:48:46.357181", "details": {"message": "Motion detected in server room", "sensor_data": {"location": "motion", "image_url": null, "video_url": null}, "media_url": null}, "user_id": null, "video_url": null, "severity": "critical", "source": "raspberry_pi", "id": 10, "role": null}
  ]
}
```

### Sensors Endpoint Example

To retrieve data for the 'door' sensor, use the following `curl` command:

```bash
curl -X GET "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/sensors/door" \
     -H "Authorization: Bearer <access_token>"
```

- **Description**: This command retrieves data for the 'door' sensor from the Raspberry Pi.
- **Response**: JSON with sensor data, including status, location, and activity.

Example response:

```json
{
  "data": {"open": false},
  "error": null,
  "event_count": 0,
  "firmware_version": null,
  "is_active": true,
  "last_check": "2025-04-09T06:22:55.720263",
  "last_event_timestamp": null,
  "location": "pin_17",
  "name": "door",
  "type": "door"
}
```

### Window Sensor Endpoint Example

To retrieve data for the 'window' sensor, use the following `curl` command:

```bash
curl -X GET "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/sensors/window" \
     -H "Authorization: Bearer <access_token>"
```

- **Description**: This command retrieves data for the 'window' sensor from the Raspberry Pi.
- **Response**: JSON with sensor data, including status, location, and activity.

Example response:

```json
{
  "data": {"open": false},
  "error": null,
  "event_count": 0,
  "firmware_version": null,
  "is_active": true,
  "last_check": "2025-04-09T06:24:42.771138",
  "last_event_timestamp": null,
  "location": "pin_27",
  "name": "window",
  "type": "window"
}
```

### Record Video Endpoint Example

To record a video using the Raspberry Pi, use the following `curl` command:

```bash
curl -X POST "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/control" \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"action": "record_video", "parameters": {"duration": 10}}'
```

- **Description**: This command sends a `record_video` action to the Raspberry Pi, instructing it to record a video for the specified duration.
- **Response**: JSON confirming the command was sent successfully, with a timestamp, duration, and the path to the recorded video.

Example response:

```json
{
  "message": "Command 'record_video' sent to Raspberry Pi successfully",
  "timestamp": "2025-04-09T06:27:49.630492",
  "result_from_pi": {
    "duration": 10,
    "status": "success",
    "video_path": "/home/admin/iot_project_server_room_security/media/videos/video_1744169269.h264",
    "video_url": null
  }
}
```

### Add User Endpoint Example

To add a new user, use the following `curl` command (requires admin privileges):

```bash
curl -X POST "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/users" \
     -H "Authorization: Bearer <admin_access_token>" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "password": "user123", "email": "user1@example.com", "is_admin": false}'
```

- **Description**: This command creates a new user with the specified credentials. The `is_admin` field determines if the new user has administrative privileges.
- **Response**: JSON confirming the user was created successfully, including the new user's ID and username.

Example response:

```json
{
  "message": "User created successfully",
  "user_id": 2,
  "username": "user1"
}
```

### Alert Endpoint Example

To send an alert, use the following `curl` command:

```bash
curl -X POST "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/alert" \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"message": "Test alert message", "video_url": "http://example.com/video.mp4"}'
```

- **Description**: This command sends an alert with a message and an optional video URL.
- **Response**: JSON confirming the alert was processed successfully, including the log ID and timestamp.

Example response:

```json
{
  "message": "Alert processed successfully",
  "log_id": 91,
  "timestamp": "2025-04-09T07:11:15.836352"
}
```

### Test Sensors Endpoint Example

To test the sensors, use the following `curl` command:

```bash
curl -X POST "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/control" \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{"action": "test_sensors"}'
```

- **Description**: This command sends a `test_sensors` action to the Raspberry Pi to verify sensor functionality.
- **Response**: JSON confirming the command was sent successfully, including the results of each sensor test.

Example response:

```json
{
  "message": "Command 'test_sensors' sent to Raspberry Pi successfully",
  "timestamp": "2025-04-09T07:13:37.285211",
  "result_from_pi": {
    "message": "Sensor test completed",
    "results": {
      "camera": {
        "details": "Camera inactive",
        "status": "error"
      },
      "door": {
        "details": "Current state: closed",
        "status": "ok"
      },
      "door_lock": {
        "details": "Test not fully implemented (check logs for state)",
        "status": "info"
      },
      "motion": {
        "details": "Current state: False",
        "status": "ok"
      },
      "rfid": {
        "details": "RFIDReader.read_card() got an unexpected keyword argument 'timeout'",
        "status": "error"
      },
      "window": {
        "details": "Current state: closed",
        "status": "ok"
      }
    },
    "status": "success",
    "summary": "One or more tests failed"
  }
}
```

### Health Check Endpoint Example

To check the health status of the server, use the following `curl` command:

```bash
curl -X GET "https://bf5a-196-207-133-221.ngrok-free.app/health" \
     -H "Authorization: Bearer <access_token>"
```

- **Description**: This command retrieves the health status of the server, including database connectivity and version information.
- **Response**: JSON with the health status, database connection status, and server version.

Example response:

```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

### Door Sensor Events Endpoint Example

To retrieve events from the door sensor, use the following `curl` command:

```bash
curl -X GET "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/sensors/door/events" \
     -H "Authorization: Bearer <access_token>"
```

- **Description**: This command retrieves events recorded by the door sensor.
- **Response**: JSON array of events. An empty array indicates no events recorded.

Example response:

```json
[]
```

### Door Sensor Stats Endpoint Example

To retrieve statistics for the door sensor, use the following `curl` command:

```bash
curl -X GET "https://bf5a-196-207-133-221.ngrok-free.app/api/v1/sensors/door/stats" \
     -H "Authorization: Bearer <access_token>"
```

- **Description**: This command retrieves statistics for the door sensor, including the total number of events in the last 24 hours and the time of the last event.
- **Response**: JSON with sensor statistics.

Example response:

```json
{
  "sensor_type": "door",
  "total_events_last_24h": 0,
  "last_event_time": null
}
```

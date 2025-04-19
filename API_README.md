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
curl -X POST "<YOUR_SERVER_URL>/api/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=<YOUR_USERNAME>&password=<YOUR_PASSWORD>"
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
curl -X GET "<YOUR_SERVER_URL>/api/v1/status" \
  -H "Authorization: Bearer <access_token>"
```

- **Description**: This command retrieves the current status of the server room, including sensor and system health metrics.
- **Response**: JSON with detailed status information, including sensor activity, storage usage, and Raspberry Pi connectivity.

Example response:

```json
{
  "status": "degraded",
  "sensors": {
    "camera": {"name": "camera", "is_active": false, "last_check": "<TIMESTAMP>", "error": null, "data": null, "location": "main_camera", "type": "camera", "firmware_version": null, "last_event": null, "event_count": 0},
    "door": {"name": "door", "is_active": true, "last_check": "<TIMESTAMP>", "error": null, "data": {"open": false}, "location": "pin_17", "type": "door", "firmware_version": null, "last_event": null, "event_count": 0},
    "motion": {"name": "motion", "is_active": true, "last_check": "<TIMESTAMP>", "error": null, "data": {"detected": false}, "location": "pin_4", "type": "motion", "firmware_version": null, "last_event": null, "event_count": 0}
  },
  "storage": {"total_gb": 28, "used_gb": 9, "free_gb": 17, "low_space": false},
  "uptime": "0:28:15",
  "errors": ["camera sensor is inactive"],
  "raspberry_pi": {"is_online": true, "last_heartbeat": "<TIMESTAMP>", "firmware_version": "unknown"}
}
```

### Control Endpoint Example

To send a control command to the Raspberry Pi, use the following `curl` command:

```bash
curl -X POST "<YOUR_SERVER_URL>/api/v1/control" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"action": "lock_door"}'
```

- **Description**: This command sends a `lock_door` action to the Raspberry Pi, instructing it to lock the door.
- **Response**: JSON confirming the command was sent successfully, with a timestamp and additional details from the Raspberry Pi.

Example response:

```json
{
  "message": "Command 'lock_door' sent to Raspberry Pi successfully",
  "timestamp": "<TIMESTAMP>",
  "result_from_pi": {}
}
```

### Logs Endpoint Example

To retrieve the 10 most recent log entries, use the following `curl` command:

```bash
curl -X GET "<YOUR_SERVER_URL>/api/v1/logs?limit=10" \
  -H "Authorization: Bearer <access_token>"
```

- **Description**: This command retrieves the 10 most recent log entries from the server.
- **Response**: JSON with log entries, including event type, timestamp, details, and severity.

Example response:

```json
{
  "logs": [
    {"event_type": "unauthorized_access", "timestamp": "<TIMESTAMP>", "details": {"message": "Unauthorized RFID access attempt"}, "severity": "info"},
    {"event_type": "window_opened", "timestamp": "<TIMESTAMP>", "details": {"message": "Window opened in server room"}, "severity": "info"}
  ]
}
```

### Sensors Endpoint Example

To retrieve data for the 'door' sensor, use the following `curl` command:

```bash
curl -X GET "<YOUR_SERVER_URL>/api/v1/sensors/door" \
  -H "Authorization: Bearer <access_token>"
```

- **Description**: This command retrieves data for the 'door' sensor from the Raspberry Pi.
- **Response**: JSON with sensor data, including status, location, and activity.

Example response:

```json
{
  "data": {"open": false},
  "is_active": true,
  "last_check": "<TIMESTAMP>",
  "location": "pin_17",
  "name": "door",
  "type": "door"
}
```

### Add User Endpoint Example

To add a new user, use the following `curl` command (requires admin privileges):

```bash
curl -X POST "<YOUR_SERVER_URL>/api/v1/users" \
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
curl -X POST "<YOUR_SERVER_URL>/api/v1/alert" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test alert message", "video_url": "<VIDEO_URL>"}'
```

- **Description**: This command sends an alert with a message and an optional video URL.
- **Response**: JSON confirming the alert was processed successfully, including the log ID and timestamp.

Example response:

```json
{
  "message": "Alert processed successfully",
  "log_id": 91,
  "timestamp": "<TIMESTAMP>"
}
```


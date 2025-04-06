#!/bin/bash

# Define project base directory (optional, but helps keep paths clean)
PROJECT_DIR="/home/admin/iot_project_server_room_security"
# Define module paths for python -m
RASPBERRY_PI_MODULE="iot_based_server_room_monitoring_control.firmware.raspberrypi.src.main"
SERVER_MODULE="iot_based_server_room_monitoring_control.server.app.main"
PYTHON_PATH="/home/admin/iot_project_server_room_security/venv/bin/python3"
LOG_DIR="$PROJECT_DIR/logs"

# Ensure the log directory exists
mkdir -p "$LOG_DIR"

# Kill existing processes to prevent 'Address already in use' errors
echo "Attempting to stop existing processes..."
pkill -f "$PYTHON_PATH -m $RASPBERRY_PI_MODULE" || true
pkill -f "$PYTHON_PATH -m $SERVER_MODULE" || true
lsof -t -i:8000 | xargs kill -9 2>/dev/null || true
lsof -t -i:5000 | xargs kill -9 2>/dev/null || true
lsof -t -i:6379 | xargs kill -9 2>/dev/null || true
sleep 5

echo "Starting Raspberry Pi firmware..."

(cd "$PROJECT_DIR" && $PYTHON_PATH -m "$RASPBERRY_PI_MODULE" >> "$LOG_DIR/raspberrypi.log" 2>&1) &
RASPBERRY_PI_PID=$!
echo "Raspberry Pi firmware started with PID $RASPBERRY_PI_PID. Logging to $LOG_DIR/raspberrypi.log"

echo "Starting Server application..."

(cd "$PROJECT_DIR" && $PYTHON_PATH -m "$SERVER_MODULE" >> "$LOG_DIR/server.log" 2>&1) &
SERVER_PID=$!
echo "Server application started with PID $SERVER_PID. Logging to $LOG_DIR/server.log"

echo "Both applications started in the background."

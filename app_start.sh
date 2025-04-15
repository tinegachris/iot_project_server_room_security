#!/bin/bash

# Define project base directory (optional, but helps keep paths clean)
PROJECT_DIR=$(pwd)
# Define module paths for python -m
RASPBERRY_PI_MODULE="iot_based_server_room_monitoring_control.firmware.raspberrypi.src.main"
SERVER_MODULE="iot_based_server_room_monitoring_control.server.app.main"
# Check if .venv path exists, otherwise use venv
if [ -f "$PROJECT_DIR/.venv/bin/python3" ]; then
    PYTHON_PATH="$PROJECT_DIR/.venv/bin/python3"
else
    PYTHON_PATH="$PROJECT_DIR/venv/bin/python3"
fi
LOG_DIR="$PROJECT_DIR/logs"

# Ensure the log directory exists
mkdir -p "$LOG_DIR"

# Kill existing processes to prevent 'Address already in use' errors
echo "Attempting to stop existing processes..."
pkill -f "$PYTHON_PATH -m $RASPBERRY_PI_MODULE" || true
pkill -f "$PYTHON_PATH -m $SERVER_MODULE" || true
pkill -f "ngrok" || true
echo "Existing processes stopped."

# Wait for a moment to ensure processes are terminated
sleep 5

echo "Starting Raspberry Pi firmware..."

# Run Pi firmware with sudo for GPIO access via lgpio
(cd "$PROJECT_DIR" && sudo $PYTHON_PATH -m "$RASPBERRY_PI_MODULE" >> "$LOG_DIR/raspberrypi.log" 2>&1) &
RASPBERRY_PI_PID=$!
echo "Raspberry Pi firmware started with PID $RASPBERRY_PI_PID. Logging to $LOG_DIR/raspberrypi.log"

echo "Starting Server application..."

# Server likely doesn't need sudo
(cd "$PROJECT_DIR" && $PYTHON_PATH -m "$SERVER_MODULE" >> "$LOG_DIR/server.log" 2>&1) &
SERVER_PID=$!
echo "Server application started with PID $SERVER_PID. Logging to $LOG_DIR/server.log"

echo "Starting ngrok tunnel..."
# Start ngrok tunnel for both server and Raspberry Pi

ngrok start --all --config "/home/admin/.config/ngrok/ngrok.yml" --log-format json --log "$LOG_DIR/ngrok.log" > /dev/null 2>&1 &
NGROK_PID=$!
echo "Ngrok tunnel started with PID $NGROK_PID. Logging to $LOG_DIR/ngrok.log"

echo "Script execution completed. Processes are running in the background."

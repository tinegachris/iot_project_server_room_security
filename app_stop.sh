#!/bin/bash

# Script to stop all running processes and apps

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

# Kill existing processes to prevent 'Address already in use' errors
echo "Attempting to stop existing processes..."
pkill -f "$PYTHON_PATH -m $RASPBERRY_PI_MODULE" || true
pkill -f "$PYTHON_PATH -m $SERVER_MODULE" || true
pkill -f "ngrok" || true
sleep 5

echo "All processes stopped."
#!/bin/bash

# Script to stop all running processes and apps

echo "Attempting to stop existing processes..."
pkill -f "$PYTHON_PATH -m $RASPBERRY_PI_MODULE" || true
pkill -f "$PYTHON_PATH -m $SERVER_MODULE" || true
lsof -t -i:8000 | xargs kill -9 2>/dev/null || true
sleep 2

echo "APP STOPPED"
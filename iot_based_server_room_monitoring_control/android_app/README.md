# Server Room Security Android App

A Flutter-based Android application for monitoring and controlling server room security systems.

## Prerequisites

- Flutter SDK (latest version)
- Android Studio or VS Code with Flutter extensions
- Android emulator or physical device
- Python 3.8+ (for running the server)
- Git

## Setup Instructions

1. **Clone the Repository**
```bash
git clone <repository-url>
cd iot_based_server_room_monitoring_control
```

2. **Set Up the Server**
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install server dependencies
cd server
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Set Up the Android App**
```bash
# Navigate to Android app directory
cd ../android_app

# Install Flutter dependencies
flutter pub get

# Run Flutter doctor to verify setup
flutter doctor
```

## Testing the App

### 1. Local Development Testing

1. **Start the Server**
```bash
# From the server directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Configure the Android App**
- Open the app in Android Studio/VS Code
- Update the base URL in `lib/services/api_service.dart`:
  ```dart
  static const String _defaultBaseUrl = 'http://10.0.2.2:8000/api';  // For Android emulator
  // or
  static const String _defaultBaseUrl = 'http://<your-local-ip>:8000/api';  // For physical device
  ```

3. **Run the App**
```bash
# Start an Android emulator or connect a physical device
flutter run
```

### 2. Testing Different Scenarios

1. **System Status Monitoring**
- Launch the app and navigate to the Dashboard
- Verify that system status is displayed correctly
- Check sensor status updates
- Monitor storage usage information

2. **Sensor Testing**
- Test each sensor type (motion, door, window, RFID)
- Verify real-time updates
- Check sensor event history

3. **Camera Operations**
- Test image capture
- Test video recording
- Verify media storage and retrieval

4. **Alert System**
- Create test alerts
- Verify alert notifications
- Check alert history

5. **User Authentication**
- Test login functionality
- Verify role-based access control
- Test session management

### 3. Debugging Tips

1. **Network Debugging**
```bash
# Enable network logging
flutter run --verbose
```

2. **API Testing**
- Use Postman or similar tool to test API endpoints
- Verify response formats match app expectations
- Test error scenarios

3. **State Management**
- Monitor app state changes using Flutter DevTools
- Check provider updates
- Verify data persistence

### 4. Common Issues and Solutions

1. **Connection Issues**
- Verify server is running and accessible
- Check base URL configuration
- Ensure proper network permissions in AndroidManifest.xml

2. **Authentication Problems**
- Verify token storage
- Check token refresh mechanism
- Test session timeout handling

3. **Data Synchronization**
- Monitor real-time updates
- Check offline data handling
- Verify data persistence

## Testing Checklist

- [ ] Server connection established
- [ ] Authentication working
- [ ] Real-time updates functioning
- [ ] Sensor data accurate
- [ ] Camera operations working
- [ ] Alert system functioning
- [ ] User roles properly enforced
- [ ] Data persistence working
- [ ] Error handling appropriate
- [ ] UI responsive and accurate

## Additional Resources

- [Flutter Documentation](https://flutter.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Android Studio Documentation](https://developer.android.com/studio)
- [VS Code Flutter Extension](https://marketplace.visualstudio.com/items?itemName=Dart-Code.flutter)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

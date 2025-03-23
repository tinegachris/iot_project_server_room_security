import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class MonitoringService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _notifications = FlutterLocalNotificationsPlugin();
  String? _serverUrl;

  Future<void> initialize() async {
    // Initialize Firebase Messaging
    await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    // Get FCM token
    String? token = await _messaging.getToken();
    print('FCM Token: $token');

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // Handle background messages
    FirebaseMessaging.onBackgroundMessage(_handleBackgroundMessage);

    // Load server URL from shared preferences or configuration
    _serverUrl = 'YOUR_SERVER_URL'; // Replace with your actual server URL
  }

  Future<Map<String, dynamic>> getMonitoringData() async {
    try {
      final response = await http.get(Uri.parse('$_serverUrl/monitoring-data'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to load monitoring data');
      }
    } catch (e) {
      print('Error fetching monitoring data: $e');
      return {};
    }
  }

  Future<void> _handleForegroundMessage(RemoteMessage message) async {
    print('Handling foreground message: ${message.messageId}');
    await _showNotification(
      title: message.notification?.title ?? 'New Alert',
      body: message.notification?.body ?? 'Check the monitoring dashboard',
    );
  }

  Future<void> _showNotification({
    required String title,
    required String body,
  }) async {
    const AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
      'monitoring_channel',
      'Monitoring Notifications',
      channelDescription: 'Notifications for server room monitoring alerts',
      importance: Importance.high,
      priority: Priority.high,
    );

    const NotificationDetails platformDetails = NotificationDetails(
      android: androidDetails,
    );

    await _notifications.show(
      0,
      title,
      body,
      platformDetails,
    );
  }
}

Future<void> _handleBackgroundMessage(RemoteMessage message) async {
  print('Handling background message: ${message.messageId}');
}
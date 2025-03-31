import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/system_status.dart';
import '../models/log_entry.dart';
import '../models/alert.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api';
  String? _authToken;

  void setAuthToken(String token) {
    _authToken = token;
  }

  Map<String, String> get _headers {
    final headers = {'Content-Type': 'application/json'};
    if (_authToken != null) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    return headers;
  }

  Future<SystemStatus> getSystemStatus() async {
    final response = await http.get(
      Uri.parse('$baseUrl/status'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return SystemStatus.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to get system status');
    }
  }

  Future<List<LogEntry>> getLogs({
    int skip = 0,
    int limit = 100,
    String? eventType,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    final queryParams = {
      'skip': skip.toString(),
      'limit': limit.toString(),
      if (eventType != null) 'event_type': eventType,
      if (startDate != null) 'start_date': startDate.toIso8601String(),
      if (endDate != null) 'end_date': endDate.toIso8601String(),
    };

    final response = await http.get(
      Uri.parse('$baseUrl/logs').replace(queryParameters: queryParams),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((json) => LogEntry.fromJson(json)).toList();
    } else {
      throw Exception('Failed to get logs');
    }
  }

  Future<Map<String, dynamic>> getSensorData(String sensorType) async {
    final response = await http.get(
      Uri.parse('$baseUrl/sensors/$sensorType'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to get sensor data');
    }
  }

  Future<List<Map<String, dynamic>>> getSensorEvents(
    String sensorType, {
    int limit = 100,
  }) async {
    final response = await http.get(
      Uri.parse('$baseUrl/sensors/$sensorType/events?limit=$limit'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.cast<Map<String, dynamic>>();
    } else {
      throw Exception('Failed to get sensor events');
    }
  }

  Future<Map<String, dynamic>> getSensorStats(String sensorType) async {
    final response = await http.get(
      Uri.parse('$baseUrl/sensors/$sensorType/stats'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to get sensor stats');
    }
  }

  Future<Map<String, dynamic>> getCameraStatus() async {
    final response = await http.get(
      Uri.parse('$baseUrl/camera/status'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to get camera status');
    }
  }

  Future<Map<String, dynamic>> captureImage() async {
    final response = await http.post(
      Uri.parse('$baseUrl/camera/capture'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to capture image');
    }
  }

  Future<Map<String, dynamic>> recordVideo({int duration = 30}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/camera/record'),
      headers: _headers,
      body: json.encode({'duration': duration}),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to record video');
    }
  }

  Future<Map<String, dynamic>> executeCommand(
    String action, {
    Map<String, dynamic>? parameters,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/control'),
      headers: _headers,
      body: json.encode({
        'action': action,
        if (parameters != null) 'parameters': parameters,
      }),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to execute command');
    }
  }

  Future<Map<String, dynamic>> getRfidStatus() async {
    final response = await http.get(
      Uri.parse('$baseUrl/rfid/status'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to get RFID status');
    }
  }

  Future<Map<String, dynamic>> createAlert(Alert alert) async {
    final response = await http.post(
      Uri.parse('$baseUrl/alerts'),
      headers: _headers,
      body: json.encode(alert.toJson()),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to create alert');
    }
  }
}
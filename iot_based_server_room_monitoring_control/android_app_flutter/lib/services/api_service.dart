import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/log_entry.dart';
import '../models/system_status.dart';

class ApiService {
  static const String baseUrl = 'http://your-server-url:8000/api';
  String? _authToken;

  void setAuthToken(String token) {
    _authToken = token;
  }

  Map<String, String> get _headers {
    return {
      'Content-Type': 'application/json',
      if (_authToken != null) 'Authorization': 'Bearer $_authToken',
    };
  }

  Future<SystemStatus> getSystemStatus() async {
    final response = await http.get(
      Uri.parse('$baseUrl/status'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return SystemStatus.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to load system status');
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

    final uri = Uri.parse('$baseUrl/logs').replace(queryParameters: queryParams);
    final response = await http.get(uri, headers: _headers);

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['logs'] as List)
          .map((log) => LogEntry.fromJson(log))
          .toList();
    } else {
      throw Exception('Failed to load logs');
    }
  }

  Future<void> postAlert({
    required String message,
    String? videoUrl,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/alert'),
      headers: _headers,
      body: json.encode({
        'message': message,
        if (videoUrl != null) 'video_url': videoUrl,
      }),
    );

    if (response.statusCode != 201) {
      throw Exception('Failed to post alert');
    }
  }

  Future<Map<String, dynamic>> postControlCommand(String action) async {
    final response = await http.post(
      Uri.parse('$baseUrl/control'),
      headers: _headers,
      body: json.encode({'action': action}),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to execute control command');
    }
  }
} 
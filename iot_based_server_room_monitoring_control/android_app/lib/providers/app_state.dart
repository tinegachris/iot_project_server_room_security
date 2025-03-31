import 'package:flutter/foundation.dart';
import '../models/log_entry.dart';
import '../models/system_status.dart';
import '../models/alert.dart';
import '../services/api_service.dart';

class AppState extends ChangeNotifier {
  late final ApiService _apiService;
  SystemStatus? _systemStatus;
  List<LogEntry> _logs = [];
  List<Alert> _alerts = [];
  bool _isLoading = false;
  String? _error;
  String? _baseUrl;

  AppState({String? baseUrl}) {
    _baseUrl = baseUrl;
    _apiService = ApiService(baseUrl: baseUrl);
  }

  SystemStatus? get systemStatus => _systemStatus;
  List<LogEntry> get logs => _logs;
  List<Alert> get alerts => _alerts;
  bool get isLoading => _isLoading;
  String? get error => _error;
  String? get baseUrl => _baseUrl;

  void setBaseUrl(String url) {
    _baseUrl = url;
    _apiService.setBaseUrl(url);
  }

  void setAuthToken(String token) {
    _apiService.setAuthToken(token);
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  Future<void> fetchSystemStatus() async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      _systemStatus = await _apiService.getSystemStatus();
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchLogs({
    int skip = 0,
    int limit = 100,
    String? eventType,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      _logs = await _apiService.getLogs(
        skip: skip,
        limit: limit,
        eventType: eventType,
        startDate: startDate,
        endDate: endDate,
      );
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<Map<String, dynamic>> getSensorData(String sensorType) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final data = await _apiService.getSensorData(sensorType);
      _isLoading = false;
      notifyListeners();
      return data;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> getSensorEvents(
    String sensorType, {
    int limit = 100,
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final events = await _apiService.getSensorEvents(sensorType, limit: limit);
      _isLoading = false;
      notifyListeners();
      return events;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getSensorStats(String sensorType) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final stats = await _apiService.getSensorStats(sensorType);
      _isLoading = false;
      notifyListeners();
      return stats;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getCameraStatus() async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final status = await _apiService.getCameraStatus();
      _isLoading = false;
      notifyListeners();
      return status;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<Map<String, dynamic>> captureImage() async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final result = await _apiService.captureImage();
      _isLoading = false;
      notifyListeners();
      return result;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<Map<String, dynamic>> recordVideo({int duration = 30}) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final result = await _apiService.recordVideo(duration: duration);
      _isLoading = false;
      notifyListeners();
      return result;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<Map<String, dynamic>> executeCommand(
    String action, {
    Map<String, dynamic>? parameters,
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final result = await _apiService.executeCommand(action, parameters: parameters);
      _isLoading = false;
      notifyListeners();
      return result;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getRfidStatus() async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final status = await _apiService.getRfidStatus();
      _isLoading = false;
      notifyListeners();
      return status;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }

  Future<Map<String, dynamic>> createAlert(Alert alert) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final result = await _apiService.createAlert(alert);
      _alerts.add(alert);
      _isLoading = false;
      notifyListeners();
      return result;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      rethrow;
    }
  }
}
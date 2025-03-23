import 'package:flutter/foundation.dart';
import '../models/log_entry.dart';
import '../models/system_status.dart';
import '../services/api_service.dart';

class AppState extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  SystemStatus? _systemStatus;
  List<LogEntry> _logs = [];
  bool _isLoading = false;
  String? _error;

  SystemStatus? get systemStatus => _systemStatus;
  List<LogEntry> get logs => _logs;
  bool get isLoading => _isLoading;
  String? get error => _error;

  void setAuthToken(String token) {
    _apiService.setAuthToken(token);
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

  Future<void> postAlert({
    required String message,
    String? videoUrl,
  }) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      await _apiService.postAlert(
        message: message,
        videoUrl: videoUrl,
      );
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> executeControlCommand(String action) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      await _apiService.postControlCommand(action);
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
    }
  }
} 
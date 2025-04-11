import 'dart:async'; // For Timer
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart'; // Import secure storage
import '../models/log_entry.dart'; // Import LogEntry
import '../models/app_user.dart'; // Import User
import '../models/system_status.dart'; // Import SystemStatus models
import '../services/api_service.dart'; // Import ApiService
import 'package:flutter/foundation.dart';
import 'package:logging/logging.dart';

class AppState with ChangeNotifier {
  final ApiService _apiService = ApiService(); // Instantiate ApiService
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage(); // Instantiate secure storage
  static const String _tokenKey = 'auth_token'; // Key for storing token
  static const String _userKey = 'auth_user'; // Key for storing user info
  static final Logger _logger = Logger('AppState');

  // --- Authentication State ---
  bool _isInitializing = true; // Flag for initial auto-login check
  bool _isAuthenticated = false;
  User? _currentUser;
  String? _loginError;
  bool _isLoggingIn = false;
  String? _registrationMessage; // For success/error feedback on registration
  bool _isRegistering = false;
  String? _fetchCurrentUserError;

  // --- System Status State ---
  SystemStatus? _currentStatus;
  String? _statusError;
  bool _isFetchingStatus = false;

  // --- Log State ---
  List<LogEntry> _logs = [];
  String? _logsError;
  bool _isFetchingLogs = false;

  // --- Control Command State ---
  String? _controlCommandError;
  bool _isExecutingControlCommand = false;
  String? _executingAction; // Track the specific action

  // --- Polling State ---
  Timer? _statusPollingTimer;
  int _consecutivePollingFailures = 0;
  bool _isPollingSuspended = false;

  // --- User Management State ---
  List<User> _managedUsers = [];
  bool _isLoadingUsers = false;
  final bool _isCreatingUser = false;
  final bool _isUpdatingUser = false;
  String? _userManagementError;
  List<String> _availableRoles = ['User']; // Default role

  // --- Getters ---
  // Authentication
  bool get isInitializing => _isInitializing;
  bool get isAuthenticated => _isAuthenticated;
  User? get currentUser => _currentUser;
  String? get loginError => _loginError;
  bool get isLoggingIn => _isLoggingIn;
  String? get registrationMessage => _registrationMessage;
  bool get isRegistering => _isRegistering;
  String? get fetchCurrentUserError => _fetchCurrentUserError;

  // System Status
  SystemStatus? get currentStatus => _currentStatus;
  String? get statusError => _statusError;
  bool get isFetchingStatus => _isFetchingStatus;

  // Logs
  List<LogEntry> get logs => _logs;
  String? get logsError => _logsError;
  bool get isFetchingLogs => _isFetchingLogs;

  // Controls
  String? get controlCommandError => _controlCommandError;
  bool get isExecutingControlCommand => _isExecutingControlCommand;
  String? get executingAction => _executingAction; // Getter for the action

  // Polling Status
  bool get isPollingSuspended => _isPollingSuspended;

  // User Management
  List<User> get managedUsers => _managedUsers;
  bool get isLoadingUsers => _isLoadingUsers;
  bool get isCreatingUser => _isCreatingUser;
  bool get isUpdatingUser => _isUpdatingUser;
  String? get userManagementError => _userManagementError;

  // Combined Loading State (can be used by UI elements needing a general loading state)
  bool get isBusy => _isLoggingIn || _isRegistering || _isFetchingStatus || _isFetchingLogs || _isExecutingControlCommand || _isLoadingUsers || _isInitializing;

  // Provide specific status parts via getters for easier consumption
  bool get doorLocked => _currentStatus?.sensors['door']?.data?['locked'] ?? false; // Example path
  String get overallSystemStatus => _currentStatus?.status ?? "unknown";
  List<String> get systemErrors => _currentStatus?.errors ?? []; // Example mapping

  // User Management
  List<String> get availableRoles => _availableRoles;

  // --- Authentication Methods ---

  // Try to log in automatically using stored token
  Future<void> tryAutoLogin() async {
    _isInitializing = true;
    notifyListeners();
    final storedToken = await _secureStorage.read(key: _tokenKey);
    final storedUserJson = await _secureStorage.read(key: _userKey);

    if (storedToken != null) {
      _logger.info("Found stored token, attempting auto-login...");
      try {
        final storedUserMap = json.decode(storedUserJson ?? '{}');
        _currentUser = User(
          id: 0,
          username: storedUserMap['username'] ?? 'unknown',
          role: 'unknown',
          token: storedToken,
        );
        _apiService.setAuthToken(storedToken);
        _isAuthenticated = true;

        // Must notify *before* async calls that depend on auth state
        notifyListeners();

        await fetchCurrentUser();
        await fetchInitialData();
        startPolling();
        _logger.info("Auto-login successful.");
      } catch (e) {
        _logger.warning("Auto-login failed: $e");
        await logout(); // Clears storage and state
      }
    } else {
      _logger.info("No stored token found for auto-login.");
    }
    _isInitializing = false;
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    _isLoggingIn = true;
    _loginError = null;
    notifyListeners();
    _logger.info("AppState: Attempting login with username: $username");
    try {
      final responseData = await _apiService.login(username, password);
      final token = responseData['access_token'] as String?;

      if (token != null) {
        _apiService.setAuthToken(token);
        await _secureStorage.write(key: _tokenKey, value: token);
        _currentUser = User(id: 0, username: username, role: 'unknown', token: token);
        await _secureStorage.write(key: _userKey, value: json.encode({'username': username}));
        _isAuthenticated = true;

        // Notify before async calls
        _isLoggingIn = false;
        notifyListeners();

        await fetchCurrentUser();
        await fetchInitialData();
        startPolling();
        return true;
      } else {
        throw ApiException('Login failed: Missing token in response');
      }
    } on ApiException catch (e) {
       _loginError = e.message; // Use specific message from exception
       _isAuthenticated = false;
       _currentUser = null;
       _apiService.setAuthToken(null);
       await _secureStorage.delete(key: _tokenKey);
       await _secureStorage.delete(key: _userKey);
       _isLoggingIn = false;
       notifyListeners();
       return false;
    } catch (e) {
      _loginError = 'Login failed: An unexpected error occurred.';
      _logger.severe("AppState login unexpected error: ${e.toString()}");
      _isAuthenticated = false;
      _currentUser = null;
      _apiService.setAuthToken(null);
      await _secureStorage.delete(key: _tokenKey);
      await _secureStorage.delete(key: _userKey);
      _isLoggingIn = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> fetchCurrentUser() async {
    if (!_isAuthenticated || _currentUser == null) return;
    _fetchCurrentUserError = null;
    // No separate loading flag for this, usually happens quickly after login/auto-login
    // notifyListeners();

    _logger.info("Fetching full current user details...");
    try {
      final userData = await _apiService.fetchUserMe();
      // Merge fetched data with existing token (if any)
      _currentUser = User.fromJson({
        ...userData, // Spread the fetched user data (id, name, email, role etc.)
        'token': _currentUser?.token, // Keep the existing token
      });
      // Save complete user data to storage
      await _secureStorage.write(key: _userKey, value: json.encode(_currentUser!.toJson()));
      _logger.info("Successfully fetched and updated current user: ${_currentUser?.username}");
    } on ApiException catch (e) {
      _fetchCurrentUserError = "Failed to fetch user details: ${e.message}";
      _logger.warning(_fetchCurrentUserError);
      // If fetching user fails (e.g., bad token), log out
      if (e.statusCode == 401 || e.statusCode == 403) {
        _logger.warning("Logging out due to error fetching current user.");
        await logout();
      }
    } catch (e) {
      _fetchCurrentUserError = "Failed to fetch user details: An unexpected error occurred.";
      _logger.severe("$_fetchCurrentUserError Error: $e");
      // Consider logout on unexpected errors too?
      // await logout();
    } finally {
      // Notify listeners regardless of success/failure to update UI (e.g., drawer header)
      notifyListeners();
    }
  }

  Future<void> logout() async {
    stopPolling();
    _currentUser = null;
    _isAuthenticated = false;
    _apiService.setAuthToken(null);
    _currentStatus = null;
    _logs = [];
    _statusError = null;
    _logsError = null;
    _loginError = null;
    _registrationMessage = null;
    _controlCommandError = null;
    _userManagementError = null;
    _fetchCurrentUserError = null;
    await _secureStorage.deleteAll(); // Clear all secure storage for this app
    _consecutivePollingFailures = 0; // Reset on logout
    _isPollingSuspended = false; // Reset on logout
    _logger.info("User logged out, storage cleared.");
    notifyListeners();
  }

  // Method to clear specific errors if needed by UI
  void clearLoginError() {
    if (_loginError != null) {
      _loginError = null;
      notifyListeners();
    }
  }
    void clearRegistrationMessage() {
    if (_registrationMessage != null) {
      _registrationMessage = null;
      notifyListeners();
    }
  }
  void clearControlCommandError() {
    if (_controlCommandError != null) {
      _controlCommandError = null;
      notifyListeners();
    }
  }
  void clearStatusError() {
    if (_statusError != null) {
      _statusError = null;
      notifyListeners();
    }
  }
  void clearLogsError() {
    if (_logsError != null) {
      _logsError = null;
      notifyListeners();
    }
  }
  void clearUserManagementError() {
    if (_userManagementError != null) {
      _userManagementError = null;
      notifyListeners();
    }
  }
  // ... add clear methods for other errors as needed ...

  // --- Data Fetching Methods ---
  Future<void> fetchInitialData() async {
    if (!_isAuthenticated) return;
    _logger.info("Fetching initial data (status and logs)...");
    // Reset errors before fetching
    _statusError = null;
    _logsError = null;
    // Indicate loading for both
    _isFetchingStatus = true;
    _isFetchingLogs = true;
    notifyListeners();

    try {
      // Fetch in parallel
      await Future.wait([
        fetchSystemStatus(notify: false), // Don't notify individually
        fetchLogs(notify: false),         // Don't notify individually
      ]);
    } catch (e) {
      // Errors are set within the individual fetch methods
      _logger.severe("Error during fetchInitialData: $e");
    } finally {
      _isFetchingStatus = false;
      _isFetchingLogs = false;
      notifyListeners(); // Notify once after both complete (or fail)
      _logger.info("Finished fetching initial data.");
    }
  }

  Future<void> fetchSystemStatus({bool notify = true}) async {
    if (!_isAuthenticated) return;
    _isFetchingStatus = true;
    _statusError = null;
    if (notify) notifyListeners();
    try {
      final statusData = await _apiService.fetchSystemStatus();
      _currentStatus = SystemStatus.fromJson(statusData);
    } on ApiException catch (e) {
      _statusError = e.message;
      _logger.warning("Error fetching system status: $_statusError");
      // Optionally clear status: _currentStatus = null;
      // Rethrow only if not part of fetchInitialData
      if (notify) rethrow;
    } catch (e) {
      _statusError = "An unexpected error occurred fetching status.";
      _logger.severe("Unexpected error fetching system status: $e");
      if (notify) rethrow;
    } finally {
      _isFetchingStatus = false;
      if (notify) notifyListeners();
    }
  }

  Future<void> fetchLogs({bool notify = true}) async {
    if (!_isAuthenticated) return;
    _isFetchingLogs = true;
    _logsError = null;
     if (notify) notifyListeners();
    try {
      final logListData = await _apiService.fetchLogs();
      _logs = logListData.map((logJson) => LogEntry.fromJson(logJson as Map<String, dynamic>)).toList();
    } on ApiException catch (e) {
      _logsError = e.message;
      _logger.warning("Error fetching logs: $_logsError");
       // Optionally clear logs: _logs = [];
      if (notify) rethrow;
    } catch (e) {
       _logsError = "An unexpected error occurred fetching logs.";
       _logger.severe("Unexpected error fetching logs: $e");
       if (notify) rethrow;
    } finally {
        _isFetchingLogs = false;
        if (notify) notifyListeners();
    }
  }

  // --- Control Methods ---
  Future<void> executeControlCommand(String piCommand, [Map<String, dynamic>? data]) async {
    if (!_isAuthenticated) return;

    _isExecutingControlCommand = true;
    _controlCommandError = null;
    _executingAction = piCommand; // Set the specific action
    notifyListeners();

    try {
      // Use the sendPiCommand which calls the server's /control endpoint
      await _apiService.sendPiCommand(piCommand, data);
      _logger.info('Control command "$piCommand" sent successfully via server.');
      // Command sent successfully, now refresh status to see effect
      await fetchSystemStatus(); // Refresh status after command
    } on ApiException catch(e) {
      _controlCommandError = 'Failed command "$piCommand": ${e.message}';
      _logger.warning(_controlCommandError);
       // Do NOT automatically clear the error here, let the UI show it
       rethrow; // Rethrow so the UI catch block can handle it (e.g., show SnackBar)
    } catch (e) {
      _controlCommandError = 'Failed command "$piCommand": An unexpected error occurred.';
      _logger.severe("$_controlCommandError Error: $e");
      rethrow;
    } finally {
      _isExecutingControlCommand = false;
      _executingAction = null; // Clear the specific action
      notifyListeners();
    }
  }

  // --- Polling for Real-time Updates ---
  void startPolling({Duration interval = const Duration(seconds: 15)}) {
    stopPolling();
    if (!_isAuthenticated) return;
    _consecutivePollingFailures = 0; // Reset counter on starting/restarting polling
    _isPollingSuspended = false; // Ensure polling is not suspended when starting
    _logger.info("Resetting polling failure count and suspension status.");

    _logger.info("Starting status polling (interval: ${interval.inSeconds} seconds)");
    _statusPollingTimer = Timer.periodic(interval, (timer) {
      _logger.fine("Polling tick...");
      _fetchStatusAndLogsSilently();
    });
     _fetchStatusAndLogsSilently(); // Fetch immediately on start
  }

  // Internal method to fetch data silently without setting global loading/error flags used by manual refresh
  Future<void> _fetchStatusAndLogsSilently() async {
    if (!_isAuthenticated || _statusPollingTimer == null) return;

    String? currentPollingStatusError;
    String? currentPollingLogsError;

    // --- Fetch Status ---
    bool statusFetchSuccess = false; // Track success for this cycle
    try {
      _logger.info("Polling: Attempting to fetch system status...");
      final statusData = await _apiService.fetchSystemStatus();
      if (_statusPollingTimer != null) {
        _currentStatus = SystemStatus.fromJson(statusData);
        _statusError = null; // Clear specific status error on success
        statusFetchSuccess = true;
        _logger.info("Polling: Successfully fetched status.");
      }
    } on ApiException catch (e) {
       _logger.warning("Polling Error fetching status: ${e.message}");
       currentPollingStatusError = e.message;
    } catch (e) {
       _logger.severe("Polling: Unexpected error fetching status: $e");
       currentPollingStatusError = "Unexpected status fetch error";
    }

    // --- Fetch Logs ---
    if (_statusPollingTimer == null) return; // Check again
    bool logsFetchSuccess = false; // Track success for this cycle

    try {
       _logger.info("Polling: Attempting to fetch logs...");
       final logListData = await _apiService.fetchLogs();
       if (_statusPollingTimer != null) {
         _logs = logListData.map((logJson) => LogEntry.fromJson(logJson as Map<String, dynamic>)).toList();
         _logsError = null; // Clear specific logs error on success
         logsFetchSuccess = true;
         _logger.info("Polling: Successfully fetched logs, count: ${_logs.length}");
       }
    } on ApiException catch (e) {
       _logger.warning("Polling Error fetching logs: ${e.message}");
       currentPollingLogsError = e.message;
    } catch (e) {
       _logger.severe("Polling: Unexpected error fetching logs: $e");
       currentPollingLogsError = "Unexpected logs fetch error";
    }

    // --- Update State (only if polling is still active) ---
    if (_statusPollingTimer != null) {
       // Update specific errors based on this polling cycle
       _statusError = currentPollingStatusError; // Can be null if successful
       _logsError = currentPollingLogsError;   // Can be null if successful

       // Handle consecutive failures
       if (!statusFetchSuccess || !logsFetchSuccess) {
          _consecutivePollingFailures++;
          _logger.warning("Polling failure count: $_consecutivePollingFailures");
          if (_consecutivePollingFailures >= 5) { // Threshold for suspension
              _logger.warning("Suspending polling due to repeated errors.");
              _isPollingSuspended = true;
              stopPolling(); // Stop the timer
              // Keep _statusError and _logsError as they are
          }
       } else {
          _consecutivePollingFailures = 0; // Reset on a fully successful cycle
       }

       // Handle critical errors during polling
       final combinedError = [_statusError, _logsError].where((e) => e != null).join(" | ");
       if (combinedError.contains("Unauthorized") || combinedError.contains("Forbidden")) {
          _logger.warning("Authentication error detected during polling. Stopping polling.");
          stopPolling();
          // Consider triggering logout
          // Future.microtask(() => logout());
       } else if (combinedError.contains("Received HTML")) {
          _logger.warning("HTML received during polling, likely ngrok/tunnel issue. Keeping polling active but showing error.");
       }
       notifyListeners();
    }
  }

  void stopPolling() {
     if (_statusPollingTimer != null) {
        _logger.info("Stopping status polling timer.");
        _statusPollingTimer?.cancel();
        _statusPollingTimer = null;
        // Don't reset _isPollingSuspended here, only when manually starting
     }
   }

   @override
   void dispose() {
    stopPolling();
    super.dispose();
  }

  // --- Registration Method ---
  Future<bool> register({
    required String name,
    required String email,
    required String password,
    required String role,
  }) async {
    _isRegistering = true;
    _registrationMessage = null;
    notifyListeners();
    try {
      final response = await _apiService.register(name, email, password, role);
      _registrationMessage = response['message'] ?? "Registration Successful!";
      _isRegistering = false;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _registrationMessage = 'Registration failed: ${e.message}';
      _isRegistering = false;
      notifyListeners();
      return false;
    } catch (e) {
       _registrationMessage = 'Registration failed: An unexpected error occurred.';
       _isRegistering = false;
       notifyListeners();
       return false;
    }
  }

  // --- Manual Alert Method ---
  Future<void> postManualAlert(String message, {String? videoUrl}) async {
     // Reuse control command state for loading/error, or create specific ones?
     _isExecutingControlCommand = true;
     _controlCommandError = null;
     notifyListeners();
     try {
        final response = await _apiService.postManualAlert(message, videoUrl: videoUrl);
        _logger.info("Manual alert posted: ${response['message']}");
        // Optional: Show success temporarily using the control error field?
        // _controlCommandError = response['message'] ?? "Alert posted successfully";
        // await fetchLogs(); // Refresh logs after posting alert
     } on ApiException catch (e) {
        _controlCommandError = 'Failed to post manual alert: ${e.message}';
        rethrow; // Let UI handle showing the error
     } catch (e) {
        _controlCommandError = 'Failed to post manual alert: ${e.toString()}';
        rethrow;
     } finally {
        _isExecutingControlCommand = false;
        notifyListeners();
     }
  }

  // --- User Management Methods ---
  Future<void> fetchManagedUsers({bool forceRefresh = false}) async {
    if (_managedUsers.isNotEmpty && !forceRefresh && !_isLoadingUsers) return;

    _isLoadingUsers = true;
    _userManagementError = null;
    notifyListeners();
    try {
      final usersData = await _apiService.fetchUsers();
      _managedUsers = usersData.map((data) => User.fromJson(data as Map<String, dynamic>)).toList();
    } on ApiException catch(e) {
      _userManagementError = "Failed to fetch users: ${e.message}";
      _managedUsers = [];
    } catch (e) {
       _userManagementError = "Failed to fetch users: An unexpected error occurred.";
       _managedUsers = [];
    } finally {
      _isLoadingUsers = false;
      notifyListeners();
    }
  }

  Future<bool> createManagedUser({
     required String name,
     required String email,
     required String password,
     required String role,
  }) async {
      _isLoadingUsers = true;
      _userManagementError = null;
      notifyListeners();
      try {
         // Derive isAdmin flag from role string
         bool isAdmin = role.toLowerCase() == 'admin';
         await _apiService.createUser(name, email, password, isAdmin);
         await fetchManagedUsers(forceRefresh: true);
         return true;
      } on ApiException catch (e) {
         _userManagementError = "Failed to create user: ${e.message}";
         _isLoadingUsers = false;
         notifyListeners();
         return false;
      } catch (e) {
         _userManagementError = "Failed to create user: An unexpected error occurred.";
         _isLoadingUsers = false;
         notifyListeners();
         return false;
      }
  }

  // Placeholder for update logic - commented out as ApiService method is commented out
  // Future<bool> updateManagedUser({ ... }) async { ... }
  Future<bool> updateManagedUser({
    required int id,
    String? name,
    String? email,
    String? role,
    // Add password update later if needed
  }) async {
    _isLoadingUsers = true;
    _userManagementError = null;
    notifyListeners();

    try {
      // Call the ApiService method
      await _apiService.updateUser(
        id,
        name: name,
        email: email,
        role: role,
        // Add other fields like isActive, password if needed by API
      );
      // Refresh the user list after successful update
      await fetchManagedUsers(forceRefresh: true);
      return true;
    } on ApiException catch (e) {
      _userManagementError = "Failed to update user: ${e.message}";
      _isLoadingUsers = false; // Stop loading on error
      notifyListeners();
      return false;
    } catch (e) {
      _userManagementError = "Failed to update user: An unexpected error occurred.";
      _isLoadingUsers = false; // Stop loading on error
      notifyListeners();
      return false;
    } finally {
       // Already setting isLoadingUsers = false in fetchManagedUsers on success
       // Only need to ensure it's false on error path, which is done above.
    }
  }

  Future<bool> deleteManagedUser(int id) async {
     _isLoadingUsers = true;
     _userManagementError = null;
     notifyListeners();
     try {
        await _apiService.deleteUser(id);
        await fetchManagedUsers(forceRefresh: true);
        return true;
     } on ApiException catch (e) {
        _userManagementError = "Failed to delete user: ${e.message}";
        _isLoadingUsers = false;
        notifyListeners();
        return false;
     } catch (e) {
        _userManagementError = "Failed to delete user: An unexpected error occurred.";
        _isLoadingUsers = false;
        notifyListeners();
        return false;
     }
  }

  Future<void> fetchAvailableRoles() async {
    try {
      final roles = await _apiService.fetchAvailableRoles();
      _availableRoles = roles;
      notifyListeners();
    } catch (e) {
      _logger.warning("Error fetching roles: $e");
      // Keep default 'User' role if fetch fails
    }
  }
}


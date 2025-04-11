import 'dart:convert';
import 'dart:io'; // For HttpStatus
import 'package:http/http.dart' as http;
import '../config.dart'; // Import config

// Removed unused model imports

class ApiService {
  // Use URLs from AppConfig
  final String _serverBaseUrl = AppConfig.serverBaseUrl;

  String? _authToken; // Store the auth token

  void setAuthToken(String? token) {
    _authToken = token;
  }

  // --- Helper Methods ---
  Map<String, String> _getHeaders() {
    final headers = {
      'Content-Type': 'application/json; charset=UTF-8',
      'Accept': 'application/json',
      'ngrok-skip-browser-warning': 'true',
    };
    if (_authToken != null) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    return headers;
  }

  Map<String, String> _getFormHeaders() {
    final headers = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json',
      'ngrok-skip-browser-warning': 'true',
    };
    return headers;
  }

  Future<Map<String, dynamic>> _handleResponse(http.Response response) async {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isNotEmpty) {
        // Check for HTML response and handle it as an error
        if (response.body.trim().toLowerCase().startsWith('<!doctype html>')) {
          print("Error: Received HTML instead of JSON. Status: ${response.statusCode}");
          throw ApiException('Received HTML instead of JSON. Check API endpoint or tunnel.', response.statusCode);
        }
        try {
            return json.decode(response.body) as Map<String, dynamic>;
        } catch (e) {
             print("Error decoding JSON: ${e}");
             print("Received body: ${response.body}");
             throw ApiException('Failed to decode JSON response.', response.statusCode);
        }
      }
      return {}; // Return empty map for successful responses with no body (e.g., 204 No Content)
    } else if (response.statusCode == HttpStatus.unauthorized) { // 401
      print("Error: Unauthorized (401)");
      throw ApiException('Unauthorized. Please log in again.', response.statusCode);
    } else if (response.statusCode == HttpStatus.forbidden) { // 403
        print("Error: Forbidden (403)");
       throw ApiException('Forbidden. You do not have permission.', response.statusCode);
    } else {
      // Handle other errors
      String errorMessage = 'API Error';
      int? statusCode = response.statusCode;
      if (response.body.isNotEmpty) {
        try {
          final errorBody = json.decode(response.body) as Map<String, dynamic>;
          // FastAPI validation errors often use 'detail'
          if (errorBody['detail'] != null) {
             if (errorBody['detail'] is String) {
                errorMessage = errorBody['detail'];
             } else if (errorBody['detail'] is List) {
                // Handle validation errors which might be a list of issues
                errorMessage = (errorBody['detail'] as List).map((item) => item['msg'] ?? item.toString()).join(', ');
             } else {
                 errorMessage = json.encode(errorBody['detail']); // Encode if complex object
             }
          } else {
              errorMessage = errorBody['error'] ?? errorBody['message'] ?? json.encode(errorBody); // Broader check
          }
        } catch (e) {
          errorMessage = response.body.length > 200 ? response.body.substring(0, 200) + '...' : response.body; // Fallback to raw body (truncated)
        }
      } else {
         errorMessage = 'API Error with empty response body.';
      }
      print("Error: API Error ($statusCode): $errorMessage");
      throw ApiException(errorMessage, statusCode);
    }
  }

  Future<List<dynamic>> _handleListResponse(http.Response response) async {
      if (response.statusCode >= 200 && response.statusCode < 300) {
        if (response.body.isNotEmpty) {
          // Check for HTML response and handle it as an error
          if (response.body.trim().toLowerCase().startsWith('<!doctype html>')) {
            print("Error: Received HTML instead of JSON list. Status: ${response.statusCode}");
            throw ApiException('Received HTML instead of JSON list. Check API endpoint or tunnel.', response.statusCode);
          }
           try {
             return json.decode(response.body) as List<dynamic>;
          } catch (e) {
             print("Error decoding JSON list: ${e}");
             print("Received body: ${response.body}");
             throw ApiException('Failed to decode JSON list response.', response.statusCode);
          }
        }
        return []; // Return empty list for successful responses with no body
      } else if (response.statusCode == HttpStatus.unauthorized) { // 401
        print("Error: Unauthorized (401)");
        throw ApiException('Unauthorized. Please log in again.', response.statusCode);
      } else if (response.statusCode == HttpStatus.forbidden) { // 403
         print("Error: Forbidden (403)");
         throw ApiException('Forbidden. You do not have permission.', response.statusCode);
      } else {
        // Handle other errors (similar to _handleResponse)
         String errorMessage = 'API Error';
         int? statusCode = response.statusCode;
         if (response.body.isNotEmpty) {
           try {
             final errorBody = json.decode(response.body) as Map<String, dynamic>;
             if (errorBody['detail'] != null) {
                if (errorBody['detail'] is String) {
                    errorMessage = errorBody['detail'];
                } else {
                    errorMessage = json.encode(errorBody['detail']);
                }
             } else {
                 errorMessage = errorBody['error'] ?? errorBody['message'] ?? json.encode(errorBody);
             }
           } catch (e) {
             errorMessage = response.body.length > 200 ? response.body.substring(0, 200) + '...' : response.body;
           }
         } else {
             errorMessage = 'API Error with empty response body.';
         }
          print("Error: API Error ($statusCode): $errorMessage");
         throw ApiException(errorMessage, statusCode);
      }
    }

  // --- Server API Methods (Examples) ---

  Future<Map<String, dynamic>> login(String username, String password) async {
    print("Attempting login with username: $username to URL: $_serverBaseUrl/token");
    try {
      // Ensure special characters are properly encoded for form data
      final encodedUsername = Uri.encodeComponent(username); // Treat input as username
      final encodedPassword = Uri.encodeComponent(password);
      
      final response = await http.post(
        Uri.parse('$_serverBaseUrl/token'), 
        headers: _getFormHeaders(),
        body: 'username=$encodedUsername&password=$encodedPassword',
      );
      
      print("Login response status: ${response.statusCode}");
      print("Login response body: ${response.body}");
      
      // Returns the raw map for AppState to process (extract token, user info)
      return _handleResponse(response);
    } catch (e) {
      print("Login error: $e");
      rethrow;
    }
  }

  Future<List<dynamic>> fetchLogs() async {
    print("Fetching logs from URL: $_serverBaseUrl/logs?limit=50"); // Added limit
    try {
      final response = await http.get(
        Uri.parse('$_serverBaseUrl/logs').replace(queryParameters: {'limit': '50'}),
        headers: _getHeaders(),
      );
      print("Logs response status: ${response.statusCode}");

      // Parse the outer JSON object first
      final responseBody = await _handleResponse(response);
      
      // Extract the list from the "logs" key
      final logsList = responseBody['logs'] as List<dynamic>?;

      if (logsList == null) {
         print("Error: 'logs' key not found or null in the response body.");
         print("Received body: $responseBody");
         throw ApiException("Invalid response format: Missing 'logs' list.");
      }

      return logsList;
    } catch (e) {
      print("Error fetching logs: $e");
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException("Could not fetch logs: ${e.toString()}");
    }
  }

  Future<Map<String, dynamic>> fetchSystemStatus() async {
    print("Fetching system status from URL: $_serverBaseUrl/status");
    try {
      final response = await http.get(
        Uri.parse('$_serverBaseUrl/status'),
        headers: _getHeaders(),
      );
      print("Status response status: ${response.statusCode}");
      // print("Status response body (first 100 chars): ${response.body.length > 100 ? response.body.substring(0, 100) + '...' : response.body}");

      // _handleResponse will now throw if it receives HTML
      return _handleResponse(response);
    } catch (e) {
      print("Error fetching system status: $e");
       // Rethrow the specific ApiException or a generic one
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException("Could not fetch system status: ${e.toString()}");
    }
  }

  // --- NEW: Server API Methods Stubs ---

  Future<Map<String, dynamic>> register(String name, String email, String password, String role) async {
    // Use POST /api/v1/register endpoint (Public, no Auth required)
    print("Registering new user publicly via: $_serverBaseUrl/register");
    try {
      final response = await http.post(
        Uri.parse('$_serverBaseUrl/register'), 
        headers: {'Content-Type': 'application/json; charset=UTF-8', 'Accept': 'application/json', 'ngrok-skip-browser-warning': 'true'}, // No Auth header
        body: json.encode({
          'username': name, // Using the name field from UI as username
          'email': email,
          'password': password,
          // Role and is_admin are determined by the server for public registration
        }),
      );
      print("Public Register response status: ${response.statusCode}");
      print("Public Register response body: ${response.body}");
      return _handleResponse(response);
    } catch (e) {
      print("Public Registration error: $e");
      rethrow;
    }
  }

  Future<Map<String, dynamic>> postManualAlert(String message, {String? videoUrl}) async {
    // Correctly target the /api/v1/alert endpoint as per API_README.md
    print("Posting manual alert to: $_serverBaseUrl/alert");
    final payload = {
        'message': message,
        // Include video_url only if provided
        if (videoUrl != null) 'video_url': videoUrl,
      };
    try {
        final response = await http.post(
          Uri.parse('$_serverBaseUrl/alert'),
          headers: _getHeaders(), // Requires Bearer token auth
          body: json.encode(payload),
        );
        print("Manual alert response status: ${response.statusCode}");
        print("Manual alert response body: ${response.body}");
        // This endpoint returns JSON confirmation, e.g., {"message": "Alert processed...", "log_id": ...}
        return _handleResponse(response);
    } catch (e) {
       print("Error posting manual alert: $e");
       rethrow;
    }
  }

  Future<List<dynamic>> fetchUsers() async {
    // Uncomment the API call now that the GET /users endpoint is implemented
    print("Fetching users from URL: $_serverBaseUrl/users");
    try {
      final response = await http.get(
        Uri.parse('$_serverBaseUrl/users'), // Correct endpoint
        headers: _getHeaders(), // Requires auth (Admin)
      );
      print("Fetch Users response status: ${response.statusCode}");
      // Assuming the endpoint returns a direct list of users based on List[UserSchema]
      return _handleListResponse(response);
    } catch (e) {
      print("Error fetching users: $e");
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException("Could not fetch users: ${e.toString()}");
    }
  }

  Future<Map<String, dynamic>> createUser(String name, String email, String password, bool isAdmin) async {
    // Use POST /api/v1/users endpoint
    print("Creating user via: $_serverBaseUrl/users");
    try {
       final response = await http.post(
         Uri.parse('$_serverBaseUrl/users'),
         headers: _getHeaders(), // Requires auth token
         body: json.encode({
           'username': email.split('@')[0], // Or let user choose username?
           'email': email,
           'password': password,
           'is_admin': isAdmin, // Pass the boolean directly
           'role': isAdmin ? 'Admin' : 'User' // Or derive role from isAdmin?
           // Ensure the UserCreate schema on the server matches these fields
         }),
       );
       print("Create User response status: ${response.statusCode}");
       print("Create User response body: ${response.body}");
       return _handleResponse(response); 
    } catch (e) {
       print("Error creating user: $e");
       rethrow;
    }
  }

  // Placeholder for update user (requires PUT /api/v1/users/{user_id})
  Future<Map<String, dynamic>> updateUser(int id, {String? name, String? email, String? role, bool? isActive, String? password}) async {
    print("Updating user $id via: $_serverBaseUrl/users/$id");
     // Construct the body with only non-null fields
    Map<String, dynamic> body = {};
    if (name != null) body['username'] = name; // Assuming schema uses username
    if (email != null) body['email'] = email;
    if (role != null) body['role'] = role;
    if (isActive != null) body['is_active'] = isActive;
    if (password != null && password.isNotEmpty) body['password'] = password;

    if (body.isEmpty) {
      throw ApiException("No fields provided for update.");
    }

    try {
       final response = await http.put(
         Uri.parse('$_serverBaseUrl/users/$id'),
         headers: _getHeaders(), // Requires auth token
         body: json.encode(body),
       );
       print("Update User response status: ${response.statusCode}");
       print("Update User response body: ${response.body}");
       return _handleResponse(response); 
    } catch (e) {
       print("Error updating user $id: $e");
       rethrow;
    }
  }

  Future<void> deleteUser(int id) async {
    print("Deleting user $id via: $_serverBaseUrl/users/$id");
    try {
      final response = await http.delete(
        Uri.parse('$_serverBaseUrl/users/$id'),
        headers: _getHeaders(), // Requires auth token
      );
      print("Delete User response status: ${response.statusCode}");
      // Expect 200/204 No Content on success, _handleResponse handles this
       _handleResponse(response);
    } catch (e) {
       print("Error deleting user $id: $e");
       if (e is ApiException && e.statusCode == 404) {
          print("User $id not found for deletion."); // Handle 404 gracefully
          // Decide if you want to rethrow or just return
          return; 
       }
       rethrow;
    }
  }

  // --- Raspberry Pi API Methods (Examples) ---

  Future<void> sendPiCommand(String command, [Map<String, dynamic>? data]) async {
    // Send control commands to the server API, not directly to the Pi
    try {
      final response = await http.post(
        Uri.parse('$_serverBaseUrl/control'),
        headers: _getHeaders(),
        body: json.encode({
          'action': command,
          'parameters': data,
        }),
      );
      _handleResponse(response);
    } catch (e) {
      print("Error sending command to Pi: $e");
      rethrow;
    }
  }

  // --- NEW: Fetch current user details ---
  Future<Map<String, dynamic>> fetchUserMe() async {
    print("Fetching current user details from: $_serverBaseUrl/users/me");
    if (_authToken == null) {
      throw ApiException("Not authenticated", 401); 
    }
    try {
      final response = await http.get(
        Uri.parse('$_serverBaseUrl/users/me'),
        headers: _getHeaders(), // Includes Authorization header
      );
      print("Fetch User Me response status: ${response.statusCode}");
      return _handleResponse(response); // Handles errors and JSON parsing
    } catch (e) {
      print("Error fetching current user: $e");
      // Rethrow specific or generic exception
      if (e is ApiException) {
        rethrow;
      }
      throw ApiException("Could not fetch user details: ${e.toString()}");
    }
  }
}

// Custom Exception for API errors
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, [this.statusCode]);

  @override
  String toString() {
    return "ApiException: $message (Status Code: ${statusCode ?? 'N/A'})";
  }
} 
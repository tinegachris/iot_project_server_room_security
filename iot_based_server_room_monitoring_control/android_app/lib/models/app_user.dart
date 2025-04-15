
class User {
  final int id;
  final String username;
  final String? email; // Made email optional as it might not always be present
  final String role; // Added role based on AppState usage
  final String? name; // Add the missing name field
  final String? token; // Keep token optional

  User({
    required this.id,
    required this.username,
    this.email,
    required this.role,
    this.name, // Add to constructor
    this.token,
  });

  // Manual fromJson - adjust fields based on your actual API response
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int? ?? 0, // Provide default or handle null
      username: json['username'] as String? ?? 'Unknown', // Handle null username
      email: json['email'] as String?,
      role: json['role'] as String? ?? 'user', // Default role if missing
      name: json['name'] as String?, // Parse name
      token: json['token'] as String?,
    );
  }

  // Optional: toJson if needed
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'role': role,
      'name': name, // Add to JSON serialization
      'token': token,
    };
  }
}
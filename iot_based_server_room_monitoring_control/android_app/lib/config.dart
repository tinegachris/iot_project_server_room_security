// lib/config.dart

class AppConfig {
  // Server API Configuration
  static const String serverScheme = "https";
  static const String serverHost = "6897-196-207-133-221.ngrok-free.app";
  static const int serverPort = 443; // Using HTTPS default port for ngrok
  static const String serverApiBasePath = "/api/v1";

  // Use ngrok URL without port in the URL string since it's handled by ngrok
  static String get serverBaseUrl => "$serverScheme://$serverHost$serverApiBasePath";

}
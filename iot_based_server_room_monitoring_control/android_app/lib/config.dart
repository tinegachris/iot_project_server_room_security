// lib/config.dart

class AppConfig {
  // Server API Configuration
  static const String serverScheme = "https";
  static const String serverHost = "big-wallaby-great.ngrok-free.app";
  static const int serverPort = 443; // Using HTTPS default port for ngrok
  static const String serverApiBasePath = "/api/v1";

  // Use ngrok URL without port in the URL string since it's handled by ngrok
  static String get serverBaseUrl => "$serverScheme://$serverHost$serverApiBasePath";

  // Raspberry Pi API Configuration
  static const String raspberryPiScheme = "http";
  // ⬇️ *** IMPORTANT: Replace with your Raspberry Pi's actual IP address ***
  static const String raspberryPiIp = "192.168.100.31"; // <--- REPLACE THIS
  static const int raspberryPiPort = 5000;

  static String get raspberryPiBaseUrl => "$raspberryPiScheme://$raspberryPiIp:$raspberryPiPort";

}
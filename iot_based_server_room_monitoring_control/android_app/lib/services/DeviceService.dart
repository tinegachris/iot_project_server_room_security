// class DeviceService {
//   final String baseUrl = 'https://clarence.fhmconsultants.com/api';

//   Future<List<dynamic>> fetchDevices() async {
//     final response = await http.get(Uri.parse('$baseUrl/devices.php?action=read'));
//     if (response.statusCode == 200) return json.decode(response.body);
//     throw Exception('Failed to load devices');
//   }

//   Future<void> createDevice(...) async { ... }
//   Future<void> updateDevice(...) async { ... }
//   Future<void> deleteDevice(...) async { ... }
// }

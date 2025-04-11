
// // devices
// Widget _manageDevices() {
//   return Scaffold(
//     body: FutureBuilder(
//       future: fetchDevices(),
//       builder: (context, snapshot) {
//         if (snapshot.connectionState == ConnectionState.waiting) {
//           return Center(child: CircularProgressIndicator());
//         }
//         if (snapshot.hasError) {
//           return Center(child: Text('Error: ${snapshot.error}'));
//         }

//         final devices = snapshot.data as List<dynamic>;
//         return ListView.builder(
//           itemCount: devices.length,
//           itemBuilder: (context, index) {
//             return ListTile(
//               title: Text(devices[index]['name']),
//               subtitle: Text("Location: ${devices[index]['location']}"),
//               trailing: Row(
//                 mainAxisSize: MainAxisSize.min,
//                 children: [
//                   IconButton(
//                     icon: Icon(Icons.edit, color: Colors.blue),
//                     onPressed: () => _editDevice(devices[index]),
//                   ),
//                   IconButton(
//                     icon: Icon(Icons.delete, color: Colors.red),
//                     onPressed: () => deleteDevice(devices[index]['id']),
//                   ),
//                 ],
//               ),
//             );
//           },
//         );
//       },
//     ),
//     floatingActionButton: FloatingActionButton(
//       onPressed: _showAddDeviceDialog,
//       backgroundColor: Colors.blue,
//       child: Icon(Icons.add, color: Colors.white),
//     ),
//   );
// }

// void _showAddDeviceDialog() {
//   TextEditingController nameController = TextEditingController();
//   TextEditingController locationController = TextEditingController();
//   TextEditingController statusController = TextEditingController();
//   TextEditingController liveFeedController = TextEditingController();

//   showDialog(
//     context: context,
//     builder: (context) {
//       return AlertDialog(
//         title: Text("Add Device", style: TextStyle(color: Colors.blue)),
//         content: Column(
//           mainAxisSize: MainAxisSize.min,
//           children: [
//             _buildStyledTextField(nameController, "Name"),
//             SizedBox(height: 10),
//             _buildStyledTextField(locationController, "Location"),
//             SizedBox(height: 10),
//             _buildStyledTextField(statusController, "Status"),
//             SizedBox(height: 10),
//             _buildStyledTextField(liveFeedController, "Live Feed URL (optional)"),
//           ],
//         ),
//         actions: [
//           TextButton(onPressed: () => Navigator.pop(context), child: Text("Cancel", style: TextStyle(color: Colors.blue))),
//           ElevatedButton(
//             onPressed: () {
//               createDevice(nameController.text, locationController.text, statusController.text, liveFeedController.text);
//               Navigator.pop(context);
//             },
//             style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
//             child: Text("Save", style: TextStyle(color: Colors.white)),
//           ),
//         ],
//       );
//     },
//   );
// }

// void _editDevice(Map device) {
//   TextEditingController nameController = TextEditingController(text: device['name']);
//   TextEditingController locationController = TextEditingController(text: device['location']);
//   TextEditingController statusController = TextEditingController(text: device['status']);
//   TextEditingController liveFeedController = TextEditingController(text: device['live_feed_url'] ?? '');

//   showDialog(
//     context: context,
//     builder: (context) {
//       return AlertDialog(
//         title: Text("Edit Device", style: TextStyle(color: Colors.blue)),
//         content: Column(
//           mainAxisSize: MainAxisSize.min,
//           children: [
//             _buildStyledTextField(nameController, "Name"),
//             SizedBox(height: 10),
//             _buildStyledTextField(locationController, "Location"),
//             SizedBox(height: 10),
//             _buildStyledTextField(statusController, "Status"),
//             SizedBox(height: 10),
//             _buildStyledTextField(liveFeedController, "Live Feed URL (optional)"),
//           ],
//         ),
//         actions: [
//           TextButton(onPressed: () => Navigator.pop(context), child: Text("Cancel", style: TextStyle(color: Colors.blue))),
//           ElevatedButton(
//             onPressed: () {
//               updateDevice(device['id'], nameController.text, locationController.text, statusController.text, liveFeedController.text);
//               Navigator.pop(context);
//             },
//             style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
//             child: Text("Update", style: TextStyle(color: Colors.white)),
//           ),
//         ],
//       );
//     },
//   );
// }



// Future<List<dynamic>> fetchDevices() async {
//   final response = await http.get(Uri.parse('$baseUrl/devices.php?action=read'));
//   if (response.statusCode == 200) {
//     return json.decode(response.body);
//   } else {
//     throw Exception('Failed to load devices');
//   }
// }

// Future<void> createDevice(String name, String location, String status, String liveFeedUrl) async {
//   await http.post(
//     Uri.parse('$baseUrl/devices.php?action=create'),
//     body: {'name': name, 'location': location, 'status': status, 'live_feed_url': liveFeedUrl},
//   );
//   setState(() {});
// }

// Future<void> updateDevice(int id, String name, String location, String status, String liveFeedUrl) async {
//   final response = await http.post(
//     Uri.parse('$baseUrl/devices.php?action=update'),
//     body: {
//       'id': id.toString(),
//       'name': name,
//       'location': location,
//       'status': status,
//       'live_feed_url': liveFeedUrl,
//     },
//   );

//   if (response.statusCode == 200) {
//     setState(() {}); // Refresh UI after updating
//   } else {
//     throw Exception('Failed to update device');
//   }
// }


// Future<void> deleteDevice(int id) async {
//   await http.post(
//     Uri.parse('$baseUrl/devices.php?action=delete'),
//     body: {'id': id.toString()},
//   );
//   setState(() {});
// }


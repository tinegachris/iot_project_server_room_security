import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

import 'notifications.dart';

class DashboardScreen extends StatefulWidget {
  final String role;

  DashboardScreen({required this.role});

  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;
  final String baseUrl = 'https://clarence.fhmconsultants.com/api'; // Replace with your backend URL

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Text('Dashboard - ${widget.role}'),
        backgroundColor: Colors.blue,
      ),
      body: _buildBody(),
      bottomNavigationBar: _buildBottomNavigationBar(),
    );
  }

  Widget _buildBottomNavigationBar() {
    return BottomNavigationBar(
      currentIndex: _currentIndex,
      onTap: (index) {
        setState(() {
          _currentIndex = index;
          if (index == 5) Navigator.pushReplacementNamed(context, '/login');
        });
      },
      selectedItemColor: Colors.blue,
      unselectedItemColor: Colors.grey,
      items: [
        BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
        if (widget.role == 'Admin')
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Manage Users'),
        if (widget.role == 'Admin')
          BottomNavigationBarItem(icon: Icon(Icons.devices), label: 'Manage Devices'),
        BottomNavigationBarItem(icon: Icon(Icons.live_tv), label: 'Live Feed'),
        BottomNavigationBarItem(icon: Icon(Icons.notifications), label: 'Broadcast'),
        BottomNavigationBarItem(icon: Icon(Icons.logout), label: 'Logout'),
      ],
    );
  }

  Widget _buildBody() {
    switch (_currentIndex) {
      case 0:
        return _buildHomeScreen();
      case 1:
        return widget.role == 'Admin' ? _manageUsers() : _liveFeed();
      case 2:
        return widget.role == 'Admin' ? _manageDevices() : _broadcastNotifications();
      case 3:
        return _liveFeed();
      case 4:
        return BroadcastNotifications();
      case 5:
        return Center(child: Text('Logging out...'));
      default:
        return Center(child: Text('Invalid Option'));
    }
  }

  Widget _buildHomeScreen() {
    return ListView(
      padding: EdgeInsets.all(16.0),
      children: [
        _buildSectionTitle('Latest Devices'),
        _buildDeviceList(),
        SizedBox(height: 20),
        _buildSectionTitle('Live Feed'),
        _liveFeed(),
        SizedBox(height: 20),
        _buildSectionTitle('Notifications'),
        _broadcastNotifications(),
      ],
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Text(
        title,
        style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.blueGrey),
      ),
    );
  }

  Widget _buildDeviceList() {
    return FutureBuilder(
      future: fetchDevices(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Text('Error: ${snapshot.error}');
        }

        final devices = snapshot.data as List<dynamic>;
        return Column(
          children: devices.take(3).map((device) {
            return ListTile(
              title: Text(device['name']),
              subtitle: Text('Status: ${device['status']}'),
            );
          }).toList(),
        );
      },
    );
  }

  // Future<List<dynamic>> fetchDevices() async {
  //   try {
  //     final response = await http.get(Uri.parse('$baseUrl/fetch_devices.php'));
  //     if (response.statusCode == 200) {
  //       return json.decode(response.body);
  //     } else {
  //       throw Exception('Failed to load devices');
  //     }
  //   } catch (e) {
  //     throw Exception('Error fetching devices: $e');
  //   }
  // }



Widget _liveFeed() {
  return FutureBuilder(
    future: fetchLiveFeeds(),
    builder: (context, snapshot) {
      if (snapshot.connectionState == ConnectionState.waiting) {
        return Center(child: CircularProgressIndicator());
      }
      if (snapshot.hasError) {
        return Center(child: Text('Error: ${snapshot.error}'));
      }

      final devices = snapshot.data as List<dynamic>;

      return ListView.builder(
        itemCount: devices.length,
        itemBuilder: (context, index) {
          final device = devices[index];
          return Card(
            margin: EdgeInsets.all(8),
            elevation: 4,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ListTile(
                  title: Text(device['name'], style: TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text("Location: ${device['location']}"),
                ),
                Container(
                  height: 300, // Adjust height as needed
                  child: Text("Live feeds here"),
                ),
              ],
            ),
          );
        },
      );
    },
  );
}
// Fetch the live feed URL from the backend
Future<List<dynamic>> fetchLiveFeeds() async {
  final response = await http.get(Uri.parse('$baseUrl/live_feeds.php'));
  if (response.statusCode == 200) {
    return json.decode(response.body);
  } else {
    throw Exception('Failed to load live feeds');
  }
}


  Widget _broadcastNotifications() {
    return Center(child: Text('Broadcast Notifications - Send messages to devices.'));
  }

// devices
Widget _manageDevices() {
  return Scaffold(
    body: FutureBuilder(
      future: fetchDevices(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        }

        final devices = snapshot.data as List<dynamic>;
        return ListView.builder(
          itemCount: devices.length,
          itemBuilder: (context, index) {
            return ListTile(
              title: Text(devices[index]['name']),
              subtitle: Text("Location: ${devices[index]['location']}"),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: Icon(Icons.edit, color: Colors.blue),
                    onPressed: () => _editDevice(devices[index]),
                  ),
                  IconButton(
                    icon: Icon(Icons.delete, color: Colors.red),
                    onPressed: () => deleteDevice(devices[index]['id']),
                  ),
                ],
              ),
            );
          },
        );
      },
    ),
    floatingActionButton: FloatingActionButton(
      onPressed: _showAddDeviceDialog,
      backgroundColor: Colors.blue,
      child: Icon(Icons.add, color: Colors.white),
    ),
  );
}

void _showAddDeviceDialog() {
  TextEditingController nameController = TextEditingController();
  TextEditingController locationController = TextEditingController();
  TextEditingController statusController = TextEditingController();
  TextEditingController liveFeedController = TextEditingController();

  showDialog(
    context: context,
    builder: (context) {
      return AlertDialog(
        title: Text("Add Device", style: TextStyle(color: Colors.blue)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildStyledTextField(nameController, "Name"),
            SizedBox(height: 10),
            _buildStyledTextField(locationController, "Location"),
            SizedBox(height: 10),
            _buildStyledTextField(statusController, "Status"),
            SizedBox(height: 10),
            _buildStyledTextField(liveFeedController, "Live Feed URL (optional)"),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text("Cancel", style: TextStyle(color: Colors.blue))),
          ElevatedButton(
            onPressed: () {
              createDevice(nameController.text, locationController.text, statusController.text, liveFeedController.text);
              Navigator.pop(context);
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
            child: Text("Save", style: TextStyle(color: Colors.white)),
          ),
        ],
      );
    },
  );
}

void _editDevice(Map device) {
  TextEditingController nameController = TextEditingController(text: device['name']);
  TextEditingController locationController = TextEditingController(text: device['location']);
  TextEditingController statusController = TextEditingController(text: device['status']);
  TextEditingController liveFeedController = TextEditingController(text: device['live_feed_url'] ?? '');

  showDialog(
    context: context,
    builder: (context) {
      return AlertDialog(
        title: Text("Edit Device", style: TextStyle(color: Colors.blue)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildStyledTextField(nameController, "Name"),
            SizedBox(height: 10),
            _buildStyledTextField(locationController, "Location"),
            SizedBox(height: 10),
            _buildStyledTextField(statusController, "Status"),
            SizedBox(height: 10),
            _buildStyledTextField(liveFeedController, "Live Feed URL (optional)"),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text("Cancel", style: TextStyle(color: Colors.blue))),
          ElevatedButton(
            onPressed: () {
              updateDevice(device['id'], nameController.text, locationController.text, statusController.text, liveFeedController.text);
              Navigator.pop(context);
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
            child: Text("Update", style: TextStyle(color: Colors.white)),
          ),
        ],
      );
    },
  );
}



Future<List<dynamic>> fetchDevices() async {
  final response = await http.get(Uri.parse('$baseUrl/devices.php?action=read'));
  if (response.statusCode == 200) {
    return json.decode(response.body);
  } else {
    throw Exception('Failed to load devices');
  }
}

Future<void> createDevice(String name, String location, String status, String liveFeedUrl) async {
  await http.post(
    Uri.parse('$baseUrl/devices.php?action=create'),
    body: {'name': name, 'location': location, 'status': status, 'live_feed_url': liveFeedUrl},
  );
  setState(() {});
}

Future<void> updateDevice(int id, String name, String location, String status, String liveFeedUrl) async {
  final response = await http.post(
    Uri.parse('$baseUrl/devices.php?action=update'),
    body: {
      'id': id.toString(),
      'name': name,
      'location': location,
      'status': status,
      'live_feed_url': liveFeedUrl,
    },
  );

  if (response.statusCode == 200) {
    setState(() {}); // Refresh UI after updating
  } else {
    throw Exception('Failed to update device');
  }
}


Future<void> deleteDevice(int id) async {
  await http.post(
    Uri.parse('$baseUrl/devices.php?action=delete'),
    body: {'id': id.toString()},
  );
  setState(() {});
}










//users
Widget _manageUsers() {
  return Scaffold(
    body: FutureBuilder(
      future: fetchUsers(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        }

        final users = snapshot.data as List<dynamic>;
        return ListView.builder(
          itemCount: users.length,
          itemBuilder: (context, index) {
            return ListTile(
              title: Text(users[index]['name']),
              subtitle: Text(users[index]['email']),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: Icon(Icons.edit, color: Colors.blue),
                    onPressed: () => _editUser(users[index]),
                  ),
                  IconButton(
                    icon: Icon(Icons.delete, color: Colors.red),
                    onPressed: () => deleteUser(users[index]['id']),
                  ),
                ],
              ),
            );
          },
        );
      },
    ),
    floatingActionButton: FloatingActionButton(
      onPressed: _showAddUserDialog,
      backgroundColor: Colors.blue,
      child: Icon(Icons.add, color: Colors.white),
    ),
  );
}


void _showAddUserDialog() {
  TextEditingController nameController = TextEditingController();
  TextEditingController emailController = TextEditingController();
  TextEditingController passwordController = TextEditingController();
  TextEditingController roleController = TextEditingController();

  showDialog(
    context: context,
    builder: (context) {
      return AlertDialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        title: Text(
          "Add User",
          style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildStyledTextField(nameController, "Name"),
              SizedBox(height: 10),
              _buildStyledTextField(emailController, "Email"),
              SizedBox(height: 10),
              _buildStyledTextField(passwordController, "Password", obscureText: true),
              SizedBox(height: 10),
              _buildStyledTextField(roleController, "Role"),
            ],
          ),
        ),
        actions: _buildDialogActions(() {
          createUser(nameController.text, emailController.text, passwordController.text, roleController.text);
          Navigator.pop(context);
        }),
      );
    },
  );
}



void _editUser(Map user) {
  TextEditingController nameController = TextEditingController(text: user['name']);
  TextEditingController emailController = TextEditingController(text: user['email']);
  TextEditingController roleController = TextEditingController(text: user['role']);

  showDialog(
    context: context,
    builder: (context) {
      return AlertDialog(
        backgroundColor: Colors.white, // White background
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)), // Rounded corners
        title: Center(
          child: Text(
            "Edit User",
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.blue),
          ),
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildStyledTextField(nameController, "Name"),
              SizedBox(height: 10),
              _buildStyledTextField(emailController, "Email"),
              SizedBox(height: 10),
              _buildStyledTextField(roleController, "Role"),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text("Cancel", style: TextStyle(color: Colors.blue, fontSize: 16)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue, // Blue button
              foregroundColor: Colors.white, // White text
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            ),
            onPressed: () {
              updateUser(user['id'], nameController.text, emailController.text, roleController.text);
              Navigator.pop(context);
            },
            child: Text("Update", style: TextStyle(fontSize: 16)),
          ),
        ],
      );
    },
  );
}

// Helper method for styling text fields
Widget _buildStyledTextField(TextEditingController controller, String label ,{bool obscureText = false}) {
  return TextField(
    controller: controller,
    decoration: InputDecoration(
      labelText: label,
      labelStyle: TextStyle(color: Colors.blue),
      filled: true,
      fillColor: Colors.blue.withOpacity(0.1), // Light blue background
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: Colors.blue),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: Colors.blue, width: 2),
      ),
    ),
  );
}



  Widget _buildTextField(TextEditingController controller, String label, {bool obscureText = false}) {
    return TextField(
      controller: controller,
      decoration: InputDecoration(labelText: label),
      obscureText: obscureText,
    );
  }

  List<Widget> _buildDialogActions(VoidCallback onSave) {
    return [
      TextButton(onPressed: () => Navigator.pop(context), child: Text("Cancel")),
      TextButton(onPressed: onSave, child: Text("Save")),
    ];
  }

  Future<List<dynamic>> fetchUsers() async {
    final response = await http.get(Uri.parse('$baseUrl/users.php?action=read'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to load users');
    }
  }

 Future<void> updateUser(dynamic id, String name, String email, String role) async {
  final response = await http.post(
    Uri.parse('$baseUrl/users.php?action=update'),
    body: {
      'id': id.toString(),  // Convert to String to avoid type errors
      'name': name,
      'email': email,
      'role': role,
    },
  );

  if (response.statusCode == 200) {
    setState(() {}); // Refresh UI after update
  } else {
    throw Exception('Failed to update user');
  }
}

  Future<void> createUser(String name, String email, String password, String role) async {
    await http.post(Uri.parse('$baseUrl/users.php?action=create'),
      body: {'name': name, 'email': email, 'password': password, 'role': role});
    setState(() {});
  }

  Future<void> deleteUser(int id) async {
    await http.post(Uri.parse('$baseUrl/users.php?action=delete'), body: {'id': id.toString()});
    setState(() {});
  }
}


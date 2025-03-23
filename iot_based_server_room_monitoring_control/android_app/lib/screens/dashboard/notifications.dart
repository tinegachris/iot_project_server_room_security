import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class BroadcastNotifications extends StatefulWidget {
  @override
  _BroadcastNotificationsState createState() => _BroadcastNotificationsState();
}

class _BroadcastNotificationsState extends State<BroadcastNotifications> {
  final String baseUrl = 'https://clarence.fhmconsultants.com/api'; // Replace with your backend URL

  List<dynamic> notifications = [];
  String selectedGroup = 'Everyone';

  TextEditingController titleController = TextEditingController();
  TextEditingController messageController = TextEditingController();

  @override
  void initState() {
    super.initState();
    fetchNotifications();
  }

  Future<void> sendNotification() async {
    final response = await http.post(
      Uri.parse('$baseUrl/broadcast.php?action=broadcast'),
      body: {
        'title': titleController.text,
        'message': messageController.text,
        'target_group': selectedGroup,
      },
    );

    if (response.statusCode == 200) {
      final responseData = json.decode(response.body);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(responseData['message'])),
      );
      fetchNotifications(); // Refresh notifications after sending
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to send notification")),
      );
    }
  }

  Future<void> fetchNotifications() async {
    final response = await http.get(Uri.parse('$baseUrl/broadcast.php?action=fetch'));
    if (response.statusCode == 200) {
      setState(() {
        notifications = json.decode(response.body);
      });
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to load notifications")),
      );
    }
  }

  void _showNotificationDialog() {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text("Send Notification", style: TextStyle(color: Colors.blue)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildTextField(titleController, "Title"),
                _buildTextField(messageController, "Message"),
                DropdownButton<String>(
                  value: selectedGroup,
                  onChanged: (value) {
                    setState(() {
                      selectedGroup = value!;
                    });
                  },
                  items: ['Everyone', 'Admins', 'Users'].map((group) {
                    return DropdownMenuItem(value: group, child: Text(group));
                  }).toList(),
                ),
              ],
            ),
          ),
          actions: _buildDialogActions(() {
            sendNotification();
            Navigator.pop(context);
          }),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: notifications.isEmpty
              ? Center(child: Text("No notifications yet"))
              : ListView.builder(
                  itemCount: notifications.length,
                  itemBuilder: (context, index) {
                    return Card(
                      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: ListTile(
                        title: Text(notifications[index]['title'], style: TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text(notifications[index]['message']),
                        trailing: Chip(
                          label: Text(notifications[index]['target_group']),
                          backgroundColor: Colors.blue.shade100,
                        ),
                      ),
                    );
                  },
                ),
        ),
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: ElevatedButton.icon(
            icon: Icon(Icons.add),
            label: Text("Send Notification"),
            onPressed: _showNotificationDialog,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue,
              foregroundColor: Colors.white,
              padding: EdgeInsets.symmetric(vertical: 12, horizontal: 20),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildTextField(TextEditingController controller, String label) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: TextField(
        controller: controller,
        decoration: InputDecoration(
          labelText: label,
          border: OutlineInputBorder(),
        ),
      ),
    );
  }

  List<Widget> _buildDialogActions(VoidCallback onSave) {
    return [
      TextButton(onPressed: () => Navigator.pop(context), child: Text("Cancel")),
      ElevatedButton(onPressed: onSave, child: Text("Send")),
    ];
  }
}

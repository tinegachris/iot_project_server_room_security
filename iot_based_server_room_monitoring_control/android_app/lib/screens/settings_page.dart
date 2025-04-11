import 'package:flutter/material.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: <Widget>[
          // --- General Settings ---
          const ListTile(
             leading: Icon(Icons.notifications_outlined),
             title: Text('Notification Preferences'),
             subtitle: Text('Manage alert channels and types'),
             // onTap: () { /* TODO: Navigate to notification settings */ },
             // trailing: Icon(Icons.chevron_right),
          ),
          const Divider(),
          // --- API/Server Settings ---
          ListTile(
             leading: const Icon(Icons.api_outlined),
             title: const Text('API Server Address'),
             subtitle: Text('Current: [Placeholder Server URL]'), // TODO: Get from AppState/Config
             // onTap: () { /* TODO: Allow editing API URL */ },
             // trailing: Icon(Icons.edit_outlined),
          ),
          ListTile(
             leading: const Icon(Icons.vpn_key_outlined),
             title: const Text('API Key (Main Server)'), // Assuming this is managed elsewhere
             subtitle: const Text('**********'),
          ),
          const Divider(),
          // --- Account Settings ---
          const ListTile(
             leading: Icon(Icons.account_circle_outlined),
             title: Text('Account'),
             subtitle: Text('Manage your profile and password'),
             // onTap: () { /* TODO: Navigate to account settings */ },
             // trailing: Icon(Icons.chevron_right),
          ),
          const ListTile(
             leading: Icon(Icons.logout),
             title: Text('Logout'),
             // TODO: Implement logout functionality here or rely on drawer
          ),
           const Divider(),
          // --- About ---
           const ListTile(
             leading: Icon(Icons.info_outline),
             title: Text('About'),
             subtitle: Text('App Version: 1.0.0'), // TODO: Get version dynamically
          ),
        ],
      ),
    );
  }
} 
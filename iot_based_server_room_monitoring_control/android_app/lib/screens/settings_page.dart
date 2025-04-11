import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../screens/add_edit_user_page.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: <Widget>[
          // --- General Settings ---
          ListTile(
             leading: const Icon(Icons.notifications_outlined),
             title: const Text('Notification Preferences'),
             subtitle: const Text('Manage alert channels and types'),
             onTap: () {
               ScaffoldMessenger.of(context).showSnackBar(
                 const SnackBar(content: Text('Notification settings coming soon')),
               );
             },
             trailing: const Icon(Icons.chevron_right),
          ),
          const Divider(),
          // --- API/Server Settings ---
          ListTile(
             leading: const Icon(Icons.api_outlined),
             title: const Text('API Server Address'),
             subtitle: Text('Current: ${appState.currentUser?.token ?? 'Not configured'}'),
             onTap: () {
               ScaffoldMessenger.of(context).showSnackBar(
                 const SnackBar(content: Text('API URL editing coming soon')),
               );
             },
             trailing: const Icon(Icons.edit_outlined),
          ),
          const ListTile(
             leading: Icon(Icons.vpn_key_outlined),
             title: Text('API Key (Main Server)'),
             subtitle: Text('**********'),
          ),
          const Divider(),
          // --- Account Settings ---
          ListTile(
             leading: const Icon(Icons.account_circle_outlined),
             title: const Text('Account'),
             subtitle: const Text('Manage your profile and password'),
             onTap: () {
               Navigator.of(context).push(
                 MaterialPageRoute(
                   builder: (context) => AddEditUserPage(user: appState.currentUser),
                 ),
               );
             },
             trailing: const Icon(Icons.chevron_right),
          ),
          ListTile(
             leading: const Icon(Icons.logout),
             title: const Text('Logout'),
             onTap: () async {
               final scaffoldMessenger = ScaffoldMessenger.of(context);
               final navigator = Navigator.of(context);

               try {
                 await appState.logout();
                 if (context.mounted) {
                   navigator.pushReplacementNamed('/login');
                 }
               } catch (e) {
                 if (context.mounted) {
                   scaffoldMessenger.showSnackBar(
                     SnackBar(
                       content: Text('Logout failed: ${e.toString()}'),
                       backgroundColor: Colors.red,
                     ),
                   );
                 }
               }
             },
          ),
          const Divider(),
          // --- About ---
          const ListTile(
             leading: Icon(Icons.info_outline),
             title: Text('About'),
             subtitle: Text('App Version: 1.0.0'),
          ),
        ],
      ),
    );
  }
}
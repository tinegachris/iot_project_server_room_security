import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../widgets/status_dashboard.dart'; // Import the dashboard widget
import '../widgets/log_viewer.dart'; // Import the log viewer widget
// import '../widgets/app_drawer.dart'; // Removed - AppDrawer is defined below
import 'login and signup/login_and_register.dart'; // Corrected path and filename
// import 'logs_page.dart'; // Commented out - Needs verification
// import 'settings_page.dart'; // Commented out - Needs verification
// import 'settings_page.dart'; // Keep for now, might need path adjustment
// import 'user_management_page.dart'; // Commented out - Needs verification
import 'controls_page.dart'; // Import the new controls page
import 'logs_page.dart'; // Import the LogsPage
import 'user_management_page.dart'; // Import the UserManagementPage
import 'settings_page.dart'; // Import the SettingsPage

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();
    // Fetch initial data when the HomePage is initialized AFTER the first frame
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final appState = Provider.of<AppState>(context, listen: false);
      if (appState.isAuthenticated && appState.currentStatus == null) {
        // Only fetch if authenticated and status is not already loaded
        appState.fetchInitialData();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    // Use a Consumer to react to changes in AppState, especially error messages
    return Consumer<AppState>(builder: (context, appState, child) {
      // If not authenticated, redirect to login
      if (!appState.isAuthenticated) {
        // Use WidgetsBinding to schedule navigation after build
        WidgetsBinding.instance.addPostFrameCallback((_) {
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (context) => const LoginRegisterScreen()), // Use correct class name
          );
        });
        // Return an empty container while navigating
        return const Scaffold(body: Center(child: CircularProgressIndicator()));
      }

      // Check for suspended polling and show banner
      if (appState.isPollingSuspended) {
         WidgetsBinding.instance.addPostFrameCallback((_) {
            if (context.mounted) {
               // Clear any existing banner first
               ScaffoldMessenger.of(context).removeCurrentMaterialBanner();
               ScaffoldMessenger.of(context).showMaterialBanner(
                  MaterialBanner(
                     padding: const EdgeInsets.all(12),
                     content: const Text('Live updates paused due to connection issues.'),
                     leading: const Icon(Icons.warning_amber_rounded, color: Colors.orange),
                     backgroundColor: Colors.orange[100],
                     actions: <Widget>[
                       TextButton(
                         child: const Text('RETRY', style: TextStyle(fontWeight: FontWeight.bold)),
                         onPressed: () {
                           ScaffoldMessenger.of(context).hideCurrentMaterialBanner();
                           // Attempt to restart polling by fetching initial data
                           appState.fetchInitialData().then((_) {
                              if (!appState.isPollingSuspended) { // Check if retry was successful
                                 appState.startPolling();
                              } 
                              // If still suspended, banner will reappear on next build
                           });
                         },
                       ),
                        TextButton(
                         child: const Text('DISMISS', style: TextStyle(color: Colors.black54)),
                         onPressed: () {
                           ScaffoldMessenger.of(context).hideCurrentMaterialBanner();
                           // Optionally, add state to *keep* banner dismissed until next app start?
                         },
                       ),
                     ],
                  ),
               );
            }
         });
      } else {
           // If polling is not suspended, ensure banner is removed
           WidgetsBinding.instance.addPostFrameCallback((_) {
              if (context.mounted) {
                 ScaffoldMessenger.of(context).removeCurrentMaterialBanner();
              }
           });
      }

      // Main Scaffold with content
      return Scaffold(
        appBar: AppBar(
          title: const Text('Server Room Monitor'),
          actions: [
            // Optional: Add a refresh button
            IconButton(
              icon: const Icon(Icons.refresh),
              // Disable refresh if currently fetching status or logs
              onPressed: (appState.isFetchingStatus || appState.isFetchingLogs) ? null : () => appState.fetchInitialData(),
              tooltip: 'Refresh Data',
            ),
          ],
        ),
        drawer: const AppDrawer(), // Use the AppDrawer widget
        body: RefreshIndicator(
           // Disable refresh if already fetching
           onRefresh: (appState.isFetchingStatus || appState.isFetchingLogs) ? () async {} : () => appState.fetchInitialData(),
           child: Center(
             child: Padding(
               padding: const EdgeInsets.all(8.0), // Adjust padding if needed
               // Use ListView for scrollability if content overflows
               child: ListView(
                 children: const [
                   StatusDashboard(), // Display the dashboard
                   SizedBox(height: 16),
                   LogViewer(maxEntriesToShow: 5), // Display recent logs
                    // Add more sections/widgets as needed
                 ],
               ),
             ),
           )
        ),
      );
    });
  }
}

// --- AppDrawer Widget (Defined within HomePage) ---
class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context, listen: false);
    final currentUser = appState.currentUser; // Get current user info

    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: <Widget>[
          UserAccountsDrawerHeader(
            accountName: Text(currentUser?.name ?? 'User'),
            accountEmail: Text(currentUser?.email ?? 'No email'),
            currentAccountPicture: CircleAvatar(
              backgroundColor: Colors.white,
              child: Text(
                currentUser?.name?.substring(0, 1).toUpperCase() ?? 'U',
                style: const TextStyle(fontSize: 40.0),
              ),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.home_outlined),
            title: const Text('Home'),
            onTap: () {
              Navigator.pop(context); // Close the drawer
              // Already on home, do nothing or explicitly navigate if needed
            },
          ),
          ListTile(
            leading: const Icon(Icons.list_alt),
            title: const Text('View All Logs'),
            onTap: () {
              Navigator.pop(context); // Close the drawer
              Navigator.push(context, MaterialPageRoute(builder: (context) => const LogsPage())); // Navigate to LogsPage
            },
          ),
          ListTile(
            leading: const Icon(Icons.settings_outlined),
            title: const Text('Settings'),
            onTap: () {
              Navigator.pop(context); // Close the drawer
              Navigator.push(context, MaterialPageRoute(builder: (context) => const SettingsPage())); // Navigate to SettingsPage
            },
          ),
          ListTile(
            leading: const Icon(Icons.admin_panel_settings_outlined),
            title: const Text('Manage Users'),
            onTap: () {
              Navigator.pop(context); // Close the drawer
              Navigator.push(context, MaterialPageRoute(builder: (context) => const UserManagementPage())); // Navigate to UserManagementPage
            },
          ),
         ListTile(
           leading: const Icon(Icons.control_camera), // Use an appropriate icon
           title: const Text('Remote Controls'),
           onTap: () {
             Navigator.pop(context); // Close the drawer
             Navigator.push(context, MaterialPageRoute(builder: (context) => const ControlsPage()));
           },
         ),
        const Divider(),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Logout'),
            onTap: () {
              // Clear auth token and navigate to login
              Provider.of<AppState>(context, listen: false).logout();
              Navigator.of(context).pushAndRemoveUntil(
                MaterialPageRoute(builder: (context) => const LoginRegisterScreen()), // Use correct class name
                (Route<dynamic> route) => false, // Remove all previous routes
              );
            },
          ),
        ],
      ),
    );
  }
}
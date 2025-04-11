import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:security_iot/providers/app_state.dart';
import 'package:security_iot/screens/dashboard/dashboardviews/controls_screen.dart';
import 'package:security_iot/screens/dashboard/dashboardviews/home_screen.dart';
import 'package:security_iot/screens/dashboard/dashboardviews/logs_screen.dart';
import 'package:security_iot/screens/dashboard/dashboardviews/manage_users.dart';
import 'package:security_iot/screens/dashboard/dashboardviews/notifications_screen.dart';

class DashboardScreen extends StatefulWidget {
  final String role;

  const DashboardScreen({super.key, required this.role});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    // Start polling when the dashboard is initialized
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<AppState>(context, listen: false).startPolling();
    });
  }

  @override
  void dispose() {
    // Stop polling when the dashboard is disposed (e.g., user logs out)
    // Accessing provider here might be tricky if the context is already removed.
    // It's generally safer to stop polling in AppState's logout method or dispose.
    // However, if DashboardScreen could be popped off while logged in, stopping here is needed.
    // Consider if AppState provider is still available during dispose.
    try {
      Provider.of<AppState>(context, listen: false).stopPolling();
    } catch (e) {
      // Error stopping polling during dispose - might already be stopped
    }
    super.dispose();
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Logout'),
        content: const Text('Are you sure you want to log out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Logout'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      if (mounted) {
         await Provider.of<AppState>(context, listen: false).logout();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // Determine the list of available screens based on role
    final List<Widget> screens = _getScreensForRole(widget.role);
    final List<BottomNavigationBarItem> navItems = _getNavItemsForRole(widget.role);

    // Ensure currentIndex is valid for the available items
    if (_currentIndex >= screens.length) {
      _currentIndex = 0; // Reset to first screen if index is out of bounds
    }

    return Scaffold(
      backgroundColor: Colors.grey[100], // Lighter background
      appBar: AppBar(
        title: Text('Dashboard - ${widget.role}'), // Removed style for default
        backgroundColor: Theme.of(context).colorScheme.primaryContainer, // Use theme color
        elevation: 1,
        actions: [
          IconButton(
            tooltip: 'Logout', // Add tooltip
            icon: const Icon(Icons.logout),
            onPressed: _logout,
          ),
        ],
      ),
      // Use IndexedStack to keep state of inactive screens
      body: IndexedStack(
         index: _currentIndex,
         children: screens,
      ),
      bottomNavigationBar: navItems.length > 1 ? BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        selectedItemColor: Theme.of(context).colorScheme.primary,
        unselectedItemColor: Colors.grey[600],
        backgroundColor: Colors.white,
        type: BottomNavigationBarType.fixed, // Ensures all labels are visible
        items: navItems,
      ) : null, // Don't show nav bar if only one item
    );
  }

  // Helper to get screens based on role
  List<Widget> _getScreensForRole(String role) {
    final List<Widget> commonScreens = [
      const HomeScreen(),
      const NotificationsScreen(),
    ];
    if (role == 'Admin') {
      return [
        const HomeScreen(),
        const ControlsScreen(),
        LogsScreen(),
        const NotificationsScreen(),
        const ManageUsersScreen(),
      ];
    } else if (role == 'Security') {
       return [
         const HomeScreen(),
         const ControlsScreen(), // Security might need controls
         LogsScreen(),
         const NotificationsScreen(),
       ];
    } else { // Default role (e.g., 'Staff', 'User')
       return [
         ...commonScreens,
         LogsScreen(), // Add Logs screen for default users
       ];
    }
    // Add other roles as needed
  }

  // Helper to get navigation items based on role
  List<BottomNavigationBarItem> _getNavItemsForRole(String role) {
     final List<BottomNavigationBarItem> items = [
       const BottomNavigationBarItem(icon: Icon(Icons.home_outlined), activeIcon: Icon(Icons.home), label: 'Home'),
       const BottomNavigationBarItem(icon: Icon(Icons.notifications_outlined), activeIcon: Icon(Icons.notifications), label: 'Alerts'),
     ];
     if (role == 'Admin') {
       items.insert(1, const BottomNavigationBarItem(icon: Icon(Icons.toggle_on_outlined), activeIcon: Icon(Icons.toggle_on), label: 'Controls'));
       items.insert(2, const BottomNavigationBarItem(icon: Icon(Icons.history_outlined), activeIcon: Icon(Icons.history), label: 'Logs'));
       items.add(const BottomNavigationBarItem(icon: Icon(Icons.people_outline), activeIcon: Icon(Icons.people), label: 'Users'));
     } else if (role == 'Security') {
       items.insert(1, const BottomNavigationBarItem(icon: Icon(Icons.toggle_on_outlined), activeIcon: Icon(Icons.toggle_on), label: 'Controls'));
       items.insert(2, const BottomNavigationBarItem(icon: Icon(Icons.history_outlined), activeIcon: Icon(Icons.history), label: 'Logs'));
     }
     // Add other roles
     else { // Default role (e.g., 'Staff', 'User')
        items.insert(1, const BottomNavigationBarItem(icon: Icon(Icons.history_outlined), activeIcon: Icon(Icons.history), label: 'Logs'));
     }
     return items;
  }
}

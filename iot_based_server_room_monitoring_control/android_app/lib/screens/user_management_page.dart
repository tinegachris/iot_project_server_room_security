import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../models/user.dart';
import '../screens/add_edit_user_page.dart';

class UserManagementPage extends StatefulWidget {
  const UserManagementPage({super.key});

  @override
  State<UserManagementPage> createState() => _UserManagementPageState();
}

class _UserManagementPageState extends State<UserManagementPage> {
  @override
  void initState() {
    super.initState();
    // Fetch users when the page loads, if not already loaded
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final appState = Provider.of<AppState>(context, listen: false);
      // Use forceRefresh: true if you always want the latest list when visiting
      appState.fetchManagedUsers(forceRefresh: true);
    });
  }

  Future<void> _confirmAndDeleteUser(BuildContext ctx, AppState appState, User user) async {
    final scaffoldMessenger = ScaffoldMessenger.of(ctx);

    final confirm = await showDialog<bool>(
      context: ctx,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          title: const Text('Confirm Delete'),
          content: Text('Are you sure you want to delete user "${user.username}"? This action cannot be undone.'),
          actions: <Widget>[
            TextButton(
              child: const Text('Cancel'),
              onPressed: () => Navigator.of(dialogContext).pop(false),
            ),
            TextButton(
              style: TextButton.styleFrom(foregroundColor: Colors.red),
              child: const Text('DELETE'),
              onPressed: () => Navigator.of(dialogContext).pop(true),
            ),
          ],
        );
      },
    );

    if (confirm == true) {
      try {
        final success = await appState.deleteManagedUser(user.id);
        final message = success ? 'User deleted successfully.' : (appState.userManagementError ?? 'Failed to delete user.');
        scaffoldMessenger.showSnackBar(
          SnackBar(
            content: Text(message),
            backgroundColor: success ? Colors.green : Colors.red,
          ),
        );
      } catch (e) {
        scaffoldMessenger.showSnackBar(
          SnackBar(
            content: Text('Error deleting user: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
      // Clear error after showing
      appState.clearUserManagementError();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Manage Users'),
      ),
      body: Consumer<AppState>(
        builder: (context, appState, child) {
          final users = appState.managedUsers;
          final isLoading = appState.isLoadingUsers;
          final error = appState.userManagementError;

          // Handle loading state
          if (isLoading && users.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          // Handle error state
          if (error != null && users.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                   mainAxisAlignment: MainAxisAlignment.center,
                   children: [
                     Text(
                       'Error loading users: $error',
                       style: const TextStyle(color: Colors.red),
                       textAlign: TextAlign.center,
                     ),
                     const SizedBox(height: 10),
                     ElevatedButton.icon(
                        icon: const Icon(Icons.refresh),
                        label: const Text('Retry'),
                        onPressed: () => appState.fetchManagedUsers(forceRefresh: true),
                     )
                   ],
                )
              ),
            );
          }

          // Handle empty state
           if (users.isEmpty) {
              return Center(
                 child: Column(
                   mainAxisAlignment: MainAxisAlignment.center,
                   children: [
                     const Text('No users found.'),
                      const SizedBox(height: 10),
                     ElevatedButton.icon(
                        icon: const Icon(Icons.refresh),
                        label: const Text('Refresh'),
                        onPressed: () => appState.fetchManagedUsers(forceRefresh: true),
                     )
                   ],
                 )
              );
           }

          // Display user list
          return RefreshIndicator(
            onRefresh: () => appState.fetchManagedUsers(forceRefresh: true),
            child: ListView.builder(
              itemCount: users.length,
              itemBuilder: (context, index) {
                final user = users[index];
                // Avoid deleting the currently logged-in user (if possible)
                final isCurrentUser = appState.currentUser?.id == user.id;

                return ListTile(
                  leading: CircleAvatar(
                     child: Text(user.username.substring(0, 1).toUpperCase()),
                  ),
                  title: Text(user.username),
                  subtitle: Text('Role: ${user.role} | Email: ${user.email ?? 'N/A'}'),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.edit_outlined, color: Colors.blue),
                        tooltip: 'Edit User',
                        onPressed: () {
                          Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (context) => AddEditUserPage(user: user),
                            ),
                          );
                        },
                      ),
                      IconButton(
                        icon: Icon(Icons.delete_outline, color: isCurrentUser ? Colors.grey : Colors.red),
                        tooltip: isCurrentUser ? 'Cannot delete current user' : 'Delete User',
                        // Disable delete for the current user
                        onPressed: isCurrentUser ? null : () => _confirmAndDeleteUser(context, appState, user),
                      ),
                    ],
                  ),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'Add User',
        onPressed: () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (context) => const AddEditUserPage(),
            ),
          );
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
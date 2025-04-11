// import 'dart:convert'; // Not needed if using models fully
import 'package:flutter/material.dart';
import 'package:provider/provider.dart'; // ✅ Keep provider
import '../../../providers/app_state.dart'; // ✅ Keep AppState import
// import '../../../services/api_service.dart';
import '../../../models/user.dart'; // ✅ Keep User model import

class ManageUsersScreen extends StatefulWidget {
  const ManageUsersScreen({super.key});

  @override
  State<ManageUsersScreen> createState() => _ManageUsersScreenState();
}

class _ManageUsersScreenState extends State<ManageUsersScreen> {
  // Removed local state variables

  @override
  void initState() {
    super.initState();
    // Fetch users when the screen initializes, if not already loaded
    WidgetsBinding.instance.addPostFrameCallback((_) {
       final appState = Provider.of<AppState>(context, listen: false);
       // Check if users are empty or loading to trigger initial fetch
       if (appState.managedUsers.isEmpty && !appState.isLoadingUsers) {
          appState.fetchManagedUsers();
       }
    });
  }

  // Removed local fetch/create/update/delete methods
  /*
  @override
  void didChangeDependencies() { ... }
  Future<void> _fetchUsers() async { ... }
  Future<void> createUser(...) async { ... }
  Future<void> updateUser(...) async { ... }
  Future<void> deleteUser(...) async { ... }
  */

  @override
  Widget build(BuildContext context) {
    // Consume AppState for user list, loading, and error state
    final appState = context.watch<AppState>();

    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: _buildBody(appState),
      floatingActionButton: FloatingActionButton(
        // Pass AppState to dialog method
        onPressed: () => _showAddUserDialog(context, appState),
        backgroundColor: Theme.of(context).colorScheme.primary,
        tooltip: 'Add User',
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  Widget _buildBody(AppState appState) {
     // Use state directly from AppState
     final bool isLoading = appState.isLoadingUsers;
     final String? error = appState.userManagementError;
     final List<User> users = appState.managedUsers;

     // Show loading indicator
     if (isLoading && users.isEmpty) { // Show only if list is empty while loading
       return const Center(child: CircularProgressIndicator());
     }
     // Show error message
     if (error != null && users.isEmpty) { // Show only if list is empty on error
        return Center(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                 mainAxisAlignment: MainAxisAlignment.center,
                 children: [
                   Text('Error loading users: $error', textAlign: TextAlign.center, style: TextStyle(color: Colors.red[700])),
                   const SizedBox(height: 10),
                   // Call AppState method to retry
                   ElevatedButton(onPressed: () => appState.fetchManagedUsers(forceRefresh: true), child: const Text('Retry')),
                 ],
               ),
            ));
     }
     // Show empty state
     if (users.isEmpty) {
       return RefreshIndicator(
           onRefresh: () => appState.fetchManagedUsers(forceRefresh: true),
           child: const Center(child: Text('No users found.'))
        );
     }

     // Display the list
     return RefreshIndicator(
        // Call AppState method to refresh
        onRefresh: () => appState.fetchManagedUsers(forceRefresh: true),
        child: ListView.builder(
          padding: const EdgeInsets.all(8.0),
          itemCount: users.length,
          itemBuilder: (context, index) {
             final user = users[index];
            return Card(
              elevation: 1.5,
              margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
              child: ListTile(
                leading: CircleAvatar(
                   backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                   child: Text(user.role.substring(0,1).toUpperCase()),
                ),
                title: Text(user.username, style: const TextStyle(fontWeight: FontWeight.w500)),
                subtitle: Text(user.username),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: Icon(Icons.edit_outlined, color: Theme.of(context).colorScheme.primary),
                      tooltip: 'Edit User',
                      // Pass AppState to dialog method
                      onPressed: () => _editUser(context, appState, user),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                      tooltip: 'Delete User',
                      // Call AppState method directly
                      onPressed: () => _confirmDeleteUser(context, appState, user.id),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
     );
  }

  // --- Dialogs ---

  // Pass AppState to Add User Dialog
  void _showAddUserDialog(BuildContext context, AppState appState) {
    final formKey = GlobalKey<FormState>();
    TextEditingController nameController = TextEditingController();
    TextEditingController emailController = TextEditingController();
    TextEditingController passwordController = TextEditingController();
    String? selectedRole = 'Staff';

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
          title: Text("Add New User", style: TextStyle(color: Theme.of(context).colorScheme.primary, fontWeight: FontWeight.bold)),
          content: StatefulBuilder(
             builder: (BuildContext context, StateSetter setState) {
               return SingleChildScrollView(
                 child: Form(
                    key: formKey,
                    child: Column(
                       mainAxisSize: MainAxisSize.min,
                       children: [
                         _buildStyledTextField(context, nameController, "Name", validator: (val) => val!.isEmpty ? 'Name required' : null),
                         const SizedBox(height: 10),
                         _buildStyledTextField(context, emailController, "Email", keyboardType: TextInputType.emailAddress, validator: (val) => val!.isEmpty || !val.contains('@') ? 'Valid email required' : null),
                         const SizedBox(height: 10),
                         _buildStyledTextField(context, passwordController, "Password", obscureText: true, validator: (val) => val!.length < 6 ? 'Password min 6 chars' : null),
                         const SizedBox(height: 10),
                         DropdownButtonFormField<String>(
                            value: selectedRole,
                            items: ['Admin', 'Security', 'Staff']
                               .map((role) => DropdownMenuItem(value: role, child: Text(role)))
                               .toList(),
                            onChanged: (value) => setState(() => selectedRole = value),
                            decoration: _getStyledInputDecoration(context, 'Role'),
                            validator: (value) => value == null ? 'Role required' : null,
                         ),
                       ],
                     ),
                 ),
               );
             },
          ),
          actions: _buildDialogActions(context, () async { // Make async
            if (formKey.currentState!.validate()) {
               // Store scaffold messenger before async gap
               final scaffoldMessenger = ScaffoldMessenger.of(context);
               final navigator = Navigator.of(context);

               // ✅ Call AppState method
               bool success = await appState.createManagedUser(
                 name: nameController.text,
                 email: emailController.text,
                 password: passwordController.text,
                 role: selectedRole!,
               );
               if (mounted && success) {
                  navigator.pop();
                  // Optional: Show success snackbar
                  scaffoldMessenger.showSnackBar(const SnackBar(content: Text('User created successfully'), backgroundColor: Colors.green));
               } else if (mounted) {
                 // Error message should be available via appState.userManagementError
                  scaffoldMessenger.showSnackBar(SnackBar(content: Text(appState.userManagementError ?? 'Failed to create user'), backgroundColor: Colors.red));
               }
            }
          }),
        );
      },
    );
  }

  // Pass AppState and User object to Edit Dialog
  void _editUser(BuildContext context, AppState appState, User user) {
    final formKey = GlobalKey<FormState>();
    TextEditingController nameController = TextEditingController(text: user.username);
    TextEditingController emailController = TextEditingController(text: user.username);
    String? selectedRole = user.role;

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
          title: Text("Edit User: ${user.username}", style: TextStyle(color: Theme.of(context).colorScheme.primary, fontWeight: FontWeight.bold, fontSize: 18)),
          content: StatefulBuilder(
            builder: (BuildContext context, StateSetter setState) {
              return SingleChildScrollView(
                child: Form(
                   key: formKey,
                   child: Column(
                     mainAxisSize: MainAxisSize.min,
                     children: [
                       _buildStyledTextField(context, nameController, "Name", validator: (val) => val!.isEmpty ? 'Name required' : null),
                       const SizedBox(height: 10),
                       _buildStyledTextField(context, emailController, "Email", keyboardType: TextInputType.emailAddress, validator: (val) => val!.isEmpty || !val.contains('@') ? 'Valid email required' : null),
                       const SizedBox(height: 10),
                       DropdownButtonFormField<String>(
                         value: selectedRole,
                         items: ['Admin', 'Security', 'Staff', 'User']
                            .map((role) => DropdownMenuItem(value: role, child: Text(role)))
                            .toList(),
                         onChanged: (value) => setState(() => selectedRole = value),
                         decoration: _getStyledInputDecoration(context, 'Role'),
                         validator: (value) => value == null ? 'Role required' : null,
                       ),
                     ],
                   ),
                ),
              );
            }
          ),
          actions: _buildDialogActions(context, () async { // Make async
            if (formKey.currentState!.validate()) {
              // Store scaffold messenger before async gap
              final scaffoldMessenger = ScaffoldMessenger.of(context);
              final navigator = Navigator.of(context);

              // Call AppState's updateManagedUser method
              bool success = await appState.updateManagedUser(
                id: user.id,
                name: nameController.text,
                email: emailController.text,
                role: selectedRole!,
                // password: newPasswordController.text, // Add if password change is implemented
              );
              // print("Update user not implemented yet in AppState"); // Placeholder
              // bool success = false; // Assume failure for now

              if (mounted && success) {
                 navigator.pop();
                 scaffoldMessenger.showSnackBar(const SnackBar(content: Text('User updated successfully'), backgroundColor: Colors.green));
              } else if (mounted) {
                // Error should be available via appState.userManagementError
                 scaffoldMessenger.showSnackBar(SnackBar(content: Text(appState.userManagementError ?? 'Failed to update user (not implemented)'), backgroundColor: Colors.red));
              }
            }
          }),
        );
      },
    );
  }

  // Pass AppState and user ID to confirmation dialog
  void _confirmDeleteUser(BuildContext context, AppState appState, int userId) {
    // Store scaffold messenger before async gap
    final scaffoldMessenger = ScaffoldMessenger.of(context);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Deletion'),
        content: const Text('Are you sure you want to delete this user? This action cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('Cancel')),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            onPressed: () async {
               final navigator = Navigator.of(context);
               navigator.pop(); // Close confirmation dialog first

               // Call AppState method
               bool success = await appState.deleteManagedUser(userId);

               if (mounted && success) {
                 // Optional: Show success snackbar
                 scaffoldMessenger.showSnackBar(const SnackBar(content: Text('User deleted successfully'), backgroundColor: Colors.green));
               } else if (mounted) {
                  // Error message should be available via appState.userManagementError
                  scaffoldMessenger.showSnackBar(SnackBar(content: Text(appState.userManagementError ?? 'Failed to delete user'), backgroundColor: Colors.red));
               }
            },
            child: const Text('Delete', style: TextStyle(color: Colors.red, fontSize: 16)),
          ),
        ],
      ),
    );
  }

  // --- UI Helpers ---

  Widget _buildStyledTextField(BuildContext context, TextEditingController controller, String label, {
    bool obscureText = false,
    TextInputType keyboardType = TextInputType.text,
    String? Function(String?)? validator
  }) {
    return TextFormField(
      controller: controller,
      obscureText: obscureText,
      keyboardType: keyboardType,
      decoration: _getStyledInputDecoration(context, label),
      validator: validator,
    );
  }

  InputDecoration _getStyledInputDecoration(BuildContext context, String label) {
    return InputDecoration(
      labelText: label,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: BorderSide(color: Theme.of(context).colorScheme.primary, width: 2),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
    );
  }

  List<Widget> _buildDialogActions(BuildContext context, VoidCallback onConfirm) {
    return [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: Text("Cancel", style: TextStyle(color: Theme.of(context).colorScheme.secondary, fontSize: 16)),
      ),
      ElevatedButton(
        onPressed: onConfirm,
        style: ElevatedButton.styleFrom(
           backgroundColor: Theme.of(context).colorScheme.primary,
           foregroundColor: Colors.white,
        ),
        child: const Text("Confirm", style: TextStyle(fontSize: 16)),
      ),
    ];
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../models/user.dart'; // Assuming User model path is correct

class AddEditUserPage extends StatefulWidget {
  final User? user; // User to edit, null if adding

  const AddEditUserPage({super.key, this.user});

  @override
  AddEditUserPageState createState() => AddEditUserPageState();
}

class AddEditUserPageState extends State<AddEditUserPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  String _selectedRole = 'User'; // Default role

  bool get _isEditing => widget.user != null;

  @override
  void initState() {
    super.initState();

    final user = widget.user;
    _nameController.text = user?.username ?? '';
    _emailController.text = user?.email ?? '';
    _passwordController.text = ''; // Password always starts empty for editing
    _selectedRole = user?.role ?? 'User'; // Default to 'User' if adding

    // Fetch available roles
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<AppState>(context, listen: false).fetchAvailableRoles();
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submitForm() async {
    final appState = Provider.of<AppState>(context, listen: false);
    // Correctly access AppState loading properties using getters
    if (appState.isLoadingUsers || appState.isCreatingUser || appState.isUpdatingUser) {
      return; // Don't submit if already busy
    }

    if (!_formKey.currentState!.validate()) {
      return; // Don't submit if validation fails
    }

    final name = _nameController.text;
    final email = _emailController.text;
    final password = _passwordController.text;
    final role = _selectedRole;

    bool success = false;
    String? errorMessage;

    try {
      if (widget.user != null) {
        // Editing existing user
        // updateManagedUser expects ID first, then named args
        success = await appState.updateManagedUser(
          id: widget.user!.id,
          name: name,
          email: email,
          role: role,
        );
        errorMessage = appState.userManagementError;
      } else {
        // Adding new user - use named arguments
        success = await appState.createManagedUser(
          name: name,
          email: email,
          password: password,
          role: role
        );
        errorMessage = appState.userManagementError;
      }

       if (mounted) {
           final message = success
               ? (_isEditing ? 'User updated successfully.' : 'User created successfully.')
               : (errorMessage ?? (_isEditing ? 'Failed to update user.' : 'Failed to create user.'));
           final color = success ? Colors.green : Colors.red;

          ScaffoldMessenger.of(context).showSnackBar(
             SnackBar(content: Text(message), backgroundColor: color),
          );

          if (success) {
             Navigator.of(context).pop(); // Go back to user list on success
          }
          // Clear error from app state if shown
          if (!success) appState.clearUserManagementError();
       }

    } catch (e) {
        if (mounted) {
           ScaffoldMessenger.of(context).showSnackBar(
             SnackBar(content: Text('An error occurred: ${e.toString()}'), backgroundColor: Colors.red),
           );
        }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = context.select((AppState state) => state.isLoadingUsers);
    final availableRoles = context.select((AppState state) => state.availableRoles);

    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? 'Edit User' : 'Add New User'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              // --- Username ---
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Username',
                  prefixIcon: Icon(Icons.person_outline),
                  border: OutlineInputBorder(),
                ),
                 // Username might not be editable for existing users
                 readOnly: _isEditing,
                 style: _isEditing ? const TextStyle(color: Colors.grey) : null,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter a username';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16.0),

              // --- Email ---
              TextFormField(
                controller: _emailController,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  prefixIcon: Icon(Icons.email_outlined),
                   border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.emailAddress,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter an email address';
                  }
                  if (!RegExp(r"^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\.[a-zA-Z]+").hasMatch(value)) {
                     return 'Please enter a valid email address';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16.0),

              // --- Password ---
               TextFormField(
                 controller: _passwordController,
                 decoration: InputDecoration(
                   labelText: _isEditing ? 'New Password (Optional)' : 'Password',
                   prefixIcon: const Icon(Icons.lock_outline),
                   border: const OutlineInputBorder(),
                 ),
                 obscureText: true,
                 validator: (value) {
                   // Password is required only when creating a user
                   if (!_isEditing && (value == null || value.isEmpty)) {
                     return 'Please enter a password';
                   }
                   // Optional: Add password strength validation
                   if (value != null && value.isNotEmpty && value.length < 6) {
                      return 'Password must be at least 6 characters';
                   }
                   return null;
                 },
               ),
               const SizedBox(height: 16.0),

               // --- Role Selection ---
               DropdownButtonFormField<String>(
                 value: _selectedRole,
                 decoration: const InputDecoration(
                   labelText: 'Role',
                   prefixIcon: Icon(Icons.badge_outlined),
                   border: OutlineInputBorder(),
                 ),
                 items: availableRoles
                     .map<DropdownMenuItem<String>>((String value) {
                   return DropdownMenuItem<String>(
                     value: value,
                     child: Text(value),
                   );
                 }).toList(),
                 onChanged: (String? newValue) {
                   if (newValue != null) {
                     setState(() {
                       _selectedRole = newValue;
                     });
                   }
                 },
                  validator: (value) => value == null ? 'Please select a role' : null,
               ),
               const SizedBox(height: 16.0),

              // --- Submit Button ---
              ElevatedButton.icon(
                icon: Icon(isLoading ? Icons.hourglass_empty : (_isEditing ? Icons.save_outlined : Icons.add_circle_outline)),
                label: Text(isLoading ? 'Processing...' : (_isEditing ? 'Save Changes' : 'Create User')),
                style: ElevatedButton.styleFrom(
                   minimumSize: const Size(double.infinity, 50),
                   textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                onPressed: isLoading ? null : _submitForm,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
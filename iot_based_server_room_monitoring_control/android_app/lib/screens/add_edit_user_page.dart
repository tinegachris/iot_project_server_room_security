import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../models/User.dart'; // Assuming User model path is correct

class AddEditUserPage extends StatefulWidget {
  final User? userToEdit; // Pass user data if editing, null if adding

  const AddEditUserPage({super.key, this.userToEdit});

  @override
  State<AddEditUserPage> createState() => _AddEditUserPageState();
}

class _AddEditUserPageState extends State<AddEditUserPage> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _usernameController;
  late TextEditingController _emailController;
  late TextEditingController _passwordController;
  late String _selectedRole; // Manage role selection
  late bool _isAdmin; // Manage admin status

  bool get _isEditing => widget.userToEdit != null;

  @override
  void initState() {
    super.initState();

    final user = widget.userToEdit;
    _usernameController = TextEditingController(text: user?.username ?? '');
    _emailController = TextEditingController(text: user?.email ?? '');
    _passwordController = TextEditingController(); // Password always starts empty
    _selectedRole = user?.role ?? 'user'; // Default to 'user' if adding
    _isAdmin = user?.role == 'admin'; // Derive from role, assuming admin role implies is_admin flag

    // TODO: Get available roles dynamically if needed, instead of hardcoding
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) {
      return; // Don't submit if validation fails
    }

    final appState = Provider.of<AppState>(context, listen: false);
    bool success = false;
    String? errorMessage;

    try {
      if (_isEditing) {
        // --- Update Logic ---
        print("Attempting to update user ID: ${widget.userToEdit!.id}");
        // TODO: Implement update user logic in AppState/ApiService
        // success = await appState.updateManagedUser(
        //   id: widget.userToEdit!.id,
        //   name: _usernameController.text, // Assuming username acts as name here?
        //   email: _emailController.text,
        //   role: _selectedRole,
        //   // Password update might be separate or handled here if provided
        //   // password: _passwordController.text.isNotEmpty ? _passwordController.text : null,
        // );
         success = false; // Placeholder
         errorMessage = "Update functionality not fully implemented yet.";

      } else {
        // --- Create Logic ---
         print("Attempting to create user: ${_usernameController.text}");
         success = await appState.createManagedUser(
           // Assuming username doubles as name for now, adjust if separate name field needed
           name: _usernameController.text, 
           email: _emailController.text,
           password: _passwordController.text, // Password required for creation
           role: _selectedRole,
           // is_admin is potentially derived from role on server? Or pass explicitly?
           // isAdmin: _isAdmin, 
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
    // Use a Consumer to react to loading state changes if you add specific loading flags
    // final isLoading = context.select((AppState state) => _isEditing ? state.isUpdatingUser : state.isCreatingUser);
    final isLoading = context.select((AppState state) => state.isLoadingUsers); // Use general user loading for now

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
                controller: _usernameController,
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
                 // TODO: Get roles from a central config or API if possible
                 items: <String>['user', 'admin', 'it_staff', 'maintenance'] 
                     .map<DropdownMenuItem<String>>((String value) {
                   return DropdownMenuItem<String>(
                     value: value,
                     child: Text(value.replaceAll('_', ' ').toUpperCase()), // Format role name
                   );
                 }).toList(),
                 onChanged: (String? newValue) {
                   if (newValue != null) {
                     setState(() {
                       _selectedRole = newValue;
                       _isAdmin = newValue == 'admin'; // Update admin flag based on role
                     });
                   }
                 },
                  validator: (value) => value == null ? 'Please select a role' : null,
               ),
               const SizedBox(height: 16.0),

                // --- Is Admin (Consider if needed or derived from Role) ---
               // CheckboxListTile(
               //   title: const Text("Administrator Privileges"),
               //   value: _isAdmin,
               //   onChanged: (bool? value) {
               //     setState(() {
               //       _isAdmin = value ?? false;
               //       // If setting admin, maybe force role to 'admin'?
               //       if (_isAdmin) _selectedRole = 'admin';
               //     });
               //   },
               //   controlAffinity: ListTileControlAffinity.leading,
               // ),
               // const SizedBox(height: 24.0),

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
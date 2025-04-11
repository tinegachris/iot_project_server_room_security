import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/app_state.dart';

class LoginRegisterScreen extends StatefulWidget {
  const LoginRegisterScreen({super.key});

  @override
  State<LoginRegisterScreen> createState() => _LoginRegisterScreenState();
}

class _LoginRegisterScreenState extends State<LoginRegisterScreen> {
  bool isRegistering = false;
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _nameController = TextEditingController();

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    final appState = Provider.of<AppState>(context, listen: false);
    await appState.login(_emailController.text, _passwordController.text);
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;

    final appState = Provider.of<AppState>(context, listen: false);
    final bool success = await appState.register(
      name: _nameController.text,
      email: _emailController.text,
      password: _passwordController.text,
      role: "User",
    );

    if (mounted) {
       final message = appState.registrationMessage ?? (success ? "Registration successful!" : "Registration failed.");
       final color = success ? Colors.green : Colors.red;
       ScaffoldMessenger.of(context).showSnackBar(
         SnackBar(content: Text(message), backgroundColor: color),
       );
       if (success) {
          setState(() {
             isRegistering = false;
          });
       }
       appState.clearRegistrationMessage();
    }

    _passwordController.clear();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final isLoading = appState.isLoggingIn || appState.isRegistering;
    final errorMessage = isRegistering ? appState.registrationMessage : appState.loginError;

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0F172A), Color(0xFF1E40AF)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Icon(Icons.security_rounded, size: 80, color: Colors.white),
                    const SizedBox(height: 24),
                    Text(
                      isRegistering ? 'Register' : 'Login',
                      style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Colors.white),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    if (isRegistering) _buildTextField(_nameController, 'Name', Icons.person),
                    _buildTextField(_emailController, isRegistering ? 'Email' : 'Username', isRegistering ? Icons.email : Icons.person),
                    _buildTextField(_passwordController, 'Password', Icons.lock, isPassword: true),
                    const SizedBox(height: 24),
                    if (errorMessage != null && !isLoading)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 10.0),
                        child: Text(
                          errorMessage,
                          style: TextStyle(color: (isRegistering && errorMessage.contains("Successful")) ? Colors.greenAccent : Colors.redAccent, fontSize: 14),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ElevatedButton(
                      onPressed: isLoading ? null : (isRegistering ? _handleRegister : _handleLogin),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: const Color(0xFF1E40AF),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: isLoading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF1E40AF)))
                            )
                          : Text(isRegistering ? 'Register' : 'Login', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    ),
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: () => setState(() {
                        isRegistering = !isRegistering;
                        if (isRegistering) {
                          Provider.of<AppState>(context, listen: false).clearLoginError();
                        } else {
                           Provider.of<AppState>(context, listen: false).clearRegistrationMessage();
                        }
                      }),
                      child: Text(
                        isRegistering ? 'Already have an account? Login' : "Don't have an account? Register",
                        style: const TextStyle(color: Colors.white70, fontSize: 16),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(TextEditingController controller, String label, IconData icon, {bool isPassword = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: TextFormField(
        controller: controller,
        obscureText: isPassword,
        decoration: InputDecoration(
          filled: true,
          fillColor: const Color.fromRGBO(255, 255, 255, 0.1),
          labelText: label,
          labelStyle: const TextStyle(color: Colors.white),
          prefixIcon: Icon(icon, color: Colors.white),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
          errorStyle: TextStyle(color: Colors.redAccent[100]),
        ),
        style: const TextStyle(color: Colors.white),
        validator: (value) {
          if (value == null || value.isEmpty) {
            return 'Please enter your $label';
          }
          // Only validate email format if in registration mode or if explicitly labeled as email-only
          if (isRegistering && label.toLowerCase().contains('email') && !RegExp(r"^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\.[a-zA-Z]+").hasMatch(value)) {
             return 'Please enter a valid email';
          }
          return null;
        },
      ),
    );
  }
}

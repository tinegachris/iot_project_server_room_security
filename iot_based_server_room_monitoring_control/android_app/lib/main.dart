import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/app_state.dart';
import 'screens/dashboard/dashboard_screen.dart';
import 'screens/login and signup/login_and_register.dart';

void main() async {
  // Ensure Flutter bindings are initialized
  WidgetsFlutterBinding.ensureInitialized();

  // Create AppState instance *before* runApp
  final appState = AppState();

  // Attempt auto-login
  await appState.tryAutoLogin();

  // Pass the *same* AppState instance to the provider
  runApp(MyApp(appState: appState));
}

class MyApp extends StatelessWidget {
  // Receive the AppState instance
  final AppState appState;
  const MyApp({super.key, required this.appState});

  @override
  Widget build(BuildContext context) {
    // Use ChangeNotifierProvider.value for existing instance
    return ChangeNotifierProvider.value(
      value: appState,
      child: Consumer<AppState>( // Use Consumer to react to AppState changes
        builder: (context, appState, child) {
          return MaterialApp(
            title: 'Server Room Security',
            theme: ThemeData(
              colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
              useMaterial3: true,
            ),
            // Show splash screen while initializing, then route based on auth
            home: appState.isInitializing
                ? const SplashScreen() // Show splash/loading screen
                : appState.isAuthenticated
                    ? DashboardScreen(role: appState.currentUser?.role ?? 'guest') // Go to dashboard
                    : const LoginRegisterScreen(), // Go to login
            routes: {
              // Define routes primarily for named navigation *after* initial load
              '/login': (context) => const LoginRegisterScreen(),
              '/dashboard': (context) {
                final role = Provider.of<AppState>(context, listen: false).currentUser?.role ?? 'guest';
                return DashboardScreen(role: role);
              },
            },
          );
        },
      ),
    );
  }
}

// Simple Placeholder Splash Screen
class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 20),
            Text("Initializing..."),
          ],
        ),
      ),
    );
  }
}

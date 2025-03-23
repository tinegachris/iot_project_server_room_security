import 'package:flutter/material.dart';
import 'package:security_iot/screens/login%20and%20signup/login_and_registration.dart';
import 'package:security_iot/screens/onboarding/onboarding_screen.dart';

void main() {
  runApp(SecurityApp());
}

class SecurityApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Security Device Management',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: OnboardingScreen(),
      routes: {
        '/login': (context) => LoginScreen(),
        '/home': (context) => HomeScreen(),
      },
    );
  }
}



class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}


class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  String _role = 'Admin';

  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)?.settings.arguments as String?;
    if (args != null) _role = args;

    final List<Widget> _pages = [
      DevicesScreen(role: _role),
      NotificationsScreen(),
      ProfileScreen(),
    ];

    return Scaffold(
      appBar: AppBar(title: Text('Dashboard ($_role)')),
      body: _pages[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: [
          BottomNavigationBarItem(icon: Icon(Icons.devices), label: 'Devices'),
          BottomNavigationBarItem(icon: Icon(Icons.notifications), label: 'Notifications'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}

class DevicesScreen extends StatelessWidget {
  final String role;
  DevicesScreen({required this.role});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text('Devices Screen - Role: $role'),
    );
  }
}

class NotificationsScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text('Notifications Screen'),
    );
  }
}

class ProfileScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text('Profile Screen'),
    );
  }
}

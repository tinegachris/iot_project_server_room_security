import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:security_iot/providers/app_state.dart';
import 'package:security_iot/screens/home_screen.dart';
import 'package:security_iot/screens/login_screen.dart';
import 'package:security_iot/screens/onboarding_screen.dart';
import 'package:security_iot/screens/logs_screen.dart';
import 'package:security_iot/screens/controls_screen.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (_) => AppState(),
      child: SecurityApp(),
    ),
  );
}

class SecurityApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Server Room Security',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        brightness: Brightness.light,
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
      ),
      home: OnboardingScreen(),
      routes: {
        '/login': (context) => LoginScreen(),
        '/home': (context) => HomeScreen(),
        '/logs': (context) => LogsScreen(),
        '/controls': (context) => ControlsScreen(),
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
      DashboardScreen(role: _role),
      LogsScreen(),
      ControlsScreen(),
      ProfileScreen(),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text('Dashboard ($_role)'),
        actions: [
          IconButton(
            icon: Icon(Icons.notifications),
            onPressed: () {
              // TODO: Show notifications
            },
          ),
        ],
      ),
      body: _pages[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        type: BottomNavigationBarType.fixed,
        items: [
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.history),
            label: 'Logs',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.control_point),
            label: 'Controls',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}

class DashboardScreen extends StatelessWidget {
  final String role;
  DashboardScreen({required this.role});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        final status = appState.systemStatus;
        if (status == null) {
          return Center(child: CircularProgressIndicator());
        }

        return SingleChildScrollView(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildStatusCard(status),
              SizedBox(height: 16),
              _buildSensorsGrid(status),
              SizedBox(height: 16),
              _buildAlertsList(appState.alerts),
            ],
          ),
        );
      },
    );
  }

  Widget _buildStatusCard(SystemStatus status) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'System Status',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Health: ${status.health}'),
                Text('Storage: ${status.storage['free']}GB free'),
                Text('Uptime: ${status.uptime}'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSensorsGrid(SystemStatus status) {
    return GridView.builder(
      shrinkWrap: true,
      physics: NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 1.5,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
      ),
      itemCount: status.sensors.length,
      itemBuilder: (context, index) {
        final sensor = status.sensors[index];
        return Card(
          child: Padding(
            padding: EdgeInsets.all(8),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  _getSensorIcon(sensor.type),
                  size: 32,
                  color: sensor.isActive ? Colors.green : Colors.red,
                ),
                SizedBox(height: 8),
                Text(
                  sensor.name,
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                Text(
                  sensor.isActive ? 'Active' : 'Inactive',
                  style: TextStyle(
                    color: sensor.isActive ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildAlertsList(List<Alert> alerts) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Recent Alerts',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 8),
            if (alerts.isEmpty)
              Text('No recent alerts')
            else
              ListView.builder(
                shrinkWrap: true,
                physics: NeverScrollableScrollPhysics(),
                itemCount: alerts.length,
                itemBuilder: (context, index) {
                  final alert = alerts[index];
                  return ListTile(
                    leading: Icon(
                      _getAlertIcon(alert.severity),
                      color: _getAlertColor(alert.severity),
                    ),
                    title: Text(alert.message),
                    subtitle: Text(
                      alert.eventTimestamp.toString(),
                      style: TextStyle(fontSize: 12),
                    ),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }

  IconData _getSensorIcon(String? type) {
    switch (type?.toLowerCase()) {
      case 'motion':
        return Icons.motion_photos_on;
      case 'door':
        return Icons.door_front_door;
      case 'window':
        return Icons.window;
      case 'rfid':
        return Icons.credit_card;
      case 'camera':
        return Icons.videocam;
      default:
        return Icons.sensors;
    }
  }

  IconData _getAlertIcon(String severity) {
    switch (severity.toLowerCase()) {
      case 'critical':
        return Icons.error;
      case 'high':
        return Icons.warning;
      case 'medium':
        return Icons.info;
      case 'low':
        return Icons.notifications;
      default:
        return Icons.notifications;
    }
  }

  Color _getAlertColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'critical':
        return Colors.red;
      case 'high':
        return Colors.orange;
      case 'medium':
        return Colors.yellow;
      case 'low':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }
}

class ProfileScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircleAvatar(
            radius: 50,
            child: Icon(Icons.person, size: 50),
          ),
          SizedBox(height: 16),
          Text(
            'User Profile',
            style: TextStyle(fontSize: 24),
          ),
          SizedBox(height: 8),
          Text('Role: Admin'),
          SizedBox(height: 16),
          ElevatedButton(
            onPressed: () {
              // TODO: Implement logout
              Navigator.pushReplacementNamed(context, '/login');
            },
            child: Text('Logout'),
          ),
        ],
      ),
    );
  }
}

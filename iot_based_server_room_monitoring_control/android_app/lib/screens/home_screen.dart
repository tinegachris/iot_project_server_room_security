import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../models/system_status.dart';
import 'package:intl/intl.dart';
import 'logs_screen.dart';
import 'controls_screen.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  final _dateFormat = DateFormat('MMM d, y HH:mm');

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().fetchSystemStatus();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Server Room Security'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: () {
              context.read<AppState>().fetchSystemStatus();
            },
          ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: [
          _buildDashboard(),
          LogsScreen(),
          ControlsScreen(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
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
            icon: Icon(Icons.settings),
            label: 'Controls',
          ),
        ],
      ),
    );
  }

  Widget _buildDashboard() {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        if (appState.isLoading) {
          return Center(child: CircularProgressIndicator());
        }

        if (appState.error != null) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text('Error: ${appState.error}'),
                ElevatedButton(
                  onPressed: () {
                    context.read<AppState>().fetchSystemStatus();
                  },
                  child: Text('Retry'),
                ),
              ],
            ),
          );
        }

        final status = appState.systemStatus;
        if (status == null) {
          return Center(child: Text('No data available'));
        }

        return _buildStatusView(status);
      },
    );
  }

  Widget _buildStatusView(SystemStatus status) {
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildStatusCard(status),
          SizedBox(height: 16),
          _buildSensorsCard(status.systemHealth.sensors),
          SizedBox(height: 16),
          _buildStorageCard(status.systemHealth.storage),
          SizedBox(height: 16),
          _buildSystemInfoCard(status.systemHealth),
        ],
      ),
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
              style: Theme.of(context).textTheme.titleLarge,
            ),
            SizedBox(height: 8),
            Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: status.status == 'normal' ? Colors.green : Colors.red,
                  ),
                ),
                SizedBox(width: 8),
                Text(
                  status.status.toUpperCase(),
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: status.status == 'normal' ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ),
            SizedBox(height: 8),
            Text(
              'Last Updated: ${_dateFormat.format(status.timestamp)}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSensorsCard(Map<String, String> sensors) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Sensors Status',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            SizedBox(height: 8),
            ...sensors.entries.map((sensor) => Padding(
              padding: EdgeInsets.symmetric(vertical: 4),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(sensor.key.toUpperCase()),
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: sensor.value == 'active' ? Colors.green : Colors.red,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      sensor.value.toUpperCase(),
                      style: TextStyle(color: Colors.white),
                    ),
                  ),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildStorageCard(StorageInfo storage) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Storage Status',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            SizedBox(height: 8),
            _buildStorageRow('Total', storage.total),
            _buildStorageRow('Used', storage.used),
            _buildStorageRow('Free', storage.free),
          ],
        ),
      ),
    );
  }

  Widget _buildStorageRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(value),
        ],
      ),
    );
  }

  Widget _buildSystemInfoCard(SystemHealth health) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'System Information',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            SizedBox(height: 8),
            _buildInfoRow('Uptime', health.uptime),
            _buildInfoRow(
              'Last Maintenance',
              _dateFormat.format(health.lastMaintenance),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(value),
        ],
      ),
    );
  }
} 
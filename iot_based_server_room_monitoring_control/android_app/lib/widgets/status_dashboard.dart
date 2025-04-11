import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart'; // For date formatting

import '../providers/app_state.dart';
import '../models/system_status.dart';

class StatusDashboard extends StatelessWidget {
  const StatusDashboard({super.key});

  // Helper to build status cards
  Widget _buildStatusCard(BuildContext context,
      {required String title,
      required String value,
      required IconData icon,
      Color iconColor = Colors.blue,
      String? subtitle}) {
    return Card(
      elevation: 2.0,
      margin: const EdgeInsets.symmetric(vertical: 6.0),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ListTile(
          leading: Icon(icon, size: 40.0, color: iconColor),
          title: Text(title, style: Theme.of(context).textTheme.titleMedium),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                value,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 4.0),
                Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
              ]
            ],
          ),
          contentPadding: EdgeInsets.zero,
        ),
      ),
    );
  }

  // Helper to get status color
  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'healthy':
        return Colors.green;
      case 'degraded':
      case 'warning':
        return Colors.orange;
      case 'error':
      case 'unhealthy':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    // Use Consumer to listen to AppState changes
    return Consumer<AppState>(
      builder: (context, appState, child) {
        final status = appState.currentStatus;
        final isLoading = appState.isFetchingStatus;
        final error = appState.statusError;

        if (isLoading && status == null) {
          return const Card(
             child: Padding(
                padding: EdgeInsets.all(20.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(strokeWidth: 2),
                    SizedBox(width: 16),
                    Text("Loading System Status..."),
                  ],
                ),
             ),
          );
        }

        // Display error directly within the widget if status is null
        if (error != null && status == null) {
          return Card(
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, color: Colors.red),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Text(
                      'Error: $error',
                      style: const TextStyle(color: Colors.red),
                    ),
                  ),
                ],
              ),
            ),
          );
        }
        
        if (status == null) {
           return const Center(child: Text('No system status available.'));
        }

        // Format last heartbeat time
        String lastHeartbeatFormatted = "N/A";
          try {
            lastHeartbeatFormatted = DateFormat('yyyy-MM-dd HH:mm:ss').format(status.raspberryPi.lastHeartbeat!);
          } catch (_) {
             lastHeartbeatFormatted = "Invalid Date"; // Handle parsing errors if any
          }
              
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildStatusCard(
              context,
              title: 'Overall System Status',
              value: status.status.toUpperCase(),
              icon: Icons.shield_outlined,
              iconColor: _getStatusColor(status.status),
            ),
            const SizedBox(height: 12.0),
             _buildStatusCard(
              context,
              title: 'Raspberry Pi',
              value: status.raspberryPi.isOnline ? 'Online' : 'Offline',
              icon: status.raspberryPi.isOnline ? Icons.lan_outlined : Icons.signal_wifi_off_outlined,
              iconColor: status.raspberryPi.isOnline ? Colors.green : Colors.red,
              subtitle: 'Last Heartbeat: $lastHeartbeatFormatted'
            ),
             const SizedBox(height: 12.0),
            _buildStatusCard(
              context,
              title: 'Storage',
              value: '${status.storage['free_gb'] ?? 'N/A'} GB Free',
              icon: status.storage['low_space'] == true ? Icons.disc_full_outlined : Icons.data_usage_outlined,
              iconColor: status.storage['low_space'] == true ? Colors.orange : Colors.blue,
               subtitle: '${status.storage['used_gb'] ?? 'N/A'} GB Used / ${status.storage['total_gb'] ?? 'N/A'} GB Total'
            ),
            const SizedBox(height: 16.0),
             // Display Sensor Status Overview (Example)
             _buildSensorOverview(context, status.sensors),
             const SizedBox(height: 16.0),
             // Display System Errors if any
             if (status.errors != null && status.errors!.isNotEmpty)
               _buildErrorList(context, status.errors!),
          ],
        );
      },
    );
  }

  // Helper Widget for Sensor Overview
  Widget _buildSensorOverview(BuildContext context, Map<String, SensorStatus> sensors) {
     final activeSensors = sensors.values.where((s) => s.isActive).length;
     final inactiveSensors = sensors.length - activeSensors;

     return Card(
       elevation: 2.0,
       margin: const EdgeInsets.symmetric(vertical: 6.0),
       shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
       child: Padding(
         padding: const EdgeInsets.all(16.0),
         child: Column(
           crossAxisAlignment: CrossAxisAlignment.start,
           children: [
              Text('Sensors Overview', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 16),
              Row(
                 mainAxisAlignment: MainAxisAlignment.spaceAround,
                 children: [
                   _buildSensorStat('Total', sensors.length.toString(), Icons.sensors),
                   _buildSensorStat('Active', activeSensors.toString(), Icons.check_circle_outline, Colors.green),
                   _buildSensorStat('Inactive', inactiveSensors.toString(), Icons.cancel_outlined, Colors.red),
                 ],
              ),
              // Optionally, add a button or expansion tile to show details per sensor
              // const SizedBox(height: 8),
              // TextButton(onPressed: () {}, child: const Text('View Sensor Details')),
           ],
         ),
       ),
     );
  }

  Widget _buildSensorStat(String label, String value, IconData icon, [Color color = Colors.blue]) {
    return Column(
      children: [
        Icon(icon, size: 30, color: color),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
    );
  }

  // Helper Widget for Error List
  Widget _buildErrorList(BuildContext context, List<String> errors) {
     return Card(
       elevation: 2.0,
       margin: const EdgeInsets.symmetric(vertical: 6.0),
       shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
       color: Colors.red[50], // Light red background for errors
       child: Padding(
         padding: const EdgeInsets.all(16.0),
         child: Column(
           crossAxisAlignment: CrossAxisAlignment.start,
           children: [
             Row(
                children: [
                  Icon(Icons.error_outline, color: Colors.red[700]),
                  const SizedBox(width: 8),
                  Text('System Errors', style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.red[700])),
                ],
             ),
             const SizedBox(height: 12),
             ...errors.map((error) => Padding(
                padding: const EdgeInsets.only(bottom: 4.0),
                child: Text('- $error', style: TextStyle(color: Colors.red[900])),
             )),
           ],
         ),
       ),
     );
  }
} 
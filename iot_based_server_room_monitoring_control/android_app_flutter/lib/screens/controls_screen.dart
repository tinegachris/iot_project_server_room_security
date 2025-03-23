import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';

class ControlsScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Server Room Controls'),
      ),
      body: Consumer<AppState>(
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
                      // Retry last action
                    },
                    child: Text('Retry'),
                  ),
                ],
              ),
            );
          }

          return ListView(
            padding: EdgeInsets.all(16),
            children: [
              _buildControlCard(
                context,
                'Door Control',
                'Lock or unlock the server room door',
                [
                  _buildControlButton(
                    context,
                    'Lock Door',
                    Icons.lock,
                    Colors.red,
                    () => _executeCommand(context, 'lock'),
                  ),
                  _buildControlButton(
                    context,
                    'Unlock Door',
                    Icons.lock_open,
                    Colors.green,
                    () => _executeCommand(context, 'unlock'),
                  ),
                ],
              ),
              SizedBox(height: 16),
              _buildControlCard(
                context,
                'System Control',
                'Manage server room system functions',
                [
                  _buildControlButton(
                    context,
                    'Test Sensors',
                    Icons.sensors,
                    Colors.blue,
                    () => _executeCommand(context, 'test_sensors'),
                  ),
                  _buildControlButton(
                    context,
                    'Restart System',
                    Icons.restart_alt,
                    Colors.orange,
                    () => _showConfirmationDialog(
                      context,
                      'Restart System',
                      'Are you sure you want to restart the system? This action cannot be undone.',
                      () => _executeCommand(context, 'restart_system'),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 16),
              _buildControlCard(
                context,
                'Manual Alert',
                'Trigger a manual alert for the server room',
                [
                  _buildControlButton(
                    context,
                    'Create Alert',
                    Icons.warning,
                    Colors.red,
                    () => _showAlertDialog(context),
                  ),
                ],
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildControlCard(
    BuildContext context,
    String title,
    String description,
    List<Widget> buttons,
  ) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            SizedBox(height: 8),
            Text(
              description,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: buttons,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildControlButton(
    BuildContext context,
    String label,
    IconData icon,
    Color color,
    VoidCallback onPressed,
  ) {
    return ElevatedButton.icon(
      onPressed: onPressed,
      icon: Icon(icon),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
      ),
    );
  }

  Future<void> _executeCommand(BuildContext context, String action) async {
    try {
      await context.read<AppState>().executeControlCommand(action);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Command executed successfully'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to execute command: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _showConfirmationDialog(
    BuildContext context,
    String title,
    String message,
    VoidCallback onConfirm,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('Confirm'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      onConfirm();
    }
  }

  Future<void> _showAlertDialog(BuildContext context) async {
    final messageController = TextEditingController();

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Create Manual Alert'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: messageController,
              decoration: InputDecoration(
                labelText: 'Alert Message',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('Create Alert'),
          ),
        ],
      ),
    );

    if (result == true && messageController.text.isNotEmpty) {
      try {
        await context.read<AppState>().postAlert(
          message: messageController.text,
        );
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Alert created successfully'),
            backgroundColor: Colors.green,
          ),
        );
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to create alert: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }
} 
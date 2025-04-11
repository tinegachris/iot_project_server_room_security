import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../providers/app_state.dart';
import '../../../models/system_status.dart';

class ControlsScreen extends StatefulWidget {
  const ControlsScreen({super.key});

  @override
  State<ControlsScreen> createState() => _ControlsScreenState();
}

class _ControlsScreenState extends State<ControlsScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: Consumer<AppState>(
        builder: (context, appState, child) {
          final systemStatus = appState.currentStatus;
          final isLoading = appState.isFetchingStatus && systemStatus == null;
          final error = appState.statusError;

          if (isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (error != null && systemStatus == null) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      'Error loading controls status: $error',
                      style: TextStyle(color: Colors.red[700]),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 10),
                    ElevatedButton(
                      onPressed: () => Provider.of<AppState>(context, listen: false).fetchSystemStatus(),
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
            );
          }

          if (systemStatus == null) {
             return const Center(child: Text("Control status not available."));
          }

          final List<String> alerts = systemStatus.errors ?? [];

          return RefreshIndicator(
             onRefresh: () => Provider.of<AppState>(context, listen: false).fetchSystemStatus(),
             child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              children: [
                _buildStatusCard(context, systemStatus),
                const SizedBox(height: 16),
                _buildControlCard(
                  context,
                  'Door Control',
                  'Lock or unlock the server room door',
                  [
                    _buildControlButton(
                      context,
                      'Lock Door',
                      'lock',
                      Icons.lock_outline,
                      Colors.redAccent,
                      (appState.isExecutingControlCommand || _isDoorLocked(systemStatus))
                       ? null
                       : () => _executeCommand(context, 'lock'),
                    ),
                    _buildControlButton(
                      context,
                      'Unlock Door',
                      'unlock',
                      Icons.lock_open_outlined,
                      const Color(0xFF4CAF50),
                      (appState.isExecutingControlCommand || !_isDoorLocked(systemStatus))
                        ? null
                        : () => _executeCommand(context, 'unlock'),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _buildControlCard(
                  context,
                  'Window Control',
                  'Lock or unlock the server room window',
                  [
                    _buildControlButton(
                      context,
                      'Lock Window',
                      'lock_window',
                      Icons.window_outlined,
                      Colors.redAccent,
                      (appState.isExecutingControlCommand || _isWindowLocked(systemStatus))
                        ? null
                        : () => _executeCommand(context, 'lock_window'),
                    ),
                    _buildControlButton(
                      context,
                      'Unlock Window',
                      'unlock_window',
                      Icons.window,
                      const Color(0xFF4CAF50),
                      (appState.isExecutingControlCommand || !_isWindowLocked(systemStatus))
                         ? null
                         : () => _executeCommand(context, 'unlock_window'),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _buildControlCard(
                  context,
                  'System Control',
                  'Manage server room system functions',
                  [
                    _buildControlButton(
                      context,
                      'Test Sensors',
                      'test_sensors',
                      Icons.rule,
                      Colors.blueAccent,
                      appState.isExecutingControlCommand ? null : () => _executeCommand(context, 'test_sensors'),
                    ),
                    _buildControlButton(
                      context,
                      'Restart System',
                      'restart_system',
                      Icons.restart_alt,
                      Colors.orangeAccent,
                      appState.isExecutingControlCommand ? null : () => _showConfirmationDialog(
                        context,
                        'Restart System',
                        'Are you sure you want to restart the Pi system?',
                        () => _executeCommand(context, 'restart_system'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                _buildControlCard(
                  context,
                  'Manual Alert',
                  'Trigger a manual alert for the server room',
                  [
                    _buildControlButton(
                      context,
                      'Create Alert',
                      'manual_alert',
                      Icons.add_alert_outlined,
                      Colors.red,
                      appState.isExecutingControlCommand ? null : () => _showManualAlertDialog(context),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                if (alerts.isNotEmpty)
                  _buildAlertsCard(context, alerts),
              ],
            ),
          );
        },
      ),
    );
  }

  bool _isDoorLocked(SystemStatus status) {
    return status.sensors['door']?.data?['locked'] ?? false;
  }

  bool _isWindowLocked(SystemStatus status) {
    return status.sensors['window']?.data?['locked'] ?? false;
  }

  Widget _buildStatusCard(BuildContext context, SystemStatus status) {
    bool isDoorLocked = _isDoorLocked(status);
    bool isWindowLocked = _isWindowLocked(status);
    String systemHealth = status.status;

    return Card(
        color: Colors.white,
        elevation: 1.5,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        margin: const EdgeInsets.only(bottom: 16),
        child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Current Status', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            _buildStatusRow(
              icon: isDoorLocked ? Icons.lock : Icons.lock_open,
              label: 'Door',
              value: isDoorLocked ? 'Locked' : 'Unlocked',
              color: isDoorLocked ? Colors.red[400]! : Colors.green[400]!,
            ),
            const SizedBox(height: 8),
            _buildStatusRow(
              icon: isWindowLocked ? Icons.sensor_window : Icons.sensor_window_outlined,
              label: 'Window',
              value: isWindowLocked ? 'Locked' : 'Unlocked',
              color: isWindowLocked ? Colors.red[400]! : Colors.green[400]!,
            ),
            const SizedBox(height: 8),
            _buildStatusRow(
              icon: Icons.monitor_heart_outlined,
              label: 'System Health',
              value: systemHealth,
              color: _getStatusColor(context, systemHealth),
            ),
          ],
        ),
      ),
    );
  }

  Color _getStatusColor(BuildContext context, String status) {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'online':
        return Colors.green[400]!;
      case 'degraded':
      case 'warning':
        return Colors.orange[400]!;
      case 'error':
      case 'offline':
        return Colors.red[400]!;
      default:
        return Colors.grey[600]!;
    }
  }

  Widget _buildStatusRow({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Row(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(width: 10),
        Text(
          '$label: ',
          style: const TextStyle(fontWeight: FontWeight.w500),
        ),
        Expanded(
            child: Text(
              value,
              style: TextStyle(fontWeight: FontWeight.w600, color: color),
              overflow: TextOverflow.ellipsis,
            )
        ),
      ],
    );
  }

  Widget _buildAlertsCard(BuildContext context, List<String> alerts) {
    return Card(
      color: Colors.orange[50],
      elevation: 1.5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
                'System Alerts (${alerts.length})',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600, color: Colors.orange[800])
            ),
            const SizedBox(height: 10),
            if (alerts.isEmpty)
              const Text("No active alerts.")
            else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: alerts.length,
                itemBuilder: (context, index) {
                    final alert = alerts[index];
                    return Padding(
                       padding: const EdgeInsets.symmetric(vertical: 4.0),
                       child: Row(
                         crossAxisAlignment: CrossAxisAlignment.start,
                         children: [
                           Icon(Icons.warning_amber_rounded, color: Colors.orange[700], size: 18),
                           const SizedBox(width: 8),
                           Expanded(
                             child: Text(
                                alert,
                                style: TextStyle(color: Colors.orange[900], fontSize: 13),
                              ),
                           ),
                         ],
                       ),
                    );
                },
                separatorBuilder: (context, index) => const Divider(height: 8, thickness: 0.5),
              ),
          ],
        ),
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
      color: Colors.white,
      elevation: 1.5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            Text(description, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey[600])),
            const SizedBox(height: 16),
            Wrap(
              spacing: 12.0,
              runSpacing: 10.0,
              alignment: WrapAlignment.start,
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
    String action,
    IconData icon,
    Color color,
    VoidCallback? onPressed,
  ) {
    final appState = Provider.of<AppState>(context, listen: false);
    final bool isExecutingThisAction = appState.executingAction == action;

    return ElevatedButton.icon(
      icon: Icon(icon, size: 18),
      label: isExecutingThisAction
        ? const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)
          )
        : Text(label),
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
      ),
    );
  }

  Future<void> _executeCommand(BuildContext context, String command, [Map<String, dynamic>? data]) async {
    final appState = Provider.of<AppState>(context, listen: false);
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    try {
      await appState.executeControlCommand(command, data);
      if (!mounted) return;
      scaffoldMessenger.showSnackBar(
        SnackBar(
          content: Text(appState.controlCommandError ?? 'Command "$command" executed successfully!'),
          backgroundColor: appState.controlCommandError == null || appState.controlCommandError!.contains('success') ? Colors.green : Colors.orange,
        ),
      );
      appState.clearControlCommandError();
    } catch (e) {
      if (!mounted) return;
      scaffoldMessenger.showSnackBar(
        SnackBar(
          content: Text('Failed to execute "$command": ${appState.controlCommandError ?? e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _showConfirmationDialog(
    BuildContext context,
    String title,
    String content,
    VoidCallback onConfirm,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.of(context).pop(true), child: Text(title)),
        ],
      ),
    );
    if (confirmed == true) {
      onConfirm();
    }
  }

  Future<void> _showManualAlertDialog(BuildContext context) async {
    final TextEditingController alertController = TextEditingController();
    final appState = Provider.of<AppState>(context, listen: false);
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Create Manual Alert'),
        content: TextField(
          controller: alertController,
          decoration: const InputDecoration(hintText: 'Enter alert message', border: OutlineInputBorder()),
          autofocus: true,
          minLines: 1,
          maxLines: 3,
        ),
        actions: [
          TextButton(onPressed: () => navigator.pop(false), child: const Text('Cancel')),
          TextButton(
             onPressed: () {
               if (alertController.text.trim().isNotEmpty) {
                 navigator.pop(true);
               }
             },
             child: const Text('Send Alert'),
          ),
        ],
      ),
    );

    if (confirmed == true && alertController.text.trim().isNotEmpty) {
       final message = alertController.text.trim();
       await appState.postManualAlert(message);
       scaffoldMessenger.showSnackBar(
          SnackBar(
            content: Text(appState.controlCommandError ?? 'Alert posted!'),
            backgroundColor: appState.controlCommandError != null && !appState.controlCommandError!.contains('success') ? Colors.red : Colors.green,
          ),
       );
       appState.clearControlCommandError();
    } else {
      scaffoldMessenger.showSnackBar(
        SnackBar(
          content: Text(appState.controlCommandError ?? 'Failed to post alert'),
          backgroundColor: Colors.red,
        ),
      );
    }
    alertController.dispose();
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart'; // For date formatting

import '../providers/app_state.dart';
import '../models/log_entry.dart';

class LogsPage extends StatefulWidget {
  const LogsPage({super.key});

  @override
  State<LogsPage> createState() => _LogsPageState();
}

class _LogsPageState extends State<LogsPage> {
  String? _selectedSeverity;
  String? _selectedSource;
  DateTime? _startDate;
  DateTime? _endDate;

  @override
  void initState() {
    super.initState();
    // Fetch logs if they haven't been fetched recently or on initial load
    // Consider adding pagination logic here in the future
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final appState = Provider.of<AppState>(context, listen: false);
      // Fetch logs if the list is empty or maybe based on a timestamp
      if (appState.logs.isEmpty && !appState.isFetchingLogs) {
          appState.fetchLogs();
      }
    });
  }

   // Reusing helpers from LogViewer for consistency
   Color _getSeverityColor(String? severity) {
    switch (severity?.toLowerCase()) {
      case 'critical':
      case 'error':
        return Colors.red;
      case 'warning':
        return Colors.orange;
      case 'info':
         return Colors.blue;
      case 'debug':
         return Colors.grey;
      default:
        return Colors.black54;
    }
  }

  IconData _getLogIcon(LogEntry log) {
    switch (log.severity.toLowerCase()) {
      case 'critical':
      case 'error':
        return Icons.error_outline;
      case 'warning':
        return Icons.warning_amber_outlined;
    }
    switch (log.eventType) {
      case 'door_opened':
      case 'door_closed':
        return Icons.door_sliding_outlined;
       case 'window_opened':
      case 'window_closed':
         return Icons.window;
      case 'motion_detected':
         return Icons.directions_run;
       case 'unauthorized_access':
         return Icons.no_accounts_outlined;
       case 'authorized_access':
          return Icons.verified_user_outlined;
       case 'manual_alert':
          return Icons.campaign_outlined;
       case 'status_check':
           return Icons.fact_check_outlined;
       case 'image_capture':
           return Icons.camera_alt_outlined;
       case 'video_record':
           return Icons.videocam_outlined;
       case 'system_info':
           return Icons.info_outline;
       default:
         return Icons.article_outlined;
    }
  }

  void _showFilterDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Filter Logs'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: _selectedSeverity,
                decoration: const InputDecoration(labelText: 'Severity'),
                items: ['All', 'Critical', 'Error', 'Warning', 'Info', 'Debug']
                    .map((String value) => DropdownMenuItem<String>(
                          value: value == 'All' ? null : value.toLowerCase(),
                          child: Text(value),
                        ))
                    .toList(),
                onChanged: (value) => setState(() => _selectedSeverity = value),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _selectedSource,
                decoration: const InputDecoration(labelText: 'Source'),
                items: ['All', 'System', 'Camera', 'Door', 'Window', 'Motion', 'RFID']
                    .map((String value) => DropdownMenuItem<String>(
                          value: value == 'All' ? null : value.toLowerCase(),
                          child: Text(value),
                        ))
                    .toList(),
                onChanged: (value) => setState(() => _selectedSource = value),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              setState(() {
                _selectedSeverity = null;
                _selectedSource = null;
              });
              Navigator.pop(context);
            },
            child: const Text('Clear'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Apply'),
          ),
        ],
      ),
    );
  }

  List<LogEntry> _filterLogs(List<LogEntry> logs) {
    return logs.where((log) {
      if (_selectedSeverity != null && log.severity != _selectedSeverity) {
        return false;
      }
      if (_selectedSource != null && log.source != _selectedSource) {
        return false;
      }
      if (_startDate != null && log.timestamp.isBefore(_startDate!)) {
        return false;
      }
      if (_endDate != null && log.timestamp.isAfter(_endDate!)) {
        return false;
      }
      return true;
    }).toList();
  }

  void _showLogDetailsDialog(BuildContext context, LogEntry log) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Log Details - ${log.eventType}'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('Time: ${DateFormat('yyyy-MM-dd HH:mm:ss').format(log.timestamp)}'),
              const SizedBox(height: 8),
              Text('Severity: ${log.severity}'),
              const SizedBox(height: 8),
              Text('Source: ${log.source}'),
              if (log.userId != null) ...[
                const SizedBox(height: 8),
                Text('User ID: ${log.userId}'),
              ],
              const SizedBox(height: 16),
              Text('Details:', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              Text(log.details.toString()),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Activity Logs'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
          ),
        ],
      ),
      body: Consumer<AppState>(
        builder: (context, appState, child) {
          final logs = _filterLogs(appState.logs);
          final isLoading = appState.isFetchingLogs;
          final error = appState.logsError;

          // Show loading indicator centrally while fetching initial logs
          if (isLoading && logs.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          // Show error message centrally if fetching failed and no logs are loaded
           if (error != null && logs.isEmpty) {
            // Display error inline, allowing for refresh
            return RefreshIndicator(
               onRefresh: () => appState.fetchLogs(),
               child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Center( // Center the error message
                    child: Text(
                      'Error loading logs: $error\nPull down to retry.',
                      style: const TextStyle(color: Colors.red),
                      textAlign: TextAlign.center
                    ),
                  ),
               )
            );
          }

          // Show message if no logs are available after loading
          if (logs.isEmpty) {
              return RefreshIndicator(
                 onRefresh: () => appState.fetchLogs(),
                 child: const Center(child: Text('No logs found.')),
              );
          }

          // Display the list of logs with pull-to-refresh
          return RefreshIndicator(
            onRefresh: () => appState.fetchLogs(),
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(vertical: 8.0),
              itemCount: logs.length,
              itemBuilder: (context, index) {
                final log = logs[index];
                final formattedTime = DateFormat('yyyy-MM-dd HH:mm:ss').format(log.timestamp);
                final message = log.details?['message'] ?? log.eventType.toString();
                final severityColor = _getSeverityColor(log.severity);
                final iconData = _getLogIcon(log);

                return ListTile(
                  leading: Icon(iconData, color: severityColor, size: 28), // Slightly larger icon
                  title: Text(message, style: const TextStyle(fontWeight: FontWeight.w500)),
                  subtitle: Text('Source: ${log.source} | ${log.userId != null ? 'User: ${log.userId}' : 'System'}\n$formattedTime'),
                  isThreeLine: true, // Allow more space for subtitle
                  dense: false,
                  onTap: () => _showLogDetailsDialog(context, log),
                );
              },
              separatorBuilder: (context, index) => const Divider(height: 1, indent: 16, endIndent: 16),
            ),
          );
        },
      ),
    );
  }
}
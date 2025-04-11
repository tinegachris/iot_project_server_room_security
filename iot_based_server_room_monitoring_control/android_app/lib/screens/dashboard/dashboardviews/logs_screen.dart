import 'package:flutter/material.dart';
import 'package:intl/intl.dart'; // For date formatting
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart'; // Import url_launcher
import '../../../providers/app_state.dart'; // Adjusted import path
import '../../../models/log_entry.dart'; // Import LogEntry model
import 'package:logging/logging.dart';

class LogsScreen extends StatelessWidget {
  static final Logger _logger = Logger('LogsScreen');

  LogsScreen({super.key});

  // Date formatter
  final DateFormat _logTimestampFormatter = DateFormat('yyyy-MM-dd HH:mm:ss');

  Color _severityColor(String severity) {
    switch (severity.toLowerCase()) { // Use toLowerCase for safety
      case 'critical':
        return Colors.red[700] ?? Colors.red;
      case 'error':
        return Colors.redAccent;
      case 'warning':
        return Colors.orange[600] ?? Colors.orange;
      case 'info':
      default:
        // Use a less prominent color for info logs
        return Colors.blueGrey[600] ?? Colors.blueGrey;
    }
  }

  IconData _sourceIcon(String source) {
    switch (source.toLowerCase()) { // Use toLowerCase for safety
      case 'camera':
        return Icons.videocam_outlined;
      case 'sensor_motion':
        return Icons.directions_run;
       case 'sensor_door':
         return Icons.door_front_door_outlined;
       case 'sensor_window':
         return Icons.window_outlined;
      case 'rfid':
        return Icons.nfc; // More specific than rss_feed
      case 'user':
        return Icons.person_outline;
      case 'system':
      default:
        return Icons.dns; // More representative of system/server
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        if (appState.isFetchingLogs) {
          return const Center(child: CircularProgressIndicator());
        }

        if (appState.logsError != null) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text('Error: ${appState.logsError}'),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () {
                    appState.clearLogsError();
                    appState.fetchLogs();
                  },
                  child: const Text('Retry'),
                ),
              ],
            ),
          );
        }

        final logs = appState.logs;
        if (logs.isEmpty) {
          return const Center(child: Text('No logs available'));
        }

        return RefreshIndicator(
          onRefresh: () => appState.fetchLogs(),
          child: ListView.builder(
            itemCount: logs.length,
            itemBuilder: (context, index) {
              final log = logs[index];
              final hasVideo = log.videoUrl != null;

              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                child: ListTile(
                  leading: Icon(
                    _sourceIcon(log.source),
                    color: _severityColor(log.severity),
                  ),
                  title: Text(log.eventType),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _logTimestampFormatter.format(log.timestamp.toLocal()),
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      if (log.details?.containsKey('message') ?? false)
                        Text(
                          log.details!['message'].toString(),
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                    ],
                  ),
                  trailing: hasVideo
                      ? const Icon(Icons.videocam_outlined)
                      : null,
                  onTap: () => _onLogTap(context, log),
                ),
              );
            },
          ),
        );
      },
    );
  }

  Future<void> _launchUrl(String urlString) async {
    try {
      final url = Uri.parse(urlString);
      if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
        _logger.warning('Could not launch $urlString');
      }
    } catch (e) {
      _logger.severe('Error launching URL $urlString: $e');
    }
  }

  void _onLogTap(BuildContext context, LogEntry log) {
    _logger.info("Tapped log: ${log.id}");
    if (log.videoUrl != null) {
      _logger.info("Video URL: ${log.videoUrl}");
      _launchUrl(log.videoUrl!);
    }
    _showLogDetailsDialog(context, log);
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
              Text('Time: ${log.timestamp.toLocal()}'),
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
              if (log.videoUrl != null) ...[
                const SizedBox(height: 16),
                Center(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.videocam_outlined),
                    label: const Text('View Video'),
                    onPressed: () => _launchUrl(log.videoUrl!),
                  ),
                ),
              ],
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
}

// Helper extension for capitalizing strings
extension StringExtension on String {
    String capitalize() {
      if (isEmpty) return "";
      return "${this[0].toUpperCase()}${substring(1).toLowerCase()}";
    }
}

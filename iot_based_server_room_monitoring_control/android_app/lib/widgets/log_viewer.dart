import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart'; // For date formatting

import '../providers/app_state.dart';
import '../models/LogEntry.dart';

class LogViewer extends StatelessWidget {
  final int maxEntriesToShow;

  const LogViewer({super.key, this.maxEntriesToShow = 10}); // Default to show 10

   // Helper to get color based on log severity
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
        return Colors.black;
    }
  }

   // Helper to get icon based on log severity or eventType
  IconData _getLogIcon(LogEntry log) {
    // Prioritize severity
     switch (log.severity?.toLowerCase()) {
      case 'critical':
      case 'error':
        return Icons.error_outline;
      case 'warning':
        return Icons.warning_amber_outlined;
    }
    // Then check event type for more specific icons
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
       case 'system_info': // Example for app-generated logs
           return Icons.info_outline;
       default:
         return Icons.article_outlined; // Generic log icon
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        final logs = appState.logs;
        final isLoading = appState.isFetchingLogs;
        final error = appState.logsError;

        if (isLoading && logs.isEmpty) {
          return const Card(
            elevation: 2.0,
            child: Padding(
              padding: EdgeInsets.all(20.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(strokeWidth: 2),
                  SizedBox(width: 16),
                  Text("Loading Recent Logs..."),
                ],
              ),
            ),
          );
        }

        if (error != null && logs.isEmpty) {
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

        if (logs.isEmpty) {
          return const Center(child: Text('No recent logs available.'));
        }

        // Take only the specified number of most recent logs
        final displayedLogs = logs.take(maxEntriesToShow).toList();

        return Card(
          elevation: 2.0,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                 child: Text(
                   'Recent Logs', 
                   style: Theme.of(context).textTheme.titleLarge
                 ),
              ),
               const Divider(),
              ListView.separated(
                shrinkWrap: true, // Important for ListView inside Column
                physics: const NeverScrollableScrollPhysics(), // Disable scrolling within the card
                itemCount: displayedLogs.length,
                itemBuilder: (context, index) {
                  final log = displayedLogs[index];
                  final formattedTime = DateFormat('yyyy-MM-dd HH:mm:ss').format(log.timestamp);
                  final message = log.details?['message'] ?? log.eventType;
                  final severityColor = _getSeverityColor(log.severity);
                  final iconData = _getLogIcon(log);

                  return ListTile(
                    leading: Icon(iconData, color: severityColor),
                    title: Text(message, style: TextStyle(fontWeight: FontWeight.w500)),
                    subtitle: Text('${log.source ?? '-'} | $formattedTime'),
                    dense: true,
                  );
                },
                separatorBuilder: (context, index) => const Divider(height: 0, indent: 16, endIndent: 16),
              ),
               // Optional: Add a button to navigate to the full logs page
               if (logs.length > maxEntriesToShow)
                 Padding(
                   padding: const EdgeInsets.only(top: 8.0, right: 8.0),
                   child: Align(
                     alignment: Alignment.centerRight,
                     child: TextButton(
                       onPressed: () {
                           // TODO: Navigate to full LogsPage
                           ScaffoldMessenger.of(context).showSnackBar(
                             const SnackBar(content: Text('Navigate to full logs page (TODO)'))
                           );
                       },
                       child: const Text('View All Logs'),
                     ),
                   ),
                 ),
            ],
          ),
        );
      },
    );
  }
} 
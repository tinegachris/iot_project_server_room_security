import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../providers/app_state.dart';

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Consume AppState to get status and errors
    final appState = context.watch<AppState>();
    final systemStatus = appState.currentStatus;
    final List<String> alerts = systemStatus?.errors ?? [];
    // Show loading only if the main status is still loading
    final isLoading = appState.isFetchingStatus && systemStatus == null;
    // Use statusError for initial load error
    final error = appState.statusError;

    return Scaffold(
       backgroundColor: Colors.grey[100], // Consistent background
       body: isLoading
           ? const Center(child: CircularProgressIndicator())
           : error != null && systemStatus == null // Show error only if status is null
               ? Center(
                   child: Padding(
                     padding: const EdgeInsets.all(16.0),
                     child: Column(
                       mainAxisAlignment: MainAxisAlignment.center,
                       children: [
                         Text(
                           'Error loading system status: $error',
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
                   ))
            : RefreshIndicator( // ✅ Add pull-to-refresh
                onRefresh: () => context.read<AppState>().fetchSystemStatus(),
                child: alerts.isEmpty
                   ? Center(
                       child: Text(
                         "No active system alerts.",
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey[600]),
                       )
                     )
                   : ListView.builder(
                       physics: const AlwaysScrollableScrollPhysics(), // Needed for RefreshIndicator
                       padding: const EdgeInsets.all(8.0),
                       itemCount: alerts.length,
                       itemBuilder: (context, index) {
                         final alertMessage = alerts[index];
                         return Card(
                           elevation: 1.5,
                           margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                           color: Colors.orange[50], // Use a warning color
                           shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                           child: ListTile(
                              leading: Icon(Icons.warning_amber_rounded, color: Colors.orange[700]),
                              title: Text(alertMessage, style: const TextStyle(fontSize: 14)),
                              // Optional: Add timestamp if available or needed
                           ),
                         );
                       },
                     ),
              ),
    );
  }
}

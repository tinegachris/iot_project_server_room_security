import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../models/log_entry.dart';
import 'package:intl/intl.dart';

class LogsScreen extends StatefulWidget {
  @override
  _LogsScreenState createState() => _LogsScreenState();
}

class _LogsScreenState extends State<LogsScreen> {
  final _dateFormat = DateFormat('MMM d, y HH:mm');
  String? _selectedEventType;
  DateTime? _startDate;
  DateTime? _endDate;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().fetchLogs();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('System Logs'),
        actions: [
          IconButton(
            icon: Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
          ),
        ],
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
                      context.read<AppState>().fetchLogs(
                        eventType: _selectedEventType,
                        startDate: _startDate,
                        endDate: _endDate,
                      );
                    },
                    child: Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final logs = appState.logs;
          if (logs.isEmpty) {
            return Center(child: Text('No logs available'));
          }

          return ListView.builder(
            itemCount: logs.length,
            itemBuilder: (context, index) {
              final log = logs[index];
              return _buildLogCard(log);
            },
          );
        },
      ),
    );
  }

  Widget _buildLogCard(LogEntry log) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _getEventTypeColor(log.eventType),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    log.eventType.toUpperCase(),
                    style: TextStyle(color: Colors.white),
                  ),
                ),
                Text(
                  _dateFormat.format(log.timestamp),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
            SizedBox(height: 8),
            Text(log.details),
            if (log.videoUrl != null) ...[
              SizedBox(height: 8),
              ElevatedButton.icon(
                onPressed: () {
                  // TODO: Implement video playback
                },
                icon: Icon(Icons.videocam),
                label: Text('View Video'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _getEventTypeColor(String eventType) {
    switch (eventType.toLowerCase()) {
      case 'alert':
        return Colors.red;
      case 'warning':
        return Colors.orange;
      case 'info':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  Future<void> _showFilterDialog() async {
    final eventTypes = ['alert', 'warning', 'info', 'control_command'];
    
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Filter Logs'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DropdownButtonFormField<String>(
              value: _selectedEventType,
              decoration: InputDecoration(
                labelText: 'Event Type',
                border: OutlineInputBorder(),
              ),
              items: [
                DropdownMenuItem(
                  value: null,
                  child: Text('All'),
                ),
                ...eventTypes.map((type) => DropdownMenuItem(
                  value: type,
                  child: Text(type.toUpperCase()),
                )),
              ],
              onChanged: (value) {
                setState(() {
                  _selectedEventType = value;
                });
              },
            ),
            SizedBox(height: 16),
            ListTile(
              title: Text('Start Date'),
              subtitle: Text(_startDate != null
                  ? _dateFormat.format(_startDate!)
                  : 'Not set'),
              onTap: () async {
                final date = await showDatePicker(
                  context: context,
                  initialDate: _startDate ?? DateTime.now(),
                  firstDate: DateTime(2000),
                  lastDate: DateTime.now(),
                );
                if (date != null) {
                  setState(() {
                    _startDate = date;
                  });
                }
              },
            ),
            ListTile(
              title: Text('End Date'),
              subtitle: Text(_endDate != null
                  ? _dateFormat.format(_endDate!)
                  : 'Not set'),
              onTap: () async {
                final date = await showDatePicker(
                  context: context,
                  initialDate: _endDate ?? DateTime.now(),
                  firstDate: DateTime(2000),
                  lastDate: DateTime.now(),
                );
                if (date != null) {
                  setState(() {
                    _endDate = date;
                  });
                }
              },
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              setState(() {
                _selectedEventType = null;
                _startDate = null;
                _endDate = null;
              });
              Navigator.pop(context);
              context.read<AppState>().fetchLogs();
            },
            child: Text('Clear Filters'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              context.read<AppState>().fetchLogs(
                eventType: _selectedEventType,
                startDate: _startDate,
                endDate: _endDate,
              );
            },
            child: Text('Apply'),
          ),
        ],
      ),
    );
  }
} 
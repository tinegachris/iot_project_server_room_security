class LogEntry {
  final int id;
  final String eventType;
  final DateTime timestamp;
  final Map<String, dynamic>? details; // Can be nullable or more specific
  final int? userId; // User associated with the event, if any
  final String? videoUrl; // Optional URL for related video
  final String severity; // e.g., info, warning, error, critical
  final String source; // e.g., system, camera, sensor_motion, rfid

  LogEntry({
    required this.id,
    required this.eventType,
    required this.timestamp,
    this.details,
    this.userId,
    this.videoUrl,
    required this.severity,
    required this.source,
  });

  // Manual fromJson based on the example log in AppState
  factory LogEntry.fromJson(Map<String, dynamic> json) {
    try {
      print("Parsing LogEntry: ${json.keys}");
      return LogEntry(
        id: json['id'] as int? ?? -1,
        eventType: json['event_type'] as String? ?? 'unknown',
        timestamp: json['timestamp'] != null 
            ? DateTime.parse(json['timestamp'] as String) 
            : DateTime.now(),
        details: json['details'] as Map<String, dynamic>?,
        userId: json['user_id'] as int?,
        videoUrl: json['video_url'] as String?,
        severity: json['severity'] as String? ?? 'info', // Default severity if missing
        source: json['source'] as String? ?? 'unknown', // Default source if missing
      );
    } catch (e) {
      print("Error parsing LogEntry: $e, JSON: $json");
      // Return a fallback log entry
      return LogEntry(
        id: -1,
        eventType: 'parse_error',
        timestamp: DateTime.now(),
        details: {'error': 'Failed to parse log entry: $e', 'original_json': json},
        userId: null,
        videoUrl: null,
        severity: 'error',
        source: 'app',
      );
    }
  }

  // Optional: toJson if needed
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'event_type': eventType,
      'timestamp': timestamp.toIso8601String(),
      'details': details,
      'user_id': userId,
      'video_url': videoUrl,
      'severity': severity,
      'source': source,
    };
  }
} 
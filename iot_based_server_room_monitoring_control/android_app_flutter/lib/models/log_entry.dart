class LogEntry {
  final int id;
  final String eventType;
  final DateTime timestamp;
  final String details;
  final String? videoUrl;
  final int userId;

  LogEntry({
    required this.id,
    required this.eventType,
    required this.timestamp,
    required this.details,
    this.videoUrl,
    required this.userId,
  });

  factory LogEntry.fromJson(Map<String, dynamic> json) {
    return LogEntry(
      id: json['id'],
      eventType: json['event_type'],
      timestamp: DateTime.parse(json['timestamp']),
      details: json['details'],
      videoUrl: json['video_url'],
      userId: json['user_id'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'event_type': eventType,
      'timestamp': timestamp.toIso8601String(),
      'details': details,
      'video_url': videoUrl,
      'user_id': userId,
    };
  }
}
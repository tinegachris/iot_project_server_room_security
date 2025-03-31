import 'package:json_annotation/json_annotation.dart';

part 'log_entry.g.dart';

enum Severity {
  @JsonValue('info')
  info,
  @JsonValue('warning')
  warning,
  @JsonValue('error')
  error,
  @JsonValue('critical')
  critical
}

enum Source {
  @JsonValue('system')
  system,
  @JsonValue('user')
  user,
  @JsonValue('sensor')
  sensor,
  @JsonValue('camera')
  camera,
  @JsonValue('rfid')
  rfid
}

@JsonSerializable()
class LogEntry {
  final int? id;
  @JsonKey(name: 'event_type')
  final String eventType;
  final DateTime timestamp;
  final Map<String, dynamic> details;
  @JsonKey(name: 'user_id')
  final int? userId;
  @JsonKey(name: 'video_url')
  final String? videoUrl;
  final Severity severity;
  final Source source;

  LogEntry({
    this.id,
    required this.eventType,
    required this.timestamp,
    required this.details,
    this.userId,
    this.videoUrl,
    this.severity = Severity.info,
    required this.source,
  });

  factory LogEntry.fromJson(Map<String, dynamic> json) =>
      _$LogEntryFromJson(json);

  bool get hasVideo => videoUrl != null;
  bool get isCritical => severity == Severity.critical;
  bool get isError => severity == Severity.error;
  bool get isWarning => severity == Severity.warning;
  bool get isInfo => severity == Severity.info;
}
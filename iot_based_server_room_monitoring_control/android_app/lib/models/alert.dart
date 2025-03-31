import 'package:json_annotation/json_annotation.dart';

part 'alert.g.dart';

enum AlertSeverity {
  @JsonValue('low')
  low,
  @JsonValue('medium')
  medium,
  @JsonValue('high')
  high,
  @JsonValue('critical')
  critical
}

@JsonSerializable()
class Alert {
  final int? id;
  final String message;
  @JsonKey(name: 'video_url')
  final String? videoUrl;
  @JsonKey(name: 'event_timestamp')
  final DateTime eventTimestamp;
  final List<String> channels;
  @JsonKey(name: 'created_by')
  final int? createdBy;
  final String status;
  @JsonKey(name: 'sent_at')
  final DateTime? sentAt;
  final AlertSeverity severity;
  @JsonKey(name: 'sensor_data')
  final Map<String, dynamic>? sensorData;
  final bool acknowledged;
  @JsonKey(name: 'acknowledged_by')
  final int? acknowledgedBy;
  @JsonKey(name: 'acknowledged_at')
  final DateTime? acknowledgedAt;

  Alert({
    this.id,
    required this.message,
    this.videoUrl,
    required this.eventTimestamp,
    required this.channels,
    this.createdBy,
    required this.status,
    this.sentAt,
    required this.severity,
    this.sensorData,
    this.acknowledged = false,
    this.acknowledgedBy,
    this.acknowledgedAt,
  });

  factory Alert.fromJson(Map<String, dynamic> json) => _$AlertFromJson(json);

  bool get hasVideo => videoUrl != null;
  bool get isCritical => severity == AlertSeverity.critical;
  bool get isHigh => severity == AlertSeverity.high;
  bool get isMedium => severity == AlertSeverity.medium;
  bool get isLow => severity == AlertSeverity.low;
  bool get isPending => status == 'pending';
  bool get isSent => status == 'sent';
  bool get isFailed => status == 'failed';
} 
import 'package:json_annotation/json_annotation.dart';

part 'system_status.g.dart';

@JsonSerializable()
class SensorStatus {
  final String name;
  final bool isActive;
  @JsonKey(name: 'last_check')
  final DateTime lastCheck;
  final String? error;
  final Map<String, dynamic>? data;
  final String? location;
  final String? type;
  @JsonKey(name: 'firmware_version')
  final String? firmwareVersion;
  @JsonKey(name: 'last_event')
  final DateTime? lastEvent;
  @JsonKey(name: 'event_count')
  final int eventCount;

  SensorStatus({
    required this.name,
    required this.isActive,
    required this.lastCheck,
    this.error,
    this.data,
    this.location,
    this.type,
    this.firmwareVersion,
    this.lastEvent,
    this.eventCount = 0,
  });

  factory SensorStatus.fromJson(Map<String, dynamic> json) =>
      _$SensorStatusFromJson(json);
}

@JsonSerializable()
class RaspberryPiStatus {
  @JsonKey(name: 'is_online')
  final bool isOnline;
  @JsonKey(name: 'last_heartbeat')
  final DateTime lastHeartbeat;
  @JsonKey(name: 'firmware_version')
  final String firmwareVersion;
  @JsonKey(name: 'sensor_types')
  final List<String> sensorTypes;
  @JsonKey(name: 'total_events')
  final int totalEvents;

  RaspberryPiStatus({
    required this.isOnline,
    required this.lastHeartbeat,
    required this.firmwareVersion,
    required this.sensorTypes,
    required this.totalEvents,
  });

  factory RaspberryPiStatus.fromJson(Map<String, dynamic> json) =>
      _$RaspberryPiStatusFromJson(json);
}

@JsonSerializable()
class SystemStatus {
  final String status;
  final Map<String, SensorStatus> sensors;
  final Map<String, dynamic> storage;
  final String uptime;
  @JsonKey(name: 'last_maintenance')
  final DateTime? lastMaintenance;
  @JsonKey(name: 'next_maintenance')
  final DateTime? nextMaintenance;
  final List<String>? errors;
  @JsonKey(name: 'raspberry_pi')
  final RaspberryPiStatus raspberryPi;

  SystemStatus({
    required this.status,
    required this.sensors,
    required this.storage,
    required this.uptime,
    this.lastMaintenance,
    this.nextMaintenance,
    this.errors,
    required this.raspberryPi,
  });

  factory SystemStatus.fromJson(Map<String, dynamic> json) =>
      _$SystemStatusFromJson(json);

  bool get hasErrors => errors != null && errors!.isNotEmpty;
  bool get isHealthy => status == 'healthy';
  bool get isDegraded => status == 'degraded';
  bool get hasLowStorage => storage['low_space'] == true;
} 
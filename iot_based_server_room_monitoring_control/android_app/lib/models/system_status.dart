import 'package:logging/logging.dart';

// Add necessary import

// Removed generator comments

class SensorStatus {
  static final Logger _logger = Logger('SensorStatus');

  final String name;
  final bool isActive;
  final DateTime lastCheck;
  final String? error;
  final Map<String, dynamic>? data;
  final String? location;
  final String? type;
  final String? firmwareVersion;
  final DateTime? lastEvent;
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

  // Manual fromJson implementation
  factory SensorStatus.fromJson(Map<String, dynamic> json) {
    try {
      return SensorStatus(
        name: json['name'] as String? ?? 'unknown',
        isActive: json['is_active'] as bool? ?? false,  // API returns 'is_active', not 'isActive'
        lastCheck: json['last_check'] != null
            ? DateTime.parse(json['last_check'] as String)
            : DateTime.now(),
        error: json['error'] as String?,
        data: json['data'] as Map<String, dynamic>?,
        location: json['location'] as String?,
        type: json['type'] as String?,
        firmwareVersion: json['firmware_version'] as String?,
        lastEvent: json['last_event'] != null ? DateTime.parse(json['last_event'] as String) : null,
        eventCount: json['event_count'] as int? ?? 0,
      );
    } catch (e) {
      _logger.warning("Error parsing SensorStatus: $e");
      rethrow;
    }
  }
}

class RaspberryPiStatus {
  static final Logger _logger = Logger('RaspberryPiStatus');

  final bool isOnline;
  final DateTime lastHeartbeat;
  final String firmwareVersion;
  final List<String> sensorTypes;
  final int totalEvents;

  RaspberryPiStatus({
    required this.isOnline,
    required this.lastHeartbeat,
    required this.firmwareVersion,
    required this.sensorTypes,
    required this.totalEvents,
  });

  // Manual fromJson implementation
  factory RaspberryPiStatus.fromJson(Map<String, dynamic> json) {
    try {
      return RaspberryPiStatus(
        isOnline: json['is_online'] as bool? ?? false,
        lastHeartbeat: json['last_heartbeat'] != null
            ? DateTime.parse(json['last_heartbeat'] as String)
            : DateTime.now(),
        firmwareVersion: json['firmware_version'] as String? ?? 'unknown',
        sensorTypes: json['sensor_types'] != null
            ? (json['sensor_types'] as List<dynamic>).cast<String>()
            : <String>[],
        totalEvents: json['total_events'] as int? ?? 0,
      );
    } catch (e) {
      _logger.warning("Error parsing RaspberryPiStatus: $e");
      rethrow;
    }
  }
}

class SystemStatus {
  static final Logger _logger = Logger('SystemStatus');

  final String status;
  final Map<String, SensorStatus> sensors;
  final Map<String, dynamic> storage; // Keeping storage as dynamic map for now
  final String uptime;
  final DateTime? lastMaintenance;
  final DateTime? nextMaintenance;
  final List<String>? errors;
  final RaspberryPiStatus raspberryPi;
  final String? message;

  SystemStatus({
    required this.status,
    required this.sensors,
    required this.storage,
    required this.uptime,
    this.lastMaintenance,
    this.nextMaintenance,
    this.errors,
    required this.raspberryPi,
    this.message,
  });

  // Manual fromJson implementation
  factory SystemStatus.fromJson(Map<String, dynamic> json) {
    _logger.info("Parsing SystemStatus from JSON: ${json.keys}");
    try {
      // Parse sensors
      Map<String, SensorStatus> sensorsMap = {};
      try {
        if (json['sensors'] is Map<String, dynamic>) {
          sensorsMap = (json['sensors'] as Map<String, dynamic>).map(
            (key, value) => MapEntry(key, SensorStatus.fromJson(value as Map<String, dynamic>)),
          );
        } else {
          _logger.warning("Sensors is not a map or is null: ${json['sensors']}");
        }
      } catch (e) {
        _logger.warning("Error parsing sensors: $e");
      }

      // Parse raspberry_pi
      RaspberryPiStatus piStatus;
      try {
        if (json['raspberry_pi'] is Map<String, dynamic>) {
          piStatus = RaspberryPiStatus.fromJson(json['raspberry_pi'] as Map<String, dynamic>);
        } else {
          _logger.warning("raspberry_pi is not a map or is null: ${json['raspberry_pi']}");
          piStatus = RaspberryPiStatus(
            isOnline: false,
            lastHeartbeat: DateTime.now(),
            firmwareVersion: "unknown",
            sensorTypes: [],
            totalEvents: 0
          );
        }
      } catch (e) {
        _logger.warning("Error parsing raspberry_pi: $e");
        piStatus = RaspberryPiStatus(
          isOnline: false,
          lastHeartbeat: DateTime.now(),
          firmwareVersion: "unknown",
          sensorTypes: [],
          totalEvents: 0
        );
      }

      return SystemStatus(
        status: json['status'] as String? ?? 'unknown',
        sensors: sensorsMap,
        storage: json['storage'] as Map<String, dynamic>? ?? {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'low_space': false},
        uptime: json['uptime'] as String? ?? 'unknown',
        lastMaintenance: json['last_maintenance'] != null ? DateTime.parse(json['last_maintenance'] as String) : null,
        nextMaintenance: json['next_maintenance'] != null ? DateTime.parse(json['next_maintenance'] as String) : null,
        errors: (json['errors'] as List<dynamic>?)?.cast<String>() ?? [],
        raspberryPi: piStatus,
        message: json['message'] as String?,
      );
    } catch (e) {
      _logger.severe("Error creating SystemStatus from JSON: $e");
      rethrow;
    }
  }

  bool get hasErrors => errors != null && errors!.isNotEmpty;
  bool get isHealthy => status == 'healthy'; // Assuming 'healthy' status string
  bool get isDegraded => status == 'degraded'; // Assuming 'degraded' status string
  bool get hasLowStorage => storage['low_space'] == true;
}
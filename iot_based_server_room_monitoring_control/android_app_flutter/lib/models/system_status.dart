class SystemStatus {
  final String status;
  final DateTime timestamp;
  final SystemHealth systemHealth;
  final String user;

  SystemStatus({
    required this.status,
    required this.timestamp,
    required this.systemHealth,
    required this.user,
  });

  factory SystemStatus.fromJson(Map<String, dynamic> json) {
    return SystemStatus(
      status: json['status'],
      timestamp: DateTime.parse(json['timestamp']),
      systemHealth: SystemHealth.fromJson(json['system_health']),
      user: json['user'],
    );
  }
}

class SystemHealth {
  final Map<String, String> sensors;
  final StorageInfo storage;
  final String uptime;
  final DateTime lastMaintenance;

  SystemHealth({
    required this.sensors,
    required this.storage,
    required this.uptime,
    required this.lastMaintenance,
  });

  factory SystemHealth.fromJson(Map<String, dynamic> json) {
    return SystemHealth(
      sensors: Map<String, String>.from(json['sensors']),
      storage: StorageInfo.fromJson(json['storage']),
      uptime: json['uptime'],
      lastMaintenance: DateTime.parse(json['last_maintenance']),
    );
  }
}

class StorageInfo {
  final String total;
  final String used;
  final String free;

  StorageInfo({
    required this.total,
    required this.used,
    required this.free,
  });

  factory StorageInfo.fromJson(Map<String, dynamic> json) {
    return StorageInfo(
      total: json['total'],
      used: json['used'],
      free: json['free'],
    );
  }
} 
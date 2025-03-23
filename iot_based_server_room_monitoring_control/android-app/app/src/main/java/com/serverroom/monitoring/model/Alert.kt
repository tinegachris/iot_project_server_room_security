package com.serverroom.monitoring.model

import java.util.Date

data class Alert(
    val id: String,
    val type: AlertType,
    val message: String,
    val timestamp: Date,
    val severity: AlertSeverity
)

enum class AlertType {
    INTRUSION_DETECTED,
    DOOR_FORCED,
    WINDOW_BREACH,
    MOTION_DETECTED,
    SYSTEM_ERROR
}

enum class AlertSeverity {
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL
}
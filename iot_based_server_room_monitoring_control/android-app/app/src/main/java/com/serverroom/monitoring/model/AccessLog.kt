package com.serverroom.monitoring.model

import java.util.Date

data class AccessLog(
    val id: String,
    val userId: String,
    val userName: String,
    val accessType: AccessType,
    val timestamp: Date,
    val status: AccessStatus
)

enum class AccessType {
    RFID,
    MANUAL_OVERRIDE,
    SYSTEM_ACCESS
}

enum class AccessStatus {
    GRANTED,
    DENIED,
    PENDING
}
package com.serverroom.monitoring.repository

import com.serverroom.monitoring.model.Alert
import com.serverroom.monitoring.model.AccessLog
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.Date

class ServerRoomRepository {
    private val api: ServerRoomApi = Retrofit.Builder()
        .baseUrl("YOUR_API_BASE_URL")
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(ServerRoomApi::class.java)

    suspend fun getServerStatus(): String {
        return try {
            api.getServerStatus().status
        } catch (e: Exception) {
            "Error: Unable to fetch server status"
        }
    }

    suspend fun getRecentAlerts(): List<Alert> {
        return try {
            api.getRecentAlerts()
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun getAccessLogs(): List<AccessLog> {
        return try {
            api.getAccessLogs()
        } catch (e: Exception) {
            emptyList()
        }
    }

    fun getRealTimeUpdates(): Flow<Update> = flow {
        // TODO: Implement WebSocket connection for real-time updates
        // For now, emit mock data
        emit(Update.Status("All systems operational"))
        emit(Update.Alert(
            Alert(
                id = "1",
                type = AlertType.MOTION_DETECTED,
                message = "Motion detected in server room",
                timestamp = Date(),
                severity = AlertSeverity.MEDIUM
            )
        ))
        emit(Update.AccessLog(
            AccessLog(
                id = "1",
                userId = "user123",
                userName = "John Doe",
                accessType = AccessType.RFID,
                timestamp = Date(),
                status = AccessStatus.GRANTED
            )
        ))
    }

    sealed class Update {
        data class Status(val status: String) : Update()
        data class Alert(val alert: Alert) : Update()
        data class AccessLog(val log: AccessLog) : Update()
    }
}

interface ServerRoomApi {
    suspend fun getServerStatus(): ServerStatusResponse
    suspend fun getRecentAlerts(): List<Alert>
    suspend fun getAccessLogs(): List<AccessLog>
}

data class ServerStatusResponse(
    val status: String,
    val lastUpdated: Date
) 
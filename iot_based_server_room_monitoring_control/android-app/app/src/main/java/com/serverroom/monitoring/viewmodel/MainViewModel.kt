package com.serverroom.monitoring.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.serverroom.monitoring.model.Alert
import com.serverroom.monitoring.model.AccessLog
import com.serverroom.monitoring.repository.ServerRoomRepository
import kotlinx.coroutines.launch

class MainViewModel : ViewModel() {
    private val repository = ServerRoomRepository()
    
    private val _serverStatus = MutableLiveData<String>()
    val serverStatus: LiveData<String> = _serverStatus

    private val _alerts = MutableLiveData<List<Alert>>()
    val alerts: LiveData<List<Alert>> = _alerts

    private val _accessLogs = MutableLiveData<List<AccessLog>>()
    val accessLogs: LiveData<List<AccessLog>> = _accessLogs

    init {
        loadInitialData()
        startRealTimeUpdates()
    }

    private fun loadInitialData() {
        viewModelScope.launch {
            try {
                // Load server status
                _serverStatus.value = repository.getServerStatus()
                
                // Load recent alerts
                _alerts.value = repository.getRecentAlerts()
                
                // Load access logs
                _accessLogs.value = repository.getAccessLogs()
            } catch (e: Exception) {
                // Handle error
            }
        }
    }

    private fun startRealTimeUpdates() {
        viewModelScope.launch {
            repository.getRealTimeUpdates().collect { update ->
                when (update) {
                    is ServerRoomRepository.Update.Alert -> {
                        val currentList = _alerts.value?.toMutableList() ?: mutableListOf()
                        currentList.add(0, update.alert)
                        _alerts.value = currentList.take(50) // Keep last 50 alerts
                    }
                    is ServerRoomRepository.Update.AccessLog -> {
                        val currentList = _accessLogs.value?.toMutableList() ?: mutableListOf()
                        currentList.add(0, update.log)
                        _accessLogs.value = currentList.take(50) // Keep last 50 logs
                    }
                    is ServerRoomRepository.Update.Status -> {
                        _serverStatus.value = update.status
                    }
                }
            }
        }
    }

    fun refreshData() {
        loadInitialData()
    }
} 
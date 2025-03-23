package com.serverroom.monitoring.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.serverroom.monitoring.databinding.ItemAlertBinding
import com.serverroom.monitoring.model.Alert
import java.text.SimpleDateFormat
import java.util.Locale

class AlertsAdapter : ListAdapter<Alert, AlertsAdapter.AlertViewHolder>(AlertDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): AlertViewHolder {
        val binding = ItemAlertBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return AlertViewHolder(binding)
    }

    override fun onBindViewHolder(holder: AlertViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class AlertViewHolder(
        private val binding: ItemAlertBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        private val dateFormat = SimpleDateFormat("MMM dd, HH:mm", Locale.getDefault())

        fun bind(alert: Alert) {
            binding.apply {
                alertType.text = alert.type.name
                alertMessage.text = alert.message
                alertTimestamp.text = dateFormat.format(alert.timestamp)
                
                // Set severity color
                val severityColor = when (alert.severity) {
                    AlertSeverity.LOW -> android.graphics.Color.GREEN
                    AlertSeverity.MEDIUM -> android.graphics.Color.YELLOW
                    AlertSeverity.HIGH -> android.graphics.Color.RED
                    AlertSeverity.CRITICAL -> android.graphics.Color.RED
                }
                severityIndicator.setBackgroundColor(severityColor)
            }
        }
    }

    private class AlertDiffCallback : DiffUtil.ItemCallback<Alert>() {
        override fun areItemsTheSame(oldItem: Alert, newItem: Alert): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: Alert, newItem: Alert): Boolean {
            return oldItem == newItem
        }
    }
} 
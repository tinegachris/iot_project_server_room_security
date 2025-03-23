package com.serverroom.monitoring.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.serverroom.monitoring.databinding.ItemAccessLogBinding
import com.serverroom.monitoring.model.AccessLog
import java.text.SimpleDateFormat
import java.util.Locale

class AccessLogAdapter : ListAdapter<AccessLog, AccessLogAdapter.AccessLogViewHolder>(AccessLogDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): AccessLogViewHolder {
        val binding = ItemAccessLogBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return AccessLogViewHolder(binding)
    }

    override fun onBindViewHolder(holder: AccessLogViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class AccessLogViewHolder(
        private val binding: ItemAccessLogBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        private val dateFormat = SimpleDateFormat("MMM dd, HH:mm", Locale.getDefault())

        fun bind(log: AccessLog) {
            binding.apply {
                userName.text = log.userName
                accessType.text = log.accessType.name
                timestamp.text = dateFormat.format(log.timestamp)
                
                // Set status color and text
                val (statusColor, statusText) = when (log.status) {
                    AccessStatus.GRANTED -> android.graphics.Color.GREEN to "GRANTED"
                    AccessStatus.DENIED -> android.graphics.Color.RED to "DENIED"
                    AccessStatus.PENDING -> android.graphics.Color.YELLOW to "PENDING"
                }
                statusIndicator.setBackgroundColor(statusColor)
                status.text = statusText
            }
        }
    }

    private class AccessLogDiffCallback : DiffUtil.ItemCallback<AccessLog>() {
        override fun areItemsTheSame(oldItem: AccessLog, newItem: AccessLog): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: AccessLog, newItem: AccessLog): Boolean {
            return oldItem == newItem
        }
    }
} 
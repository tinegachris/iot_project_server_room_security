package com.serverroom.monitoring

import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.exoplayer2.ExoPlayer
import com.google.android.exoplayer2.MediaItem
import com.google.android.material.snackbar.Snackbar
import com.serverroom.monitoring.databinding.ActivityMainBinding
import com.serverroom.monitoring.viewmodel.MainViewModel
import com.serverroom.monitoring.adapter.AlertsAdapter
import com.serverroom.monitoring.adapter.AccessLogAdapter

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private lateinit var viewModel: MainViewModel
    private lateinit var player: ExoPlayer
    private lateinit var alertsAdapter: AlertsAdapter
    private lateinit var accessLogAdapter: AccessLogAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Setup toolbar
        setSupportActionBar(binding.toolbar)
        supportActionBar?.title = "Server Room Monitor"

        // Initialize ViewModel
        viewModel = ViewModelProvider(this)[MainViewModel::class.java]

        // Setup ExoPlayer for video streaming
        setupVideoPlayer()

        // Setup RecyclerViews
        setupRecyclerViews()

        // Setup FAB
        binding.fabSettings.setOnClickListener {
            // TODO: Implement settings navigation
            Snackbar.make(it, "Settings coming soon", Snackbar.LENGTH_SHORT).show()
        }

        // Observe ViewModel data
        observeViewModel()
    }

    private fun setupVideoPlayer() {
        player = ExoPlayer.Builder(this).build().apply {
            binding.playerView.player = this
            // TODO: Set video source from server
            val mediaItem = MediaItem.fromUri("YOUR_VIDEO_STREAM_URL")
            setMediaItem(mediaItem)
            prepare()
        }
    }

    private fun setupRecyclerViews() {
        // Setup Alerts RecyclerView
        alertsAdapter = AlertsAdapter()
        binding.alertsRecyclerView.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = alertsAdapter
        }

        // Setup Access Log RecyclerView
        accessLogAdapter = AccessLogAdapter()
        binding.accessLogRecyclerView.apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = accessLogAdapter
        }
    }

    private fun observeViewModel() {
        viewModel.serverStatus.observe(this) { status ->
            binding.statusText.text = status
        }

        viewModel.alerts.observe(this) { alerts ->
            alertsAdapter.submitList(alerts)
        }

        viewModel.accessLogs.observe(this) { logs ->
            accessLogAdapter.submitList(logs)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        player.release()
    }
} 
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import '../widgets/monitoring_card.dart';
import '../services/monitoring_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late MonitoringService _monitoringService;
  bool _isLoading = true;
  Map<String, dynamic> _monitoringData = {};

  @override
  void initState() {
    super.initState();
    _monitoringService = MonitoringService();
    _initializeMonitoring();
  }

  Future<void> _initializeMonitoring() async {
    try {
      await _monitoringService.initialize();
      _monitoringData = await _monitoringService.getMonitoringData();
      setState(() {
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error initializing monitoring: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Server Room Monitoring'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _initializeMonitoring,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _initializeMonitoring,
              child: ListView(
                padding: const EdgeInsets.all(16.0),
                children: [
                  MonitoringCard(
                    title: 'Temperature',
                    value: '${_monitoringData['temperature'] ?? 'N/A'}°C',
                    icon: Icons.thermostat,
                    color: Colors.orange,
                  ),
                  const SizedBox(height: 16),
                  MonitoringCard(
                    title: 'Humidity',
                    value: '${_monitoringData['humidity'] ?? 'N/A'}%',
                    icon: Icons.water_drop,
                    color: Colors.blue,
                  ),
                  const SizedBox(height: 16),
                  MonitoringCard(
                    title: 'Smoke Level',
                    value: '${_monitoringData['smoke'] ?? 'N/A'} ppm',
                    icon: Icons.smoke_free,
                    color: Colors.red,
                  ),
                  const SizedBox(height: 16),
                  MonitoringCard(
                    title: 'Motion Detected',
                    value: _monitoringData['motion'] ?? false ? 'Yes' : 'No',
                    icon: Icons.motion_photos_on,
                    color: Colors.green,
                  ),
                ],
              ),
            ),
    );
  }
}
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart'; // To access control commands

class ControlsPage extends StatelessWidget {
  const ControlsPage({super.key});

  @override
  Widget build(BuildContext context) {
    // Access AppState but don't listen for rebuilds on the whole page for simple button presses
    final appState = Provider.of<AppState>(context, listen: false);
    // Listen to isLoading to disable buttons during operations
    final isExecutingCommand = context.select((AppState state) => state.isExecutingControlCommand);

    // Helper function to create styled buttons
    Widget buildControlButton({
      required String label,
      required IconData icon,
      required String action,
      Map<String, dynamic>? parameters,
      required BuildContext ctx,
      Color? buttonColor,
      Color? iconColor,
    }) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 16.0),
        child: ElevatedButton.icon(
          icon: Icon(icon, color: iconColor ?? Theme.of(context).colorScheme.onPrimary),
          label: Text(label.toUpperCase()),
          style: ElevatedButton.styleFrom(
            backgroundColor: buttonColor ?? Theme.of(context).colorScheme.primary,
            foregroundColor: iconColor ?? Theme.of(context).colorScheme.onPrimary,
            minimumSize: const Size(double.infinity, 50),
            textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 0.5),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.0)),
            elevation: 3,
          ),
          onPressed: isExecutingCommand
              ? null
              : () async {
                  final scaffoldMessenger = ScaffoldMessenger.of(ctx);
                  try {
                    await appState.executeControlCommand(action, parameters);
                    // Show success feedback
                    scaffoldMessenger.showSnackBar(
                      SnackBar(
                        content: Text('Command "$label" sent successfully.'),
                        backgroundColor: Colors.green,
                      ),
                    );
                  } catch (e) {
                    // Show error feedback from AppState or a generic message
                    final errorMsg = appState.controlCommandError ?? e.toString();
                    scaffoldMessenger.showSnackBar(
                      SnackBar(
                        content: Text('Failed to execute "$label": $errorMsg'),
                        backgroundColor: Colors.red,
                      ),
                    );
                    // Clear the specific error in AppState after showing it
                    appState.clearControlCommandError();
                  }
                },
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Remote Controls'),
      ),
      body: SingleChildScrollView( // Allow scrolling if controls exceed screen height
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            const SizedBox(height: 20), // Add some space at the top

            // --- Door Controls ---
             buildControlButton(
              label: 'Lock Door',
              icon: Icons.lock_outline,
              action: 'lock',
              buttonColor: Colors.teal,
              ctx: context,
            ),
             buildControlButton(
              label: 'Unlock Door',
              icon: Icons.lock_open_outlined,
              action: 'unlock',
              buttonColor: Colors.teal[300],
              ctx: context,
            ),

            const Divider(indent: 16, endIndent: 16, height: 30),

            // --- Camera Controls ---
             buildControlButton(
              label: 'Capture Image',
              icon: Icons.camera_alt_outlined,
              action: 'capture_image',
              buttonColor: Colors.indigo,
              ctx: context,
            ),
             buildControlButton(
              label: 'Record Video (10s)', // Specify duration for clarity
              icon: Icons.videocam_outlined,
              action: 'record_video',
              parameters: {'duration': 10}, // Example parameter
              buttonColor: Colors.indigo[300],
              ctx: context,
            ),

             const Divider(indent: 16, endIndent: 16, height: 30),

             // --- System Controls ---
             buildControlButton(
              label: 'Test Sensors',
              icon: Icons.sensors,
              action: 'test_sensors',
              buttonColor: Colors.blueGrey,
              ctx: context,
            ),
             buildControlButton(
              label: 'Clear Logs',
              icon: Icons.delete_sweep_outlined,
              action: 'clear_logs',
              buttonColor: Colors.orange[700],
              ctx: context,
            ),
             buildControlButton(
              label: 'Restart Pi',
              icon: Icons.power_settings_new,
              action: 'restart_system',
              buttonColor: Colors.red[700],
              ctx: context,
            ),
            
            const SizedBox(height: 20), // Add some space at the bottom
          ],
        ),
      ),
    );
  }
} 
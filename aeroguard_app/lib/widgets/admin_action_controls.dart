import 'package:flutter/material.dart';
import 'cyber_button.dart';
import '../services/auth_service.dart';
import '../services/network_service.dart';
import '../config/transitions.dart';
import '../screens/provision_token_screen.dart';

class AdminActionControls extends StatefulWidget {
  const AdminActionControls({super.key});

  @override
  State<AdminActionControls> createState() => _AdminActionControlsState();
}

class _AdminActionControlsState extends State<AdminActionControls> {
  bool _isKnocking = false;

  Future<void> _handleKnock() async {
    setState(() => _isKnocking = true);
    final username = await AuthService.getUsername() ?? '';
    final success = await NetworkService.sendAuthorizationKnock(username);
    setState(() => _isKnocking = false);

    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          success
              ? 'GATEWAY OPEN — Secure Tunnel Established'
              : 'ACCESS DENIED — See console for details',
          style: TextStyle(
            color: success ? Colors.black : Colors.white,
            fontWeight: FontWeight.w600,
            fontSize: 13,
            letterSpacing: 0.3,
          ),
        ),
        backgroundColor:
            success ? const Color(0xFF10B981) : const Color(0xFFEF4444),
        behavior: SnackBarBehavior.floating,
        shape:
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        margin: const EdgeInsets.all(16),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        CyberButton(
          label: 'INITIATE ZTNA KNOCK',
          icon: Icons.shield,
          isLoading: _isKnocking,
          onPressed: _handleKnock,
        ),
        const SizedBox(height: 14),
        CyberButton(
          label: 'PROVISION VENDOR TOKEN',
          icon: Icons.qr_code,
          overrideColor: Colors.orangeAccent,
          outlined: true,
          onPressed: () => Navigator.push(
            context,
            premiumRoute(const ProvisionTokenScreen()),
          ),
        ),
      ],
    );
  }
}
